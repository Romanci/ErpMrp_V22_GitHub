# Uretim emri yonetimi
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.uretim.models import UretimEmri, UretimOperasyonu, Tezgah
from app.stok.models import Urun

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
uretim_bp = Blueprint('uretim', __name__, template_folder=template_klasoru)

# Uretim emri listesi
@uretim_bp.route('/uretim-emirleri')
def uretim_emri_liste():
    durum   = request.args.get('durum', '')
    oncelik = request.args.get('oncelik', '')
    ara     = request.args.get('ara', '')
    q = UretimEmri.query.filter_by(aktif=1)
    if durum:
        q = q.filter_by(durum=durum)
    if oncelik:
        q = q.filter_by(oncelik=oncelik)
    if ara:
        from app.stok.models import Urun as _Urun
        q = q.join(_Urun, isouter=True).filter(
            db.or_(
                UretimEmri.emir_no.ilike(f'%{ara}%'),
                _Urun.urun_adi.ilike(f'%{ara}%')
            )
        )
    emirler = q.order_by(UretimEmri.emir_no.desc()).all()
    return render_template('uretim/uretim_emri_liste.html', emirler=emirler)

# Yeni uretim emri
@uretim_bp.route('/uretim-emri/yeni', methods=['GET', 'POST'])
def uretim_emri_ekle():
    if request.method == 'POST':
        yeni_emir = UretimEmri(
            emir_no=request.form['emir_no'],
            urun_id=request.form['urun_id'],
            miktar=float(request.form['miktar']),
            planlanan_baslangic=request.form.get('planlanan_baslangic'),
            planlanan_bitis=request.form.get('planlanan_bitis'),
            oncelik=request.form.get('oncelik', 'normal'),
            aciklama=request.form.get('aciklama')
        )
        db.session.add(yeni_emir)
        db.session.commit()
        flash('Uretim emri olusturuldu', 'success')
        return redirect(url_for('uretim.uretim_emri_detay', id=yeni_emir.id))
    
    urunler = Urun.query.filter_by(aktif=1).all()
    return render_template('uretim/uretim_emri_form.html', emir=None, urunler=urunler)

# Uretim emri detay
@uretim_bp.route('/uretim-emri/<int:id>')
def uretim_emri_detay(id):
    emir = UretimEmri.query.get_or_404(id)
    tezgahlar = Tezgah.query.filter_by(aktif=1).all()
    return render_template('uretim/uretim_emri_detay.html', emir=emir, tezgahlar=tezgahlar)

# Operasyon ekle
@uretim_bp.route('/uretim-emri/<int:emir_id>/operasyon/ekle', methods=['POST'])
def operasyon_ekle(emir_id):
    yeni_operasyon = UretimOperasyonu(
        uretim_emri_id=emir_id,
        operasyon_sirasi=int(request.form['operasyon_sirasi']),
        operasyon_adi=request.form['operasyon_adi'],
        tezgah_id=request.form.get('tezgah_id') or None,
        planlanan_sure=float(request.form.get('planlanan_sure', 0)),
        aciklama=request.form.get('aciklama')
    )
    db.session.add(yeni_operasyon)
    db.session.commit()
    flash('Operasyon eklendi', 'success')
    return redirect(url_for('uretim.uretim_emri_detay', id=emir_id))

# Operasyon baslat
@uretim_bp.route('/operasyon/<int:id>/baslat', methods=['POST'])
def operasyon_baslat(id):
    operasyon = UretimOperasyonu.query.get_or_404(id)
    from datetime import datetime
    operasyon.durum = 'devam'
    operasyon.baslangic_zamani = datetime.now().strftime('%d.%m.%Y %H:%M')
    db.session.commit()
    flash('Operasyon baslatildi', 'success')
    return redirect(url_for('uretim.uretim_emri_detay', id=operasyon.uretim_emri_id))

# Operasyon bitir
@uretim_bp.route('/operasyon/<int:id>/bitir', methods=['POST'])
def operasyon_bitir(id):
    operasyon = UretimOperasyonu.query.get_or_404(id)
    from datetime import datetime
    operasyon.durum = 'tamamlandi'
    operasyon.bitis_zamani = datetime.now().strftime('%d.%m.%Y %H:%M')
    operasyon.fire_miktari = float(request.form.get('fire_miktari', 0))
    operasyon.gerceklesen_sure = float(request.form.get('gerceklesen_sure', 0))
    db.session.commit()
    flash('Operasyon tamamlandi', 'success')
    return redirect(url_for('uretim.uretim_emri_detay', id=operasyon.uretim_emri_id))

# Uretim emri durum guncelle
@uretim_bp.route('/uretim-emri/<int:id>/durum/<string:yeni_durum>', methods=['POST'])
def uretim_durum_guncelle(id, yeni_durum):
    emir = UretimEmri.query.get_or_404(id)
    emir.durum = yeni_durum
    if yeni_durum == 'tamamlandi':
        from datetime import datetime
        emir.gerceklesen_bitis = datetime.now().strftime('%d.%m.%Y')
    db.session.commit()
    flash(f'Uretim emri durumu: {yeni_durum}', 'success')
    return redirect(url_for('uretim.uretim_emri_liste'))

# Operasyon sil
@uretim_bp.route('/operasyon/<int:id>/sil', methods=['POST'])
def operasyon_sil(id):
    operasyon = UretimOperasyonu.query.get_or_404(id)
    emir_id = operasyon.uretim_emri_id
    if operasyon.durum == 'devam':
        flash('Devam eden operasyon silinemez', 'error')
        return redirect(url_for('uretim.uretim_emri_detay', id=emir_id))
    db.session.delete(operasyon)
    db.session.commit()
    flash('Operasyon silindi', 'success')
    return redirect(url_for('uretim.uretim_emri_detay', id=emir_id))

# Uretim emri sil
@uretim_bp.route('/uretim-emri/<int:id>/sil', methods=['POST'])
def uretim_emri_sil(id):
    emir = UretimEmri.query.get_or_404(id)
    if emir.durum == 'devam':
        flash('Devam eden uretim emri silinemez', 'error')
        return redirect(url_for('uretim.uretim_emri_liste'))
    emir.aktif = 0
    db.session.commit()
    flash('Uretim emri silindi', 'success')
    return redirect(url_for('uretim.uretim_emri_liste'))
