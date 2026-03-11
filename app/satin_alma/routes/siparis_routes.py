# Satin alma siparisi yonetimi
import os
from app.kullanici.auth import yazma_gerekli, silme_gerekli
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.satin_alma.models import Tedarikci, SatinAlmaSiparisi, SatinAlmaSiparisiSatir
from app.stok.models import Urun

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
siparis_bp = Blueprint('satin_alma_siparis', __name__, template_folder=template_klasoru)

# Siparis listesi
@siparis_bp.route('/siparisler')
def siparis_liste():
    durum    = request.args.get('durum', '')
    ara      = request.args.get('ara', '')
    tarih_bas = request.args.get('tarih_bas', '')
    tarih_bit = request.args.get('tarih_bit', '')

    q = SatinAlmaSiparisi.query.filter_by(aktif=1)
    if durum:
        q = q.filter_by(durum=durum)
    if ara:
        q = q.join(Tedarikci, isouter=True).filter(
            db.or_(
                SatinAlmaSiparisi.siparis_no.ilike(f'%{ara}%'),
                Tedarikci.unvan.ilike(f'%{ara}%')
            )
        )
    siparisler = q.order_by(SatinAlmaSiparisi.siparis_tarihi.desc()).all()
    return render_template('satin_alma/siparis_liste.html', siparisler=siparisler)

# Yeni siparis
@siparis_bp.route('/siparis/yeni', methods=['GET', 'POST'])
@yazma_gerekli
def siparis_ekle():
    if request.method == 'POST':
        yeni_siparis = SatinAlmaSiparisi(
            siparis_no=request.form['siparis_no'],
            tedarikci_id=request.form['tedarikci_id'],
            siparis_tarihi=request.form.get('siparis_tarihi'),
            teslim_tarihi=request.form.get('teslim_tarihi'),
            para_birimi=request.form.get('para_birimi', 'TL'),
            aciklama=request.form.get('aciklama')
        )
        db.session.add(yeni_siparis)
        db.session.commit()
        flash('Siparis olusturuldu. Simdi urun ekleyebilirsiniz.', 'success')
        return redirect(url_for('siparis.siparis_detay', id=yeni_siparis.id))
    
    tedarikciler = Tedarikci.query.filter_by(aktif=1).all()
    return render_template('satin_alma/siparis_form.html', siparis=None, tedarikciler=tedarikciler)

# Siparis detay ve satir ekleme
@siparis_bp.route('/siparis/<int:id>')
def siparis_detay(id):
    siparis = SatinAlmaSiparisi.query.get_or_404(id)
    urunler = Urun.query.filter_by(aktif=1).all()
    return render_template('satin_alma/siparis_detay.html', siparis=siparis, urunler=urunler)

# Siparis satiri ekle
@siparis_bp.route('/siparis/<int:siparis_id>/satir/ekle', methods=['POST'])
def siparis_satir_ekle(siparis_id):
    yeni_satir = SatinAlmaSiparisiSatir(
        siparis_id=siparis_id,
        urun_id=request.form['urun_id'],
        miktar=float(request.form['miktar']),
        birim_fiyat=float(request.form['birim_fiyat']),
        indirim_orani=float(request.form.get('indirim_orani', 0)),
        kdv_orani=float(request.form.get('kdv_orani', 18)),
        aciklama=request.form.get('aciklama')
    )
    db.session.add(yeni_satir)

    # Siparis toplam tutarini satirlari yeniden toplayarak guncelle
    siparis = SatinAlmaSiparisi.query.get(siparis_id)
    db.session.flush()  # yeni_satir.id olusmasi icin
    siparis.toplam_tutar = sum(s.hesapla_tutar() for s in siparis.satirlar)

    db.session.commit()
    flash('Urun eklendi', 'success')
    return redirect(url_for('siparis.siparis_detay', id=siparis_id))

# Siparis satiri sil
@siparis_bp.route('/siparis/satir/<int:satir_id>/sil', methods=['POST'])
def siparis_satir_sil(satir_id):
    satir = SatinAlmaSiparisiSatir.query.get_or_404(satir_id)
    siparis_id = satir.siparis_id
    db.session.delete(satir)
    db.session.flush()
    # Toplam tutari yeniden hesapla
    siparis = SatinAlmaSiparisi.query.get(siparis_id)
    siparis.toplam_tutar = sum(s.hesapla_tutar() for s in siparis.satirlar)
    db.session.commit()
    flash('Urun silindi', 'success')
    return redirect(url_for('siparis.siparis_detay', id=siparis_id))

# Siparis durum guncelle
@siparis_bp.route('/siparis/<int:id>/durum/<string:yeni_durum>', methods=['POST'])
def siparis_durum_guncelle(id, yeni_durum):
    siparis = SatinAlmaSiparisi.query.get_or_404(id)
    siparis.durum = yeni_durum
    db.session.commit()
    flash(f'Siparis durumu: {yeni_durum}', 'success')
    return redirect(url_for('siparis.siparis_liste'))

# Siparis silme
@siparis_bp.route('/siparis/<int:id>/sil', methods=['POST'])
def siparis_sil(id):
    siparis = SatinAlmaSiparisi.query.get_or_404(id)
    siparis.aktif = 0
    db.session.commit()
    flash('Siparis silindi', 'success')
    return redirect(url_for('siparis.siparis_liste'))
