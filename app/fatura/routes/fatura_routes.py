# Fatura ve Irsaliye route'lari
import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.fatura.models import Fatura, FaturaSatir, Irsaliye, IrsaliyeSatir
from app.satin_alma.models import Tedarikci, SatinAlmaSiparisi
from app.stok.models import Urun

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
fatura_bp = Blueprint('fatura', __name__, template_folder=template_klasoru)


def _fatura_no(tip):
    """Otomatik fatura numarasi uret"""
    yil = datetime.now().strftime('%Y')
    ay = datetime.now().strftime('%m')
    prefix = 'ALF' if tip == 'alis' else 'SAF'
    son = Fatura.query.filter(
        Fatura.fatura_no.like(f'{prefix}-{yil}{ay}-%')
    ).count() + 1
    return f'{prefix}-{yil}{ay}-{son:04d}'


def _irsaliye_no(tip):
    yil = datetime.now().strftime('%Y')
    ay = datetime.now().strftime('%m')
    prefix = 'GIR' if tip == 'giris' else 'CIK'
    son = Irsaliye.query.filter(
        Irsaliye.irsaliye_no.like(f'{prefix}-{yil}{ay}-%')
    ).count() + 1
    return f'{prefix}-{yil}{ay}-{son:04d}'


# ─── Fatura Listesi ──────────────────────────────────────────────────────────
@fatura_bp.route('/')
def fatura_liste():
    tip    = request.args.get('tip', '')
    durum  = request.args.get('durum', '')
    tarih_bas = request.args.get('tarih_bas', '')
    tarih_bit = request.args.get('tarih_bit', '')

    q = Fatura.query.filter_by(aktif=1)
    if tip:
        q = q.filter_by(fatura_tipi=tip)
    if durum:
        q = q.filter_by(durum=durum)
    # Tarih filtresi (GG.AA.YYYY formatı - string karşılaştırma)
    if tarih_bas:
        try:
            from datetime import datetime as _dt
            bas = _dt.strptime(tarih_bas, '%Y-%m-%d').strftime('%d.%m.%Y')
            q = q.filter(Fatura.fatura_tarihi >= bas)
        except Exception:
            pass
    if tarih_bit:
        try:
            from datetime import datetime as _dt
            bit = _dt.strptime(tarih_bit, '%Y-%m-%d').strftime('%d.%m.%Y')
            q = q.filter(Fatura.fatura_tarihi <= bit)
        except Exception:
            pass

    faturalar  = q.order_by(Fatura.id.desc()).all()
    irsaliyeler = Irsaliye.query.filter_by(aktif=1).order_by(Irsaliye.id.desc()).limit(20).all()
    return render_template('fatura/fatura_liste.html',
                           faturalar=faturalar, irsaliyeler=irsaliyeler,
                           tip_filtre=tip)


# ─── Yeni Fatura ─────────────────────────────────────────────────────────────
@fatura_bp.route('/yeni', methods=['GET', 'POST'])
@fatura_bp.route('/yeni/<string:tip>', methods=['GET', 'POST'])
def fatura_ekle(tip='alis'):
    if request.method == 'POST':
        fatura_tipi = request.form.get('fatura_tipi', tip)
        yeni = Fatura(
            fatura_no=request.form.get('fatura_no') or _fatura_no(fatura_tipi),
            fatura_tipi=fatura_tipi,
            fatura_tarihi=request.form.get('fatura_tarihi') or datetime.now().strftime('%d.%m.%Y'),
            vade_tarihi=request.form.get('vade_tarihi'),
            tedarikci_id=request.form.get('tedarikci_id') or None,
            musteri_adi=request.form.get('musteri_adi'),
            musteri_vergi_no=request.form.get('musteri_vergi_no'),
            musteri_adres=request.form.get('musteri_adres'),
            siparis_id=request.form.get('siparis_id') or None,
            para_birimi=request.form.get('para_birimi', 'TL'),
            durum='taslak',
            aciklama=request.form.get('aciklama'),
        )
        db.session.add(yeni)
        db.session.commit()

        # Siparis satirlarindan otomatik fatura satirlari olustur
        if yeni.siparis_id:
            siparis = SatinAlmaSiparisi.query.get(yeni.siparis_id)
            if siparis:
                for ss in siparis.satirlar:
                    satir = FaturaSatir(
                        fatura_id=yeni.id,
                        urun_id=ss.urun_id,
                        miktar=ss.miktar,
                        birim=ss.urun.birim if ss.urun else 'adet',
                        birim_fiyat=ss.birim_fiyat,
                        indirim_orani=ss.indirim_orani,
                        kdv_orani=ss.kdv_orani,
                    )
                    db.session.add(satir)
                db.session.flush()
                yeni.toplam_hesapla()
                db.session.commit()

        flash('Fatura oluşturuldu', 'success')
        return redirect(url_for('fatura.fatura_detay', id=yeni.id))

    tedarikciler = Tedarikci.query.filter_by(aktif=1).all()
    siparisler = SatinAlmaSiparisi.query.filter_by(aktif=1, durum='acik').all()
    uneriler_no = _fatura_no(tip)
    return render_template('fatura/fatura_form.html', fatura=None, tip=tip,
                           tedarikciler=tedarikciler, siparisler=siparisler,
                           onerilen_no=uneriler_no)


# ─── Fatura Detay ────────────────────────────────────────────────────────────
@fatura_bp.route('/<int:id>')
def fatura_detay(id):
    fatura = Fatura.query.get_or_404(id)
    urunler = Urun.query.filter_by(aktif=1).all()
    return render_template('fatura/fatura_detay.html', fatura=fatura, urunler=urunler)


# ─── Fatura Satir Ekle ───────────────────────────────────────────────────────
@fatura_bp.route('/<int:fatura_id>/satir/ekle', methods=['POST'])
def fatura_satir_ekle(fatura_id):
    fatura = Fatura.query.get_or_404(fatura_id)
    urun_id = request.form.get('urun_id') or None
    birim = 'adet'
    if urun_id:
        urun = Urun.query.get(urun_id)
        birim = urun.birim if urun else 'adet'

    satir = FaturaSatir(
        fatura_id=fatura_id,
        urun_id=urun_id,
        tanim=request.form.get('tanim'),
        miktar=float(request.form.get('miktar', 1)),
        birim=birim,
        birim_fiyat=float(request.form.get('birim_fiyat', 0)),
        indirim_orani=float(request.form.get('indirim_orani', 0)),
        kdv_orani=float(request.form.get('kdv_orani', 18)),
        proje_kodu=request.form.get('proje_kodu', '').strip() or None,
    )
    db.session.add(satir)
    db.session.flush()
    fatura.toplam_hesapla()
    db.session.commit()
    flash('Kalem eklendi', 'success')
    return redirect(url_for('fatura.fatura_detay', id=fatura_id))


# ─── Fatura Satir Sil ────────────────────────────────────────────────────────
@fatura_bp.route('/satir/<int:satir_id>/sil', methods=['POST'])
def fatura_satir_sil(satir_id):
    satir = FaturaSatir.query.get_or_404(satir_id)
    fatura_id = satir.fatura_id
    db.session.delete(satir)
    db.session.flush()
    fatura = Fatura.query.get(fatura_id)
    fatura.toplam_hesapla()
    db.session.commit()
    flash('Kalem silindi', 'success')
    return redirect(url_for('fatura.fatura_detay', id=fatura_id))


# ─── Fatura Durum Guncelle ───────────────────────────────────────────────────
@fatura_bp.route('/<int:id>/durum/<string:durum>', methods=['POST'])
def fatura_durum(id, durum):
    fatura = Fatura.query.get_or_404(id)
    if durum in ['taslak', 'kesildi', 'odendi', 'iptal']:
        fatura.durum = durum
        if durum == 'odendi':
            fatura.odeme_tarihi = datetime.now().strftime('%d.%m.%Y')
        db.session.commit()
        # Muhasebe entegrasyonu — fatura kesilince otomatik kayıt
        if durum == 'kesildi':
            try:
                from app.muhasebe.routes.muhasebe_routes import fatura_muhasebe_kaydet
                fatura_muhasebe_kaydet(fatura)
            except Exception:
                pass
        flash(f'Fatura durumu: {durum}', 'success')
    return redirect(url_for('fatura.fatura_detay', id=id))


# ─── Fatura Sil ──────────────────────────────────────────────────────────────
@fatura_bp.route('/<int:id>/sil', methods=['POST'])
def fatura_sil(id):
    fatura = Fatura.query.get_or_404(id)
    fatura.aktif = 0
    db.session.commit()
    flash('Fatura silindi', 'success')
    return redirect(url_for('fatura.fatura_liste'))


# ════════════════════════════════════════════════════════
# İRSALİYE
# ════════════════════════════════════════════════════════

# ─── Irsaliye Listesi ────────────────────────────────────────────────────────
@fatura_bp.route('/irsaliyeler')
def irsaliye_liste():
    irsaliyeler = Irsaliye.query.filter_by(aktif=1).order_by(Irsaliye.id.desc()).all()
    return render_template('fatura/irsaliye_liste.html', irsaliyeler=irsaliyeler)


# ─── Yeni Irsaliye ───────────────────────────────────────────────────────────
@fatura_bp.route('/irsaliye/yeni', methods=['GET', 'POST'])
@fatura_bp.route('/irsaliye/yeni/<string:tip>', methods=['GET', 'POST'])
def irsaliye_ekle(tip='cikis'):
    if request.method == 'POST':
        irsaliye_tipi = request.form.get('irsaliye_tipi', tip)
        yeni = Irsaliye(
            irsaliye_no=request.form.get('irsaliye_no') or _irsaliye_no(irsaliye_tipi),
            irsaliye_tipi=irsaliye_tipi,
            irsaliye_tarihi=request.form.get('irsaliye_tarihi') or datetime.now().strftime('%d.%m.%Y'),
            tedarikci_id=request.form.get('tedarikci_id') or None,
            musteri_adi=request.form.get('musteri_adi'),
            teslim_adresi=request.form.get('teslim_adresi'),
            arac_plaka=request.form.get('arac_plaka'),
            sofor=request.form.get('sofor'),
            durum='hazirlaniyor',
            aciklama=request.form.get('aciklama'),
        )
        db.session.add(yeni)
        db.session.commit()
        flash('İrsaliye oluşturuldu', 'success')
        return redirect(url_for('fatura.irsaliye_detay', id=yeni.id))

    tedarikciler = Tedarikci.query.filter_by(aktif=1).all()
    onerilen_no = _irsaliye_no(tip)
    return render_template('fatura/irsaliye_form.html', irsaliye=None, tip=tip,
                           tedarikciler=tedarikciler, onerilen_no=onerilen_no)


# ─── Irsaliye Detay ──────────────────────────────────────────────────────────
@fatura_bp.route('/irsaliye/<int:id>')
def irsaliye_detay(id):
    irsaliye = Irsaliye.query.get_or_404(id)
    urunler = Urun.query.filter_by(aktif=1).all()
    return render_template('fatura/irsaliye_detay.html', irsaliye=irsaliye, urunler=urunler)


# ─── Irsaliye Satir Ekle ─────────────────────────────────────────────────────
@fatura_bp.route('/irsaliye/<int:irsaliye_id>/satir/ekle', methods=['POST'])
def irsaliye_satir_ekle(irsaliye_id):
    Irsaliye.query.get_or_404(irsaliye_id)
    urun_id = request.form.get('urun_id') or None
    birim = 'adet'
    if urun_id:
        urun = Urun.query.get(urun_id)
        birim = urun.birim if urun else 'adet'
    satir = IrsaliyeSatir(
        irsaliye_id=irsaliye_id,
        urun_id=urun_id,
        tanim=request.form.get('tanim'),
        miktar=float(request.form.get('miktar', 1)),
        birim=birim,
        aciklama=request.form.get('aciklama'),
    )
    db.session.add(satir)
    db.session.commit()
    flash('Kalem eklendi', 'success')
    return redirect(url_for('fatura.irsaliye_detay', id=irsaliye_id))


# ─── Irsaliye Durum Guncelle ─────────────────────────────────────────────────
@fatura_bp.route('/irsaliye/<int:id>/durum/<string:durum>', methods=['POST'])
def irsaliye_durum(id, durum):
    irsaliye = Irsaliye.query.get_or_404(id)
    if durum in ['hazirlaniyor', 'yolda', 'teslim', 'iptal']:
        irsaliye.durum = durum
        db.session.commit()
        flash(f'İrsaliye durumu: {durum}', 'success')
    return redirect(url_for('fatura.irsaliye_detay', id=id))


# ─── SİPARİŞTEN FATURA OLUŞTUR (tek tıkla) ────────────────────────────────────
@fatura_bp.route('/siparis-den-olustur/<int:siparis_id>', methods=['POST'])
def siparis_den_fatura_olustur(siparis_id):
    """
    Satın alma siparişinden tek tıkla alış faturası oluşturur.
    Sipariş satırlarını otomatik olarak fatura satırlarına kopyalar.
    """
    from app.satin_alma.models import SatinAlmaSiparisi, SatinAlmaSiparisiSatir
    from app.fatura.models import FaturaSatir

    siparis = SatinAlmaSiparisi.query.get_or_404(siparis_id)

    # Bu siparişten zaten fatura oluşturulmuş mu?
    mevcut = Fatura.query.filter_by(siparis_id=siparis_id, aktif=1).first()
    if mevcut:
        flash(f'Bu sipariş için zaten fatura mevcut: {mevcut.fatura_no}', 'warning')
        return redirect(url_for('fatura.fatura_detay', id=mevcut.id))

    try:
        # Yeni fatura oluştur
        yeni_fatura = Fatura(
            fatura_no=_fatura_no('alis'),
            fatura_tipi='alis',
            fatura_tarihi=datetime.now().strftime('%d.%m.%Y'),
            tedarikci_id=siparis.tedarikci_id,
            para_birimi=siparis.para_birimi or 'TL',
            siparis_id=siparis.id,
            durum='taslak',
            aciklama=f'Sipariş {siparis.siparis_no} üzerinden otomatik oluşturuldu.'
        )
        db.session.add(yeni_fatura)
        db.session.flush()

        # Sipariş satırlarını fatura satırlarına kopyala
        for ss in siparis.satirlar:
            urun = ss.urun
            fs = FaturaSatir(
                fatura_id=yeni_fatura.id,
                satir_tanim=urun.urun_adi if urun else 'Bilinmiyor',
                urun_id=ss.urun_id,
                miktar=ss.miktar,
                birim=urun.birim if urun else 'adet',
                birim_fiyat=ss.birim_fiyat,
                indirim_orani=ss.indirim_orani or 0,
                kdv_orani=ss.kdv_orani or 18,
            )
            db.session.add(fs)

        db.session.flush()
        yeni_fatura.toplam_hesapla()
        db.session.commit()

        flash(f'Fatura {yeni_fatura.fatura_no} oluşturuldu. Kontrol edip kaydedebilirsiniz.', 'success')
        return redirect(url_for('fatura.fatura_detay', id=yeni_fatura.id))

    except Exception as e:
        db.session.rollback()
        flash(f'Fatura oluşturulamadı: {str(e)}', 'error')
        return redirect(url_for('satin_alma_siparis.siparis_detay', id=siparis_id))
