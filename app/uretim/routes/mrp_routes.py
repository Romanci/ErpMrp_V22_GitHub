# MRP - Malzeme Ihtiyac Planlama Motoru
# Uretim emirleri + BOM + mevcut stok = ihtiyac analizi + otomatik siparis
import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.stok.models import Urun, StokHareket, Depo
from app.uretim.models import UretimEmri, Bom, BomSatir
from app.satin_alma.models import SatinAlmaSiparisi, SatinAlmaSiparisiSatir, Tedarikci
from sqlalchemy import func

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
mrp_bp = Blueprint('mrp', __name__, template_folder=template_klasoru)


def _mevcut_stok(urun_id):
    """Bir urunun tum depolardaki toplam mevcut stogunu hesapla."""
    giris = db.session.query(func.sum(StokHareket.miktar)).filter(
        StokHareket.urun_id == urun_id,
        StokHareket.hareket_tipi == 'giris'
    ).scalar() or 0
    cikis = db.session.query(func.sum(StokHareket.miktar)).filter(
        StokHareket.urun_id == urun_id,
        StokHareket.hareket_tipi == 'cikis'
    ).scalar() or 0
    return giris - cikis


def _mrp_hesapla(uretim_emri_ids=None):
    """
    MRP hesaplama motoru.
    Secilen (veya tum aktif/beklemedeki) uretim emirleri icin
    BOM'dan ihtiyac duyulan malzemeleri hesaplar,
    mevcut stokla karsilastirir, eksikleri listeler.

    Returns:
        list of dict:
            urun, ihtiyac_toplam, mevcut_stok, eksik, saglanabilir_oran,
            emri_listesi, tedarikci
    """
    if uretim_emri_ids:
        emirler = UretimEmri.query.filter(
            UretimEmri.id.in_(uretim_emri_ids),
            UretimEmri.aktif == 1,
            UretimEmri.durum.in_(['beklemede', 'devam'])
        ).all()
    else:
        emirler = UretimEmri.query.filter(
            UretimEmri.aktif == 1,
            UretimEmri.durum.in_(['beklemede', 'devam'])
        ).all()

    # urun_id -> {ihtiyac_toplam, emri_listesi}
    ihtiyac_map = {}

    for emir in emirler:
        # Bu urun icin gecerli BOM bul
        bom = Bom.query.filter_by(urun_id=emir.urun_id, gecerli=1).first()
        if not bom:
            continue
        for satir in bom.satirlar:
            mat_id = satir.ham_madde_id
            fire_katsayi = 1 + (satir.fire_orani / 100.0)
            gereken = satir.miktar * emir.miktar * fire_katsayi
            if mat_id not in ihtiyac_map:
                ihtiyac_map[mat_id] = {'ihtiyac': 0, 'emirler': []}
            ihtiyac_map[mat_id]['ihtiyac'] += gereken
            ihtiyac_map[mat_id]['emirler'].append({
                'emir_no': emir.emir_no,
                'urun_adi': emir.urun.urun_adi if emir.urun else '-',
                'miktar': emir.miktar,
                'gereken': round(gereken, 4)
            })

    sonuclar = []
    for urun_id, veri in ihtiyac_map.items():
        urun = Urun.query.get(urun_id)
        if not urun:
            continue
        mevcut = _mevcut_stok(urun_id)
        eksik = max(0, veri['ihtiyac'] - mevcut)
        saglanabilir = min(100, round((mevcut / veri['ihtiyac']) * 100, 1)) if veri['ihtiyac'] > 0 else 100
        sonuclar.append({
            'urun': urun,
            'ihtiyac_toplam': round(veri['ihtiyac'], 4),
            'mevcut_stok': round(mevcut, 4),
            'eksik': round(eksik, 4),
            'saglanabilir_oran': saglanabilir,
            'emri_listesi': veri['emirler'],
            'tedarikci': urun.tedarikci if urun.tedarikci_id else None
        })

    # Eksik olanlari once sirala
    sonuclar.sort(key=lambda x: x['eksik'], reverse=True)
    return sonuclar, emirler


# ─── MRP Ana Sayfa: Ihtiyac Analizi ───────────────────────────────────────────
@mrp_bp.route('/mrp')
def mrp_analiz():
    sonuclar, emirler = _mrp_hesapla()

    # Ozet istatistikler
    toplam_malzeme = len(sonuclar)
    eksik_malzeme = sum(1 for s in sonuclar if s['eksik'] > 0)
    tamam_malzeme = toplam_malzeme - eksik_malzeme
    aktif_emir_sayisi = len(emirler)

    return render_template(
        'uretim/mrp_analiz.html',
        sonuclar=sonuclar,
        emirler=emirler,
        toplam_malzeme=toplam_malzeme,
        eksik_malzeme=eksik_malzeme,
        tamam_malzeme=tamam_malzeme,
        aktif_emir_sayisi=aktif_emir_sayisi
    )


# ─── MRP Otomatik Siparis Olustur ─────────────────────────────────────────────
@mrp_bp.route('/mrp/siparis-olustur', methods=['POST'])
def mrp_siparis_olustur():
    """
    Eksik malzemeleri tedarikci bazli gruplar,
    her tedarikci icin bir satin alma siparisi olusturur.
    Tedarikci tanimli olmayan malzemeler varsayilan (ilk aktif) tedarikcie atanir.
    """
    sonuclar, _ = _mrp_hesapla()
    eksikler = [s for s in sonuclar if s['eksik'] > 0]

    if not eksikler:
        flash('Eksik malzeme yok, siparis olusturmaya gerek yok.', 'info')
        return redirect(url_for('mrp.mrp_analiz'))

    # Tedarikci ID -> eksik malzeme listesi
    tedarikci_gruplari = {}
    varsayilan_tedarikci = Tedarikci.query.filter_by(aktif=1).first()

    for s in eksikler:
        tedarikci = s['tedarikci'] or varsayilan_tedarikci
        if not tedarikci:
            flash('Hic aktif tedarikci bulunamadi. Lutfen once tedarikci ekleyin.', 'error')
            return redirect(url_for('mrp.mrp_analiz'))
        tid = tedarikci.id
        if tid not in tedarikci_gruplari:
            tedarikci_gruplari[tid] = {'tedarikci': tedarikci, 'malzemeler': []}
        tedarikci_gruplari[tid]['malzemeler'].append(s)

    now_str = datetime.now().strftime('%d.%m.%Y %H:%M')
    tarih_kisa = datetime.now().strftime('%Y%m%d%H%M%S')
    olusturulan_siparisler = []

    for tid, grup in tedarikci_gruplari.items():
        tedarikci = grup['tedarikci']
        siparis_no = f"MRP-{tarih_kisa}-{tid}"

        yeni_siparis = SatinAlmaSiparisi(
            siparis_no=siparis_no,
            tedarikci_id=tid,
            siparis_tarihi=datetime.now().strftime('%d.%m.%Y'),
            durum='acik',
            para_birimi='TL',
            aciklama=f'MRP tarafindan otomatik olusturuldu. {now_str}'
        )
        db.session.add(yeni_siparis)
        db.session.flush()  # ID almak icin

        toplam = 0
        for mal in grup['malzemeler']:
            urun = mal['urun']
            birim_fiyat = urun.alis_fiyati if urun.alis_fiyati and urun.alis_fiyati > 0 else 1.0
            miktar = mal['eksik']
            satir = SatinAlmaSiparisiSatir(
                siparis_id=yeni_siparis.id,
                urun_id=urun.id,
                miktar=miktar,
                birim_fiyat=birim_fiyat,
                indirim_orani=0,
                kdv_orani=urun.kdv_orani if urun.kdv_orani else 18,
                aciklama=f'MRP - {now_str}'
            )
            db.session.add(satir)
            db.session.flush()
            toplam += satir.hesapla_tutar()

        yeni_siparis.toplam_tutar = round(toplam, 2)
        olusturulan_siparisler.append(yeni_siparis)

    db.session.commit()

    flash(f'{len(olusturulan_siparisler)} tedarikci icin {len(olusturulan_siparisler)} siparis olusturuldu.', 'success')
    return redirect(url_for('mrp.mrp_siparis_listesi'))


# ─── MRP Ile Olusturulan Siparisler ───────────────────────────────────────────
@mrp_bp.route('/mrp/siparisler')
def mrp_siparis_listesi():
    """MRP tarafindan olusturulan siparisler"""
    siparisler = SatinAlmaSiparisi.query.filter(
        SatinAlmaSiparisi.aciklama.like('MRP tarafindan%'),
        SatinAlmaSiparisi.aktif == 1
    ).order_by(SatinAlmaSiparisi.id.desc()).all()
    return render_template('uretim/mrp_siparisler.html', siparisler=siparisler)
