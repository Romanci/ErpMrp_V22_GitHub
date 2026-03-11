# Tezgah yonetimi
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.uretim.models import Tezgah

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
tezgah_bp = Blueprint('tezgah', __name__, template_folder=template_klasoru)

# Tezgah listesi
@tezgah_bp.route('/tezgahlar')
def tezgah_liste():
    tezgahlar = Tezgah.query.filter_by(aktif=1).all()
    return render_template('uretim/tezgah_liste.html', tezgahlar=tezgahlar)

# Tezgah ekleme
@tezgah_bp.route('/tezgah/yeni', methods=['GET', 'POST'])
def tezgah_ekle():
    if request.method == 'POST':
        yeni_tezgah = Tezgah(
            tezgah_kodu=request.form['tezgah_kodu'],
            tezgah_adi=request.form['tezgah_adi'],
            tezgah_tipi=request.form.get('tezgah_tipi'),
            marka=request.form.get('marka'),
            model=request.form.get('model'),
            seri_no=request.form.get('seri_no'),
            lokasyon=request.form.get('lokasyon'),
            kapasite=float(request.form.get('kapasite', 8)),
            verimlilik_orani=float(request.form.get('verimlilik_orani', 100)),
            bakim_periyodu_gun=int(request.form.get('bakim_periyodu_gun', 90)),
            garanti_bitis=request.form.get('garanti_bitis') or None,
            sonraki_bakim=request.form.get('sonraki_bakim') or None
        )
        db.session.add(yeni_tezgah)
        db.session.commit()
        flash('Tezgah eklendi', 'success')
        return redirect(url_for('tezgah.tezgah_liste'))
    
    return render_template('uretim/tezgah_form.html', tezgah=None)

# Tezgah duzenleme
@tezgah_bp.route('/tezgah/<int:id>/duzenle', methods=['GET', 'POST'])
def tezgah_duzenle(id):
    tezgah = Tezgah.query.get_or_404(id)
    
    if request.method == 'POST':
        tezgah.tezgah_kodu = request.form['tezgah_kodu']
        tezgah.tezgah_adi = request.form['tezgah_adi']
        tezgah.tezgah_tipi = request.form.get('tezgah_tipi')
        tezgah.marka = request.form.get('marka')
        tezgah.model = request.form.get('model')
        tezgah.seri_no = request.form.get('seri_no')
        tezgah.lokasyon = request.form.get('lokasyon')
        tezgah.kapasite = float(request.form.get('kapasite', 8))
        tezgah.verimlilik_orani = float(request.form.get('verimlilik_orani', 100))
        tezgah.bakim_periyodu_gun = int(request.form.get('bakim_periyodu_gun', 90))
        tezgah.garanti_bitis = request.form.get('garanti_bitis') or None
        tezgah.sonraki_bakim = request.form.get('sonraki_bakim') or None
        tezgah.durum = request.form.get('durum', 'musait')
        db.session.commit()
        flash('Tezgah guncellendi', 'success')
        return redirect(url_for('tezgah.tezgah_liste'))
    
    return render_template('uretim/tezgah_form.html', tezgah=tezgah)

# Tezgah silme
@tezgah_bp.route('/tezgah/<int:id>/sil', methods=['POST'])
def tezgah_sil(id):
    tezgah = Tezgah.query.get_or_404(id)
    tezgah.aktif = 0
    db.session.commit()
    flash('Tezgah silindi', 'success')
    return redirect(url_for('tezgah.tezgah_liste'))
