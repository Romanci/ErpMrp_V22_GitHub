# Depo ve lokasyon yonetimi
import os
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app import db
from app.stok.models import Depo, StokLokasyon
from app.stok.models.sube import Sube

# Blueprint tanimi
template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
depo_bp = Blueprint('depo', __name__, template_folder=template_klasoru)

# Depo listesi
@depo_bp.route('/depolar')
def depo_liste():
    depolar = Depo.query.filter_by(aktif=1).all()
    return render_template('stok/depo_liste.html', depolar=depolar)

# Depo ekleme (GET: form, POST: kaydet)
@depo_bp.route('/depo/yeni', methods=['GET', 'POST'])
def depo_ekle():
    if request.method == 'POST':
        yeni_depo = Depo(
            depo_kodu=request.form['depo_kodu'],
            depo_adi=request.form['depo_adi'],
            adres=request.form.get('adres'),
            sube_id=request.form.get('sube_id') or None,
            yetkili_kullanici_id=request.form.get('yetkili_kullanici_id') or None
        )
        db.session.add(yeni_depo)
        db.session.commit()
        flash('Depo eklendi', 'success')
        return redirect(url_for('depo.depo_liste'))
    subeler = Sube.query.filter_by(aktif=1).all()
    return render_template('stok/depo_form.html', depo=None, subeler=subeler)

# Depo duzenleme
@depo_bp.route('/depo/<int:id>/duzenle', methods=['GET', 'POST'])
def depo_duzenle(id):
    depo = Depo.query.get_or_404(id)
    
    if request.method == 'POST':
        depo.depo_kodu = request.form['depo_kodu']
        depo.depo_adi = request.form['depo_adi']
        depo.adres = request.form.get('adres')
        depo.sube_id = request.form.get('sube_id') or None
        depo.yetkili_kullanici_id = request.form.get('yetkili_kullanici_id') or None
        db.session.commit()
        flash('Depo guncellendi', 'success')
        return redirect(url_for('depo.depo_liste'))
    subeler = Sube.query.filter_by(aktif=1).all()
    return render_template('stok/depo_form.html', depo=depo, subeler=subeler)

# Depo silme (soft delete)
@depo_bp.route('/depo/<int:id>/sil', methods=['POST'])
def depo_sil(id):
    depo = Depo.query.get_or_404(id)
    depo.aktif = 0
    db.session.commit()
    flash('Depo silindi', 'success')
    return redirect(url_for('depo.depo_liste'))

# Lokasyon ekleme
@depo_bp.route('/depo/<int:depo_id>/lokasyon/yeni', methods=['POST'])
def lokasyon_ekle(depo_id):
    yeni_lokasyon = StokLokasyon(
        depo_id=depo_id,
        lokasyon_kodu=request.form['lokasyon_kodu'],
        lokasyon_adi=request.form.get('lokasyon_adi')
    )
    db.session.add(yeni_lokasyon)
    db.session.commit()
    flash('Lokasyon eklendi', 'success')
    return redirect(url_for('depo.depo_liste'))

# API: Depo lokasyonlarini getir (JSON) - diger routelar icin
@depo_bp.route('/api/depo/<int:depo_id>/lokasyonlar')
def lokasyonlar_json(depo_id):
    lokasyonlar = StokLokasyon.query.filter_by(depo_id=depo_id, aktif=1).all()
    return jsonify([l.to_dict() for l in lokasyonlar])
