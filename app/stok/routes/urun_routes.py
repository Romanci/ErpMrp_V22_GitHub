# Urun yonetimi URL rotalari - listeleme, ekleme, guncelleme, silme
import os
from app.kullanici.auth import yazma_gerekli, silme_gerekli
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app import db
from app.stok.models import Urun, Kategori

# Blueprint tanimi
template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
stok_bp = Blueprint('stok', __name__, template_folder=template_klasoru)

# Urun listesi sayfasi
@stok_bp.route('/urunler')
def urun_liste():
    ara         = request.args.get('ara', '')
    kategori_id = request.args.get('kategori_id', '')
    sadece_kritik = request.args.get('kritik', '')

    q = Urun.query.filter_by(aktif=1)
    if ara:
        q = q.filter(
            db.or_(
                Urun.urun_adi.ilike(f'%{ara}%'),
                Urun.stok_kodu.ilike(f'%{ara}%'),
                Urun.barkod.ilike(f'%{ara}%')
            )
        )
    if kategori_id:
        q = q.filter_by(kategori_id=int(kategori_id))

    urunler = q.order_by(Urun.urun_adi).all()

    if sadece_kritik == '1':
        from sqlalchemy import func
        from app.stok.models import StokHareket
        kritik = []
        for u in urunler:
            giris = db.session.query(func.sum(StokHareket.miktar)).filter_by(urun_id=u.id, hareket_tipi='giris').scalar() or 0
            cikis = db.session.query(func.sum(StokHareket.miktar)).filter_by(urun_id=u.id, hareket_tipi='cikis').scalar() or 0
            if u.min_stok > 0 and (giris - cikis) <= u.min_stok:
                kritik.append(u)
        urunler = kritik

    kategoriler = Kategori.query.order_by(Kategori.kategori_adi).all()
    return render_template('stok/urun_liste.html', urunler=urunler, kategoriler=kategoriler)

# Yeni urun ekleme sayfasi (GET) ve kaydetme (POST)
@stok_bp.route('/urun/yeni', methods=['GET', 'POST'])
@yazma_gerekli
def urun_ekle():
    if request.method == 'POST':
        # Formdan gelen verileri al
        yeni_urun = Urun(
            stok_kodu=request.form['stok_kodu'],
            barkod=request.form.get('barkod'),
            urun_adi=request.form['urun_adi'],
            birim=request.form['birim'],
            kategori_id=request.form.get('kategori_id') or None,
            min_stok=float(request.form.get('min_stok', 0)),
            max_stok=float(request.form.get('max_stok', 0)),
            alis_fiyati=float(request.form.get('alis_fiyati', 0)),
            satis_fiyati=float(request.form.get('satis_fiyati', 0)),
            kdv_orani=float(request.form.get('kdv_orani', 20)),
            parti_takibi=1 if request.form.get('parti_takibi') else 0
        )
        # Veritabanina kaydet
        db.session.add(yeni_urun)
        db.session.commit()
        flash('Urun basariyla eklendi', 'success')
        return redirect(url_for('stok.urun_liste'))
    
    # GET istegi - form sayfasini goster
    kategoriler = Kategori.query.all()
    return render_template('stok/urun_form.html', kategoriler=kategoriler, urun=None)

# Urun duzenleme
@stok_bp.route('/urun/<int:id>/duzenle', methods=['GET', 'POST'])
def urun_duzenle(id):
    urun = Urun.query.get_or_404(id)
    
    if request.method == 'POST':
        # Formdan gelen verilerle guncelle
        urun.stok_kodu = request.form['stok_kodu']
        urun.barkod = request.form.get('barkod')
        urun.urun_adi = request.form['urun_adi']
        urun.birim = request.form['birim']
        urun.kategori_id = request.form.get('kategori_id') or None
        urun.min_stok = float(request.form.get('min_stok', 0))
        urun.max_stok = float(request.form.get('max_stok', 0))
        urun.alis_fiyati = float(request.form.get('alis_fiyati', 0))
        urun.satis_fiyati = float(request.form.get('satis_fiyati', 0))
        urun.kdv_orani = float(request.form.get('kdv_orani', 20))
        urun.parti_takibi = 1 if request.form.get('parti_takibi') else 0
        
        db.session.commit()
        flash('Urun guncellendi', 'success')
        return redirect(url_for('stok.urun_liste'))
    
    kategoriler = Kategori.query.all()
    return render_template('stok/urun_form.html', urun=urun, kategoriler=kategoriler)

# Urun silme (soft delete)
@stok_bp.route('/urun/<int:id>/sil', methods=['POST'])
@silme_gerekli
def urun_sil(id):
    urun = Urun.query.get_or_404(id)
    urun.aktif = 0  # Pasif yap (gercek silme degil)
    db.session.commit()
    flash('Urun silindi', 'success')
    return redirect(url_for('stok.urun_liste'))

# API: Urun arama (JSON)
@stok_bp.route('/api/urun/ara')
def urun_ara():
    q = request.args.get('q', '')
    urunler = Urun.query.filter(
        Urun.urun_adi.contains(q) | Urun.stok_kodu.contains(q),
        Urun.aktif == 1
    ).limit(10).all()
    return jsonify([u.to_dict() for u in urunler])
