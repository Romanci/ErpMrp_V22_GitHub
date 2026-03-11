import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.arac.models.arac import Arac, AracBakim, YakitKayit
from app.kullanici.auth import yazma_gerekli, admin_gerekli

_tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
arac_bp = Blueprint('arac', __name__, template_folder=_tpl)

@arac_bp.route('/')
def arac_dashboard():
    araclar = Arac.query.filter_by(aktif=1).all()
    uyarilar = [a for a in araclar if a.muayene_uyari]
    return render_template('arac/arac_dashboard.html', araclar=araclar, uyarilar=uyarilar)

@arac_bp.route('/liste')
def arac_liste():
    araclar = Arac.query.filter_by(aktif=1).order_by(Arac.plaka).all()
    return render_template('arac/arac_liste.html', araclar=araclar)

@arac_bp.route('/yeni', methods=['GET', 'POST'])
@arac_bp.route('/<int:id>/duzenle', methods=['GET', 'POST'])
@yazma_gerekli
def arac_form(id=None):
    a = Arac.query.get_or_404(id) if id else Arac()
    if request.method == 'POST':
        for alan in ['plaka','marka','model','sase_no','motor_no','yakit_turu','renk','notlar']:
            setattr(a, alan, request.form.get(alan, ''))
        a.yil = int(request.form.get('yil') or 0) or None
        a.tur = request.form.get('tur', 'arac')
        for tarih_alan in ['muayene_tarihi','sigorta_tarihi','kasko_tarihi']:
            setattr(a, tarih_alan, request.form.get(tarih_alan) or None)
        a.sorumlu_personel_id = request.form.get('sorumlu_personel_id') or None
        if not id: db.session.add(a)
        try:
            db.session.commit()
            flash('Araç kaydedildi', 'success')
            return redirect(url_for('arac.arac_detay', id=a.id))
        except Exception as e:
            db.session.rollback(); flash(f'Hata: {e}', 'danger')
    from app.ik.models.personel import Personel
    return render_template('arac/arac_form.html', arac=a,
        personeller=Personel.query.filter_by(aktif=1).all())

@arac_bp.route('/<int:id>')
def arac_detay(id):
    a = Arac.query.get_or_404(id)
    return render_template('arac/arac_detay.html', arac=a)

@arac_bp.route('/<int:arac_id>/bakim/ekle', methods=['POST'])
@yazma_gerekli
def bakim_ekle(arac_id):
    Arac.query.get_or_404(arac_id)
    b = AracBakim(
        arac_id=arac_id,
        bakim_turu=request.form.get('bakim_turu','genel'),
        tarih=request.form.get('tarih', datetime.now().strftime('%d.%m.%Y')),
        km=int(request.form.get('km') or 0),
        yapilan_isler=request.form.get('yapilan_isler',''),
        maliyet=float(request.form.get('maliyet') or 0),
        servis_yeri=request.form.get('servis_yeri',''),
        sonraki_bakim_km=int(request.form.get('sonraki_bakim_km') or 0) or None,
        sonraki_bakim_tarih=request.form.get('sonraki_bakim_tarih') or None,
    )
    db.session.add(b)
    db.session.commit()
    flash('Bakım kaydedildi', 'success')
    return redirect(url_for('arac.arac_detay', id=arac_id))

@arac_bp.route('/<int:arac_id>/yakit/ekle', methods=['POST'])
@yazma_gerekli
def yakit_ekle(arac_id):
    Arac.query.get_or_404(arac_id)
    litre = float(request.form.get('litre') or 0)
    fiyat = float(request.form.get('birim_fiyat') or 0)
    y = YakitKayit(
        arac_id=arac_id,
        tarih=request.form.get('tarih', datetime.now().strftime('%d.%m.%Y')),
        km=int(request.form.get('km') or 0),
        litre=litre, birim_fiyat=fiyat,
        toplam=litre*fiyat,
        istasyon=request.form.get('istasyon',''),
    )
    db.session.add(y)
    db.session.commit()
    flash('Yakıt kaydedildi', 'success')
    return redirect(url_for('arac.arac_detay', id=arac_id))
