# Tedarikci yonetimi
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.satin_alma.models import Tedarikci

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
tedarikci_bp = Blueprint('tedarikci', __name__, template_folder=template_klasoru)

# Tedarikci listesi
@tedarikci_bp.route('/tedarikciler')
def tedarikci_liste():
    tedarikciler = Tedarikci.query.filter_by(aktif=1).all()
    return render_template('satin_alma/tedarikci_liste.html', tedarikciler=tedarikciler)

# Tedarikci ekleme
@tedarikci_bp.route('/tedarikci/yeni', methods=['GET', 'POST'])
def tedarikci_ekle():
    if request.method == 'POST':
        yeni_tedarikci = Tedarikci(
            tedarikci_kodu=request.form['tedarikci_kodu'],
            unvan=request.form['unvan'],
            yetkili_adi=request.form.get('yetkili_adi'),
            telefon=request.form.get('telefon'),
            email=request.form.get('email'),
            adres=request.form.get('adres'),
            vergi_dairesi=request.form.get('vergi_dairesi'),
            vergi_no=request.form.get('vergi_no'),
            para_birimi=request.form.get('para_birimi', 'TL'),
            banka_bilgisi=request.form.get('banka_bilgisi'),
            notlar=request.form.get('notlar')
        )
        db.session.add(yeni_tedarikci)
        db.session.commit()
        flash('Tedarikci eklendi', 'success')
        return redirect(url_for('tedarikci.tedarikci_liste'))
    
    return render_template('satin_alma/tedarikci_form.html', tedarikci=None)

# Tedarikci duzenleme
@tedarikci_bp.route('/tedarikci/<int:id>/duzenle', methods=['GET', 'POST'])
def tedarikci_duzenle(id):
    tedarikci = Tedarikci.query.get_or_404(id)
    
    if request.method == 'POST':
        tedarikci.tedarikci_kodu = request.form['tedarikci_kodu']
        tedarikci.unvan = request.form['unvan']
        tedarikci.yetkili_adi = request.form.get('yetkili_adi')
        tedarikci.telefon = request.form.get('telefon')
        tedarikci.email = request.form.get('email')
        tedarikci.adres = request.form.get('adres')
        tedarikci.vergi_dairesi = request.form.get('vergi_dairesi')
        tedarikci.vergi_no = request.form.get('vergi_no')
        tedarikci.para_birimi = request.form.get('para_birimi', 'TL')
        tedarikci.banka_bilgisi = request.form.get('banka_bilgisi')
        tedarikci.notlar = request.form.get('notlar')
        db.session.commit()
        flash('Tedarikci guncellendi', 'success')
        return redirect(url_for('tedarikci.tedarikci_liste'))
    
    return render_template('satin_alma/tedarikci_form.html', tedarikci=tedarikci)

# Tedarikci silme
@tedarikci_bp.route('/tedarikci/<int:id>/sil', methods=['POST'])
def tedarikci_sil(id):
    tedarikci = Tedarikci.query.get_or_404(id)
    tedarikci.aktif = 0
    db.session.commit()
    flash('Tedarikci silindi', 'success')
    return redirect(url_for('tedarikci.tedarikci_liste'))
