import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.siparis.models.siparis import SatisEmri, SatisEmriSatir, SIPARIS_DURUMLARI, KAYNAK_TURLERI
from app.kullanici.auth import yazma_gerekli, admin_gerekli

_tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
siparis_bp = Blueprint('siparis', __name__, template_folder=_tpl)


def _siparis_no_olustur():
    son = SatisEmri.query.order_by(SatisEmri.id.desc()).first()
    yil = datetime.now().year
    return f'SE-{yil}-{((son.id if son else 0) + 1):04d}'


# ── Dashboard ────────────────────────────────────────────────────────────────

@siparis_bp.route('/')
def siparis_dashboard():
    emirler = SatisEmri.query.filter_by(aktif=1).order_by(SatisEmri.id.desc()).all()
    durum_sayilari = {d[0]: sum(1 for e in emirler if e.durum == d[0]) for d in SIPARIS_DURUMLARI}
    onay_bekleyenler = [e for e in emirler if e.durum == 'onay_bekliyor']
    aktif = [e for e in emirler if e.durum not in ('teslim_edildi', 'iptal')]
    return render_template('siparis/siparis_dashboard.html',
        emirler=emirler, aktif=aktif, onay_bekleyenler=onay_bekleyenler,
        durum_sayilari=durum_sayilari, durumlar=SIPARIS_DURUMLARI)


# ── Liste ────────────────────────────────────────────────────────────────────

@siparis_bp.route('/liste')
def siparis_liste():
    durum = request.args.get('durum', '')
    q = SatisEmri.query.filter_by(aktif=1)
    if durum:
        q = q.filter_by(durum=durum)
    emirler = q.order_by(SatisEmri.id.desc()).all()
    return render_template('siparis/siparis_liste.html',
        emirler=emirler, secili_durum=durum, durumlar=SIPARIS_DURUMLARI)


# ── Yeni Sipariş Formu ───────────────────────────────────────────────────────

@siparis_bp.route('/yeni', methods=['GET', 'POST'])
@yazma_gerekli
def siparis_yeni():
    if request.method == 'POST':
        e = SatisEmri(
            siparis_no          = _siparis_no_olustur(),
            musteri_id          = request.form.get('musteri_id') or None,
            musteri_adi_serbest = request.form.get('musteri_adi_serbest', ''),
            musteri_telefon     = request.form.get('musteri_telefon', ''),
            teslim_adresi       = request.form.get('teslim_adresi', ''),
            kaynak              = request.form.get('kaynak', 'telefon'),
            termin_tarihi       = request.form.get('termin_tarihi', ''),
            para_birimi         = request.form.get('para_birimi', 'TL'),
            aciklama            = request.form.get('aciklama', ''),
            proje_id            = request.form.get('proje_id') or None,
            durum               = 'onay_bekliyor',
            olusturan_id        = session.get('kullanici_id'),
        )
        db.session.add(e)
        db.session.flush()

        # Satırları ekle
        urun_idler   = request.form.getlist('urun_id[]')
        tanimlar     = request.form.getlist('tanim[]')
        miktarlar    = request.form.getlist('miktar[]')
        fiyatlar     = request.form.getlist('birim_fiyat[]')
        kdvler       = request.form.getlist('kdv_orani[]')
        projeler     = request.form.getlist('proje_kodu[]')

        for i in range(len(tanimlar)):
            tanim = tanimlar[i].strip() if i < len(tanimlar) else ''
            urun_id = urun_idler[i] if i < len(urun_idler) else ''
            if not tanim and not urun_id:
                continue
            miktar = float(miktarlar[i]) if i < len(miktarlar) and miktarlar[i] else 1
            fiyat  = float(fiyatlar[i])  if i < len(fiyatlar)  and fiyatlar[i]  else 0
            kdv    = float(kdvler[i])    if i < len(kdvler)    and kdvler[i]    else 18

            satir = SatisEmriSatir(
                siparis_id  = e.id,
                urun_id     = urun_id or None,
                tanim       = tanim,
                miktar      = miktar,
                birim_fiyat = fiyat,
                kdv_orani   = kdv,
                proje_kodu  = projeler[i] if i < len(projeler) else '',
            )
            # Stok durumu kontrolü
            if urun_id:
                from app.stok.models import Urun, StokHareket
                from app import db as _db
                from sqlalchemy import func
                u = Urun.query.get(urun_id)
                if u:
                    giris = _db.session.query(func.sum(StokHareket.miktar)).filter_by(
                        urun_id=u.id, hareket_tipi='giris').scalar() or 0
                    cikis = _db.session.query(func.sum(StokHareket.miktar)).filter_by(
                        urun_id=u.id, hareket_tipi='cikis').scalar() or 0
                    satir.stok_mevcut = giris - cikis
                    satir.birim = u.birim
            db.session.add(satir)

        e.toplam_hesapla()
        db.session.commit()

        # Bildirim gönder
        _siparis_bildirimi_gonder(e, 'yeni')
        flash(f'Sipariş oluşturuldu: {e.siparis_no} — Yönetici onayı bekleniyor', 'success')
        return redirect(url_for('siparis.siparis_detay', id=e.id))

    from app.crm.models.crm import Musteri
    from app.stok.models import Urun
    from app.proje.models.proje import Proje
    return render_template('siparis/siparis_form.html',
        musteriler=Musteri.query.filter_by(aktif=1).all(),
        urunler=Urun.query.filter_by(aktif=1).all(),
        projeler=Proje.query.filter(Proje.asama.notin_(['kapandi','iptal'])).all(),
        kaynaklar=KAYNAK_TURLERI)


# ── Detay ────────────────────────────────────────────────────────────────────

@siparis_bp.route('/<int:id>')
def siparis_detay(id):
    e = SatisEmri.query.get_or_404(id)
    return render_template('siparis/siparis_detay.html',
        siparis=e, durumlar=SIPARIS_DURUMLARI)


# ── Yönetici Onay Ekranı ─────────────────────────────────────────────────────

@siparis_bp.route('/<int:id>/onayla', methods=['GET', 'POST'])
@admin_gerekli
def siparis_onayla(id):
    e = SatisEmri.query.get_or_404(id)
    if request.method == 'POST':
        aksiyon = request.form.get('aksiyon')
        if aksiyon == 'onayla':
            e.durum        = 'onaylandi'
            e.onaylayan_id = session.get('kullanici_id')
            e.onay_tarihi  = datetime.now().strftime('%d.%m.%Y')
            e.onay_notu    = request.form.get('onay_notu', '')
            db.session.commit()

            # Seçilen aksiyonlara göre görev oluştur
            _siparis_gorev_olustur(e, request.form)
            _siparis_bildirimi_gonder(e, 'onaylandi')
            flash(f'{e.siparis_no} onaylandı, görevler oluşturuldu', 'success')
        elif aksiyon == 'reddet':
            e.durum     = 'iptal'
            e.onay_notu = request.form.get('onay_notu', '')
            db.session.commit()
            flash(f'{e.siparis_no} reddedildi', 'warning')
        return redirect(url_for('siparis.siparis_detay', id=id))

    return render_template('siparis/siparis_onayla.html', siparis=e)


# ── Durum Güncelle ───────────────────────────────────────────────────────────

@siparis_bp.route('/<int:id>/durum', methods=['POST'])
@yazma_gerekli
def siparis_durum_guncelle(id):
    e = SatisEmri.query.get_or_404(id)
    yeni = request.form.get('durum')
    if yeni:
        e.durum = yeni
        db.session.commit()
        _siparis_bildirimi_gonder(e, 'durum_degisimi')
        flash(f'Durum güncellendi: {e.durum_adi}', 'success')
    return redirect(url_for('siparis.siparis_detay', id=id))


# ── Tekliften Dönüştür ───────────────────────────────────────────────────────

@siparis_bp.route('/tekliften/<int:teklif_id>')
@yazma_gerekli
def tekliften_siparis(teklif_id):
    from app.crm.models.crm import Teklif, TeklifKalem
    teklif = Teklif.query.get_or_404(teklif_id)

    e = SatisEmri(
        siparis_no          = _siparis_no_olustur(),
        musteri_id          = teklif.musteri_id,
        kaynak              = 'teklif',
        teklif_id           = teklif_id,
        para_birimi         = teklif.para_birimi or 'TL',
        aciklama            = f'Teklif {teklif.teklif_no} onayından oluşturuldu',
        durum               = 'onay_bekliyor',
        olusturan_id        = session.get('kullanici_id'),
    )
    db.session.add(e)
    db.session.flush()

    for kalem in teklif.kalemler:
        satir = SatisEmriSatir(
            siparis_id  = e.id,
            urun_id     = kalem.urun_id,
            tanim       = kalem.tanim or (kalem.urun.urun_adi if kalem.urun else ''),
            miktar      = kalem.miktar,
            birim       = kalem.birim or 'Adet',
            birim_fiyat = kalem.birim_fiyat,
            kdv_orani   = kalem.kdv_orani or 18,
        )
        db.session.add(satir)

    e.toplam_hesapla()

    # Teklifi güncelle
    teklif.durum = 'onaylandi'
    db.session.commit()

    # Proje otomatik oluştur
    from app.proje.routes.proje_routes import teklif_den_proje_olustur
    proje = teklif_den_proje_olustur(teklif_id)
    if proje:
        e.proje_id = proje.id
        db.session.commit()

    _siparis_bildirimi_gonder(e, 'yeni')
    flash(f'Teklif siparişe dönüştürüldü: {e.siparis_no}', 'success')
    return redirect(url_for('siparis.siparis_onayla', id=e.id))


# ── Yardımcılar ──────────────────────────────────────────────────────────────

def _siparis_gorev_olustur(siparis, form):
    """Onay sonrası seçilen departmanlara görev oluştur"""
    from app.proje.models.proje import ProjeGorev
    departmanlar = []
    if form.get('gorev_depo'):      departmanlar.append(('depo',      'Depo Hazırlık'))
    if form.get('gorev_uretim'):    departmanlar.append(('uretim',    'Üretim'))
    if form.get('gorev_satin'):     departmanlar.append(('satin_alma','Satın Alma Talebi'))

    proje_id = siparis.proje_id

    for dep, baslik_prefix in departmanlar:
        if proje_id:
            g = ProjeGorev(
                proje_id    = proje_id,
                baslik      = f'{baslik_prefix}: {siparis.siparis_no}',
                departman   = dep,
                son_tarih   = siparis.termin_tarihi,
                oncelik     = 'yuksek',
                durum       = 'bekliyor',
            )
            db.session.add(g)

        # Sistem bildirimi
        try:
            from app.stok.models.bildirim import Bildirim
            b = Bildirim(
                baslik   = f'{baslik_prefix} Görevi',
                mesaj    = f'{siparis.siparis_no} siparişi için görev oluşturuldu. Müşteri: {siparis.musteri_adi}',
                tur      = 'siparis',
                kayit_id = siparis.id,
            )
            db.session.add(b)
        except Exception:
            pass

    db.session.commit()


def _siparis_bildirimi_gonder(siparis, olay):
    try:
        mesajlar = {
            'yeni':           f'Yeni sipariş alındı: {siparis.siparis_no} — {siparis.musteri_adi} — Onay bekliyor',
            'onaylandi':      f'Sipariş onaylandı: {siparis.siparis_no} — {siparis.musteri_adi}',
            'durum_degisimi': f'Sipariş durumu değişti: {siparis.siparis_no} → {siparis.durum_adi}',
        }
        mesaj = mesajlar.get(olay, f'Sipariş güncellendi: {siparis.siparis_no}')
        from app.stok.models.bildirim import Bildirim
        b = Bildirim(baslik='Sipariş Bildirimi', mesaj=mesaj, tur='siparis', kayit_id=siparis.id)
        db.session.add(b)
        db.session.commit()
    except Exception:
        pass
