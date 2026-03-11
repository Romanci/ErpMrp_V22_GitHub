import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.stok.models.sube import Sube

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
sube_bp = Blueprint('sube', __name__, template_folder=template_klasoru)


@sube_bp.route('/subeler')
def sube_liste():
    subeler = Sube.query.order_by(Sube.merkez_mi.desc(), Sube.sube_adi).all()
    return render_template('sube/sube_liste.html', subeler=subeler)


@sube_bp.route('/sube/yeni', methods=['GET', 'POST'])
@sube_bp.route('/sube/<int:id>/duzenle', methods=['GET', 'POST'])
def sube_form(id=None):
    sube = Sube.query.get_or_404(id) if id else Sube()
    if request.method == 'POST':
        sube.sube_kodu = request.form.get('sube_kodu', '').upper()
        sube.sube_adi = request.form.get('sube_adi', '')
        sube.adres = request.form.get('adres', '')
        sube.sehir = request.form.get('sehir', '')
        sube.telefon = request.form.get('telefon', '')
        sube.email = request.form.get('email', '')
        sube.mudur = request.form.get('mudur', '')
        sube.merkez_mi = 1 if request.form.get('merkez_mi') else 0

        # Merkez zaten varsa ve bu yeni merkez olacaksa eskisini kaldır
        if sube.merkez_mi:
            Sube.query.filter(Sube.id != (sube.id or 0)).update({'merkez_mi': 0})

        if not id:
            db.session.add(sube)
        try:
            db.session.commit()
            flash(f'Şube {"oluşturuldu" if not id else "güncellendi"}', 'success')
            return redirect(url_for('sube.sube_liste'))
        except Exception as e:
            db.session.rollback()
            flash(f'Hata: {str(e)}', 'danger')

    return render_template('sube/sube_form.html', sube=sube)


@sube_bp.route('/sube/<int:id>')
def sube_detay(id):
    sube = Sube.query.get_or_404(id)
    return render_template('sube/sube_detay.html', sube=sube)


@sube_bp.route('/sube/<int:id>/sil', methods=['POST'])
def sube_sil(id):
    sube = Sube.query.get_or_404(id)
    if sube.merkez_mi:
        flash('Merkez şube silinemez', 'danger')
        return redirect(url_for('sube.sube_liste'))
    sube.aktif = 0
    db.session.commit()
    flash('Şube pasife alındı', 'success')
    return redirect(url_for('sube.sube_liste'))


@sube_bp.route('/api/sube-ozet')
def sube_ozet():
    """Dashboard için şube özeti JSON"""
    from flask import jsonify
    from app.stok.models import StokHareket, Urun
    from sqlalchemy import func
    subeler = Sube.query.filter_by(aktif=1).all()
    sonuc = []
    for s in subeler:
        depo_sayisi = len([d for d in s.depolar if d.aktif])
        personel_sayisi = len([p for p in s.personeller if p.aktif])
        sonuc.append({
            'id': s.id,
            'ad': s.sube_adi,
            'sehir': s.sehir or '',
            'depo': depo_sayisi,
            'personel': personel_sayisi,
            'merkez': bool(s.merkez_mi),
        })
    return jsonify(sonuc)
