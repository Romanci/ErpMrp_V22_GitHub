# Parti takibi yonetimi
import os
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app import db
from app.stok.models import Parti, Urun, Depo

# Blueprint tanimi
template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
parti_bp = Blueprint('parti', __name__, template_folder=template_klasoru)

# Parti listesi
@parti_bp.route('/partiler')
def parti_liste():
    partiler = Parti.query.filter_by(aktif=1).order_by(Parti.uretim_tarihi.desc()).all()
    return render_template('stok/parti_liste.html', partiler=partiler)

# Yeni parti ekleme
@parti_bp.route('/parti/yeni', methods=['GET', 'POST'])
def parti_ekle():
    if request.method == 'POST':
        yeni_parti = Parti(
            urun_id=request.form['urun_id'],
            parti_kodu=request.form['parti_kodu'],
            uretim_tarihi=request.form.get('uretim_tarihi'),
            son_kullanma_tarihi=request.form.get('son_kullanma_tarihi'),
            miktar=float(request.form.get('miktar', 0)),
            depo_id=request.form.get('depo_id') or None
        )
        db.session.add(yeni_parti)
        db.session.commit()
        flash('Parti eklendi', 'success')
        return redirect(url_for('parti.parti_liste'))
    
    urunler = Urun.query.filter_by(aktif=1, parti_takibi=1).all()
    depolar = Depo.query.filter_by(aktif=1).all()
    return render_template('stok/parti_form.html', parti=None, urunler=urunler, depolar=depolar)

# Parti duzenleme
@parti_bp.route('/parti/<int:id>/duzenle', methods=['GET', 'POST'])
def parti_duzenle(id):
    parti = Parti.query.get_or_404(id)
    
    if request.method == 'POST':
        parti.urun_id = request.form['urun_id']
        parti.parti_kodu = request.form['parti_kodu']
        parti.uretim_tarihi = request.form.get('uretim_tarihi')
        parti.son_kullanma_tarihi = request.form.get('son_kullanma_tarihi')
        parti.miktar = float(request.form.get('miktar', 0))
        parti.depo_id = request.form.get('depo_id') or None
        db.session.commit()
        flash('Parti guncellendi', 'success')
        return redirect(url_for('parti.parti_liste'))
    
    urunler = Urun.query.filter_by(aktif=1, parti_takibi=1).all()
    depolar = Depo.query.filter_by(aktif=1).all()
    return render_template('stok/parti_form.html', parti=parti, urunler=urunler, depolar=depolar)

# Parti silme (soft delete)
@parti_bp.route('/parti/<int:id>/sil', methods=['POST'])
def parti_sil(id):
    parti = Parti.query.get_or_404(id)
    parti.aktif = 0
    db.session.commit()
    flash('Parti silindi', 'success')
    return redirect(url_for('parti.parti_liste'))

# API: Urunun partilerini getir
@parti_bp.route('/api/urun/<int:urun_id>/partiler')
def api_partiler(urun_id):
    partiler = Parti.query.filter_by(urun_id=urun_id, aktif=1).all()
    return jsonify([p.to_dict() for p in partiler])
