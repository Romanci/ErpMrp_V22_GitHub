"""
ERP MRP v0.4 - Ana Route'lar
Bu dosya dashboard ve ana sayfa route'larini icerir
Blueprint: main_bp
"""

from flask import Blueprint, render_template
from datetime import datetime, timedelta
from app import db
from sqlalchemy import func

# Blueprint tanimla
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@main_bp.route('/dashboard')
def dashboard():
    """
    Ana dashboard sayfasi - Gercek veritabani verileri ile guncellendi
    """
    from app.stok.models import Urun, StokHareket, Parti
    from app.satin_alma.models import SatinAlmaSiparisi
    from app.uretim.models import UretimEmri

    # Toplam aktif urun sayisi
    toplam_urun = Urun.query.filter_by(aktif=1).count()

    # Kritik stok kontrolu
    urunler = Urun.query.filter_by(aktif=1).all()
    kritik_stoklar = []
    toplam_stok_kalemi = 0

    for urun in urunler:
        giris = db.session.query(func.sum(StokHareket.miktar)).filter(
            StokHareket.urun_id == urun.id,
            StokHareket.hareket_tipi == 'giris'
        ).scalar() or 0
        cikis = db.session.query(func.sum(StokHareket.miktar)).filter(
            StokHareket.urun_id == urun.id,
            StokHareket.hareket_tipi == 'cikis'
        ).scalar() or 0
        mevcut = giris - cikis
        toplam_stok_kalemi += mevcut
        if urun.min_stok > 0 and mevcut <= urun.min_stok:
            kritik_stoklar.append({
                'ad': urun.urun_adi,
                'stok_kodu': urun.stok_kodu,
                'miktar': mevcut,
                'min_stok': urun.min_stok,
                'birim': urun.birim
            })

    # Satin alma ozeti
    aktif_siparis_sayisi = SatinAlmaSiparisi.query.filter_by(aktif=1, durum='acik').count()

    # Uretim ozeti
    devam_eden_uretim = UretimEmri.query.filter_by(aktif=1, durum='devam').count()
    bekleyen_uretim = UretimEmri.query.filter_by(aktif=1, durum='beklemede').count()

    # Son stok hareketleri
    son_hareketler = StokHareket.query.order_by(StokHareket.id.desc()).limit(8).all()
    son_aktiviteler = []
    for h in son_hareketler:
        urun_adi = h.urun.urun_adi if h.urun else 'Bilinmiyor'
        birim = h.urun.birim if h.urun else ''
        if h.hareket_tipi == 'giris':
            tip, baslik = 'success', f"Stok girisi: {urun_adi} ({h.miktar} {birim})"
        elif h.hareket_tipi == 'cikis':
            tip, baslik = 'warning', f"Stok cikisi: {urun_adi} ({h.miktar} {birim})"
        else:
            tip, baslik = 'info', f"Transfer: {urun_adi}"
        son_aktiviteler.append({'tip': tip, 'baslik': baslik, 'zaman': h.tarih})

    # SKT yaklasan/gecen parti uyarisi
    partiler = Parti.query.filter_by(aktif=1).all()
    skt_uyari = sum(1 for p in partiler if p.skt_durumu() in ['Yaklasiyor', 'Gecti'])

    # Son 7 gunluk stok hareketleri grafigi icin gercek veri
    from datetime import timedelta
    bugun = datetime.now()
    gun_etiketleri = []
    giris_verileri = []
    cikis_verileri = []
    for i in range(6, -1, -1):
        gun = bugun - timedelta(days=i)
        gun_str = gun.strftime('%d.%m.%Y')
        gun_kisa = gun.strftime('%d.%m')
        gun_etiketleri.append(gun_kisa)
        gun_giris = db.session.query(func.sum(StokHareket.miktar)).filter(
            StokHareket.hareket_tipi == 'giris',
            StokHareket.tarih.like(gun_str + '%')
        ).scalar() or 0
        gun_cikis = db.session.query(func.sum(StokHareket.miktar)).filter(
            StokHareket.hareket_tipi == 'cikis',
            StokHareket.tarih.like(gun_str + '%')
        ).scalar() or 0
        giris_verileri.append(round(gun_giris, 2))
        cikis_verileri.append(round(gun_cikis, 2))

    # Kategori bazli stok dagilimi (urun sayisi)
    from app.stok.models.kategori import Kategori
    kategoriler = Kategori.query.all()
    kategori_etiketleri = []
    kategori_verileri = []
    for kat in kategoriler:
        sayi = Urun.query.filter_by(aktif=1, kategori_id=kat.id).count()
        if sayi > 0:
            kategori_etiketleri.append(kat.kategori_adi)
            kategori_verileri.append(sayi)
    # Kategorisiz urunler
    kategorisiz = Urun.query.filter_by(aktif=1, kategori_id=None).count()
    if kategorisiz > 0:
        kategori_etiketleri.append('Kategorisiz')
        kategori_verileri.append(kategorisiz)

    # MRP ozeti - eksik malzeme sayisi
    from app.uretim.models import UretimEmri as _UE
    mrp_eksik = 0
    try:
        from app.uretim.routes.mrp_routes import _mrp_hesapla
        mrp_sonuclar, _ = _mrp_hesapla()
        mrp_eksik = sum(1 for s in mrp_sonuclar if s['eksik'] > 0)
    except Exception:
        mrp_eksik = 0

    # IK ozeti
    ik_personel = 0
    bekleyen_izin = 0
    try:
        from app.ik.models.personel import Personel, Izin
        ik_personel = Personel.query.filter_by(aktif=1).count()
        bekleyen_izin = Izin.query.filter_by(durum='beklemede').count()
    except Exception:
        pass

    # Bakim ozeti
    acik_ariza = 0
    try:
        from app.bakim.models.bakim import ArizaKayit
        acik_ariza = ArizaKayit.query.filter_by(durum='acik').count()
    except Exception:
        pass

    # Fatura ozeti
    odenmemis_fatura = 0
    try:
        from app.fatura.models.fatura import Fatura
        odenmemis_fatura = Fatura.query.filter_by(aktif=1, durum='kesildi').count()
    except Exception:
        pass

    # ── Aylık satın alma tutarları (son 6 ay) ──────────────────────────────
    ay_etiketleri = []
    ay_siparis_tutar = []
    try:
        from datetime import datetime as _dt, timedelta
        simdi = _dt.now()
        for i in range(5, -1, -1):
            if simdi.month - i <= 0:
                yil = simdi.year - 1
                ay  = simdi.month - i + 12
            else:
                yil = simdi.year
                ay  = simdi.month - i
            ay_str = f'{ay:02d}.{yil}'
            toplam = db.session.query(
                func.coalesce(func.sum(SatinAlmaSiparisi.toplam_tutar), 0)
            ).filter(
                SatinAlmaSiparisi.siparis_tarihi.like(f'%.{ay_str}'),
                SatinAlmaSiparisi.aktif == 1
            ).scalar() or 0
            ay_etiketleri.append(f'{ay:02d}/{yil}')
            ay_siparis_tutar.append(round(float(toplam), 2))
    except Exception:
        ay_etiketleri = []
        ay_siparis_tutar = []

    # ── Üretim durum dağılımı ──────────────────────────────────────────────
    uretim_durum_etiket = ['Beklemede', 'Devam', 'Tamamlandı', 'İptal']
    uretim_durum_veri   = [0, 0, 0, 0]
    try:
        uretim_durum_veri[0] = UretimEmri.query.filter_by(aktif=1, durum='beklemede').count()
        uretim_durum_veri[1] = UretimEmri.query.filter_by(aktif=1, durum='devam').count()
        uretim_durum_veri[2] = UretimEmri.query.filter_by(aktif=1, durum='tamamlandi').count()
        uretim_durum_veri[3] = UretimEmri.query.filter_by(aktif=1, durum='iptal').count()
    except Exception:
        pass

    context = {
        'toplam_urun': toplam_urun,
        'toplam_stok_kalemi': round(toplam_stok_kalemi, 2),
        'kritik_stok_sayisi': len(kritik_stoklar),
        'kritik_stoklar': kritik_stoklar[:5],
        'aktif_siparis': aktif_siparis_sayisi,
        'devam_eden_uretim': devam_eden_uretim,
        'bekleyen_uretim': bekleyen_uretim,
        'son_aktiviteler': son_aktiviteler,
        'skt_uyari': skt_uyari,
        'gun_etiketleri': gun_etiketleri,
        'giris_verileri': giris_verileri,
        'cikis_verileri': cikis_verileri,
        'kategori_etiketleri': kategori_etiketleri,
        'kategori_verileri': kategori_verileri,
        'mrp_eksik': mrp_eksik,
        'ik_personel': ik_personel,
        'bekleyen_izin': bekleyen_izin,
        'acik_ariza': acik_ariza,
        'odenmemis_fatura': odenmemis_fatura,
        'ay_etiketleri': ay_etiketleri,
        'ay_siparis_tutar': ay_siparis_tutar,
        'uretim_durum_etiket': uretim_durum_etiket,
        'uretim_durum_veri': uretim_durum_veri,
    }
    return render_template('dashboard.html', **context)

@main_bp.route('/profil')
def profil():
    """Kullanici profil sayfasi"""
    return render_template('profil.html')

@main_bp.route('/ayarlar')
def ayarlar():
    """Sistem ayarlari sayfasi"""
    from app.stok.models.sistem_ayar import SistemAyar
    ayarlar_dict = {a.anahtar: a.deger for a in SistemAyar.query.all()}
    return render_template('ayarlar.html', ayarlar=ayarlar_dict)
