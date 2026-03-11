# Stok hareketleri - giris, cikis, transfer islemleri
import os
from app.kullanici.auth import yazma_gerekli
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from app import db
from app.stok.models import StokHareket, Urun, Depo, StokLokasyon

# Blueprint tanimi
template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
hareket_bp = Blueprint('hareket', __name__, template_folder=template_klasoru)

# Stok hareket listesi
@hareket_bp.route('/hareketler')
def hareket_liste():
    tip  = request.args.get('tip', '')
    ara  = request.args.get('ara', '')
    tarih_bas = request.args.get('tarih_bas', '')
    tarih_bit = request.args.get('tarih_bit', '')

    q = StokHareket.query
    if tip:
        q = q.filter_by(hareket_tipi=tip)
    if ara:
        q = q.join(Urun, isouter=True).filter(
            db.or_(
                Urun.urun_adi.ilike(f'%{ara}%'),
                Urun.stok_kodu.ilike(f'%{ara}%'),
                StokHareket.referans_no.ilike(f'%{ara}%') if hasattr(StokHareket,'referans_no') else db.false()
            )
        )
    hareketler = q.order_by(StokHareket.tarih.desc()).limit(1000).all()
    urunler = Urun.query.filter_by(aktif=1).order_by(Urun.urun_adi).all()
    depolar = Depo.query.filter_by(aktif=1).all()
    return render_template('stok/hareket_liste.html',
                           hareketler=hareketler, urunler=urunler, depolar=depolar)

# Yeni stok girisi
@hareket_bp.route('/hareket/giris', methods=['GET', 'POST'])
@yazma_gerekli
def stok_giris():
    if request.method == 'POST':
        try:
            miktar = float(request.form['miktar'])
            if miktar <= 0:
                flash('Miktar sifirdan buyuk olmalidir!', 'error')
                urunler = Urun.query.filter_by(aktif=1).all()
                depolar = Depo.query.filter_by(aktif=1).all()
                return render_template('stok/hareket_form.html', hareket_tipi='giris', urunler=urunler, depolar=depolar, hareket=None)
        except (ValueError, TypeError):
            flash('Gecersiz miktar!', 'error')
            urunler = Urun.query.filter_by(aktif=1).all()
            depolar = Depo.query.filter_by(aktif=1).all()
            return render_template('stok/hareket_form.html', hareket_tipi='giris', urunler=urunler, depolar=depolar, hareket=None)

        yeni_hareket = StokHareket(
            urun_id=request.form['urun_id'],
            depo_id=request.form['depo_id'],
            lokasyon_id=request.form.get('lokasyon_id') or None,
            hareket_tipi='giris',
            miktar=miktar,
            birim_fiyat=float(request.form.get('birim_fiyat', 0) or 0),
            referans_tipi=request.form.get('referans_tipi'),
            aciklama=request.form.get('aciklama')
        )
        db.session.add(yeni_hareket)
        db.session.commit()
        flash('Stok girisi kaydedildi', 'success')
        return redirect(url_for('hareket.hareket_liste'))
    
    urunler = Urun.query.filter_by(aktif=1).all()
    depolar = Depo.query.filter_by(aktif=1).all()
    return render_template('stok/hareket_form.html', 
                         hareket_tipi='giris', 
                         urunler=urunler, 
                         depolar=depolar,
                         hareket=None)

# Stok cikisi
@hareket_bp.route('/hareket/cikis', methods=['GET', 'POST'])
@yazma_gerekli
def stok_cikis():
    if request.method == 'POST':
        try:
            miktar = float(request.form['miktar'])
            if miktar <= 0:
                flash('Miktar sifirdan buyuk olmalidir!', 'error')
                urunler = Urun.query.filter_by(aktif=1).all()
                depolar = Depo.query.filter_by(aktif=1).all()
                return render_template('stok/hareket_form.html', hareket_tipi='cikis', urunler=urunler, depolar=depolar, hareket=None)
        except (ValueError, TypeError):
            flash('Gecersiz miktar!', 'error')
            urunler = Urun.query.filter_by(aktif=1).all()
            depolar = Depo.query.filter_by(aktif=1).all()
            return render_template('stok/hareket_form.html', hareket_tipi='cikis', urunler=urunler, depolar=depolar, hareket=None)

        # Negatif stok kontrolu
        urun_id = request.form['urun_id']
        depo_id = request.form['depo_id']
        from sqlalchemy import func as sqlfunc
        giris_toplam = db.session.query(sqlfunc.sum(StokHareket.miktar)).filter(
            StokHareket.urun_id == urun_id,
            StokHareket.depo_id == depo_id,
            StokHareket.hareket_tipi == 'giris'
        ).scalar() or 0
        cikis_toplam = db.session.query(sqlfunc.sum(StokHareket.miktar)).filter(
            StokHareket.urun_id == urun_id,
            StokHareket.depo_id == depo_id,
            StokHareket.hareket_tipi == 'cikis'
        ).scalar() or 0
        mevcut_stok = giris_toplam - cikis_toplam
        if miktar > mevcut_stok:
            urun = Urun.query.get(urun_id)
            depo = Depo.query.get(depo_id)
            flash(f'Yetersiz stok! {urun.urun_adi if urun else ""} - {depo.depo_adi if depo else ""} deposunda mevcut: {mevcut_stok:.2f}, istenen: {miktar:.2f}', 'error')
            urunler = Urun.query.filter_by(aktif=1).all()
            depolar = Depo.query.filter_by(aktif=1).all()
            return render_template('stok/hareket_form.html', hareket_tipi='cikis', urunler=urunler, depolar=depolar, hareket=None)

        yeni_hareket = StokHareket(
            urun_id=urun_id,
            depo_id=depo_id,
            lokasyon_id=request.form.get('lokasyon_id') or None,
            hareket_tipi='cikis',
            miktar=miktar,
            birim_fiyat=float(request.form.get('birim_fiyat', 0) or 0),
            referans_tipi=request.form.get('referans_tipi'),
            aciklama=request.form.get('aciklama')
        )
        db.session.add(yeni_hareket)
        db.session.commit()
        flash('Stok cikisi kaydedildi', 'success')
        return redirect(url_for('hareket.hareket_liste'))
    
    urunler = Urun.query.filter_by(aktif=1).all()
    depolar = Depo.query.filter_by(aktif=1).all()
    return render_template('stok/hareket_form.html',
                         hareket_tipi='cikis',
                         urunler=urunler,
                         depolar=depolar,
                         hareket=None)

# Stok transferi (depo degisimi veya karantina)
@hareket_bp.route('/hareket/transfer', methods=['GET', 'POST'])
def stok_transfer():
    if request.method == 'POST':
        kaynak_depo_id = request.form['kaynak_depo_id']
        hedef_depo_id = request.form['hedef_depo_id']

        # Ayni depo kontrolu
        if kaynak_depo_id == hedef_depo_id:
            flash('Kaynak ve hedef depo ayni olamaz!', 'error')
            urunler = Urun.query.filter_by(aktif=1).all()
            depolar = Depo.query.filter_by(aktif=1).all()
            return render_template('stok/transfer_form.html', urunler=urunler, depolar=depolar)

        # Miktar kontrolu
        try:
            miktar = float(request.form['miktar'])
            if miktar <= 0:
                flash('Miktar sifirdan buyuk olmalidir!', 'error')
                urunler = Urun.query.filter_by(aktif=1).all()
                depolar = Depo.query.filter_by(aktif=1).all()
                return render_template('stok/transfer_form.html', urunler=urunler, depolar=depolar)
        except (ValueError, TypeError):
            flash('Gecersiz miktar!', 'error')
            urunler = Urun.query.filter_by(aktif=1).all()
            depolar = Depo.query.filter_by(aktif=1).all()
            return render_template('stok/transfer_form.html', urunler=urunler, depolar=depolar)

        # DUZELTME: Depo ID yerine depo adini açıklamaya yaz
        kaynak_depo = Depo.query.get(kaynak_depo_id)
        hedef_depo = Depo.query.get(hedef_depo_id)
        kaynak_adi = kaynak_depo.depo_adi if kaynak_depo else kaynak_depo_id
        hedef_adi = hedef_depo.depo_adi if hedef_depo else hedef_depo_id

        # Transfer icin kaynak depoda yeterli stok kontrolu
        urun_id = request.form['urun_id']
        from sqlalchemy import func as sqlfunc
        giris_toplam = db.session.query(sqlfunc.sum(StokHareket.miktar)).filter(
            StokHareket.urun_id == urun_id,
            StokHareket.depo_id == kaynak_depo_id,
            StokHareket.hareket_tipi == 'giris'
        ).scalar() or 0
        cikis_toplam = db.session.query(sqlfunc.sum(StokHareket.miktar)).filter(
            StokHareket.urun_id == urun_id,
            StokHareket.depo_id == kaynak_depo_id,
            StokHareket.hareket_tipi == 'cikis'
        ).scalar() or 0
        mevcut_stok = giris_toplam - cikis_toplam
        if miktar > mevcut_stok:
            urun = Urun.query.get(urun_id)
            flash(f'Yetersiz stok! {urun.urun_adi if urun else ""} - {kaynak_adi} deposunda mevcut: {mevcut_stok:.2f}, istenen: {miktar:.2f}', 'error')
            urunler = Urun.query.filter_by(aktif=1).all()
            depolar = Depo.query.filter_by(aktif=1).all()
            return render_template('stok/transfer_form.html', urunler=urunler, depolar=depolar)

        # Cikis hareketi (kaynak depo)
        cikis_hareket = StokHareket(
            urun_id=request.form['urun_id'],
            depo_id=kaynak_depo_id,
            lokasyon_id=request.form.get('kaynak_lokasyon_id') or None,
            hareket_tipi='cikis',
            miktar=miktar,
            referans_tipi='transfer',
            aciklama=f"Transfer -> Hedef: {hedef_adi}"
        )

        # Giris hareketi (hedef depo)
        giris_hareket = StokHareket(
            urun_id=request.form['urun_id'],
            depo_id=hedef_depo_id,
            lokasyon_id=request.form.get('hedef_lokasyon_id') or None,
            hareket_tipi='giris',
            miktar=miktar,
            referans_tipi='transfer',
            aciklama=f"Transfer <- Kaynak: {kaynak_adi}"
        )
        
        db.session.add(cikis_hareket)
        db.session.add(giris_hareket)
        db.session.commit()
        flash('Transfer tamamlandi', 'success')
        return redirect(url_for('hareket.hareket_liste'))
    
    urunler = Urun.query.filter_by(aktif=1).all()
    depolar = Depo.query.filter_by(aktif=1).all()
    return render_template('stok/transfer_form.html',
                         urunler=urunler,
                         depolar=depolar)

# NOT: Lokasyon API'si /stok/api/depo/X/lokasyonlar yolunda depo_routes.py'de tanimlidir.
# Bu blueprint ayni URL'yi kayit etmemek icin bu route burada tekrarlanmiyor.

