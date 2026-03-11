# Kategori yonetimi
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.stok.models import Kategori, Urun

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
kategori_bp = Blueprint('kategori', __name__, template_folder=template_klasoru)

# Kategori listesi
@kategori_bp.route('/kategoriler')
def kategori_liste():
    kategoriler = Kategori.query.filter(Kategori.ust_kategori_id == None).all()
    return render_template('stok/kategori_liste.html', kategoriler=kategoriler)

# Kategori ekle
@kategori_bp.route('/kategori/yeni', methods=['GET', 'POST'])
def kategori_ekle():
    if request.method == 'POST':
        yeni = Kategori(
            kategori_adi=request.form['kategori_adi'],
            ust_kategori_id=request.form.get('ust_kategori_id') or None
        )
        db.session.add(yeni)
        db.session.commit()
        flash('Kategori eklendi', 'success')
        return redirect(url_for('kategori.kategori_liste'))
    kategoriler = Kategori.query.all()
    return render_template('stok/kategori_form.html', kategori=None, kategoriler=kategoriler)

# Kategori duzenle
@kategori_bp.route('/kategori/<int:id>/duzenle', methods=['GET', 'POST'])
def kategori_duzenle(id):
    kategori = Kategori.query.get_or_404(id)
    if request.method == 'POST':
        kategori.kategori_adi = request.form['kategori_adi']
        kategori.ust_kategori_id = request.form.get('ust_kategori_id') or None
        db.session.commit()
        flash('Kategori guncellendi', 'success')
        return redirect(url_for('kategori.kategori_liste'))
    kategoriler = Kategori.query.filter(Kategori.id != id).all()
    return render_template('stok/kategori_form.html', kategori=kategori, kategoriler=kategoriler)

# Kategori sil
@kategori_bp.route('/kategori/<int:id>/sil', methods=['POST'])
def kategori_sil(id):
    kategori = Kategori.query.get_or_404(id)
    # Bagli urun var mi?
    urun_sayisi = Urun.query.filter_by(kategori_id=id, aktif=1).count()
    if urun_sayisi > 0:
        flash(f'Bu kategoriye bagli {urun_sayisi} urun var. Once urunleri baska kategoriye tasiyin.', 'error')
        return redirect(url_for('kategori.kategori_liste'))
    db.session.delete(kategori)
    db.session.commit()
    flash('Kategori silindi', 'success')
    return redirect(url_for('kategori.kategori_liste'))
