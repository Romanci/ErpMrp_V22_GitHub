# BOM (Bill of Materials) yonetimi
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.uretim.models import Bom, BomSatir
from app.stok.models import Urun

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
bom_bp = Blueprint('bom', __name__, template_folder=template_klasoru)

# BOM listesi
@bom_bp.route('/bomlar')
def bom_liste():
    bomlar = Bom.query.filter_by(gecerli=1).all()
    return render_template('uretim/bom_liste.html', bomlar=bomlar)

# Yeni BOM
@bom_bp.route('/bom/yeni', methods=['GET', 'POST'])
def bom_ekle():
    if request.method == 'POST':
        yeni_bom = Bom(
            urun_id=request.form['urun_id'],
            versiyon=request.form.get('versiyon', '1.0'),
            aciklama=request.form.get('aciklama')
        )
        db.session.add(yeni_bom)
        db.session.commit()
        flash('BOM olusturuldu', 'success')
        return redirect(url_for('bom.bom_detay', id=yeni_bom.id))
    
    urunler = Urun.query.filter_by(aktif=1).all()
    return render_template('uretim/bom_form.html', bom=None, urunler=urunler)

# BOM detay
@bom_bp.route('/bom/<int:id>')
def bom_detay(id):
    bom = Bom.query.get_or_404(id)
    urunler = Urun.query.filter_by(aktif=1).all()
    return render_template('uretim/bom_detay.html', bom=bom, urunler=urunler)

# BOM satiri ekle
@bom_bp.route('/bom/<int:bom_id>/satir/ekle', methods=['POST'])
def bom_satir_ekle(bom_id):
    yeni_satir = BomSatir(
        bom_id=bom_id,
        ham_madde_id=request.form['ham_madde_id'],
        miktar=float(request.form['miktar']),
        fire_orani=float(request.form.get('fire_orani', 0)),
        operasyon_sirasi=int(request.form.get('operasyon_sirasi', 1)),
        aciklama=request.form.get('aciklama')
    )
    db.session.add(yeni_satir)
    db.session.commit()
    flash('Malzeme eklendi', 'success')
    return redirect(url_for('bom.bom_detay', id=bom_id))

# BOM satiri sil
@bom_bp.route('/bom/satir/<int:satir_id>/sil', methods=['POST'])
def bom_satir_sil(satir_id):
    satir = BomSatir.query.get_or_404(satir_id)
    bom_id = satir.bom_id
    db.session.delete(satir)
    db.session.commit()
    flash('Malzeme silindi', 'success')
    return redirect(url_for('bom.bom_detay', id=bom_id))

# BOM sil
@bom_bp.route('/bom/<int:id>/sil', methods=['POST'])
def bom_sil(id):
    bom = Bom.query.get_or_404(id)
    db.session.delete(bom)
    db.session.commit()
    flash('BOM silindi', 'success')
    return redirect(url_for('bom.bom_liste'))
