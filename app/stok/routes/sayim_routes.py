# Sayim islemleri yonetimi
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.stok.models import Sayim, SayimDuzeltme, Depo, Urun, StokHareket

# Blueprint tanimi
template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
sayim_bp = Blueprint('sayim', __name__, template_folder=template_klasoru)

# Sayim listesi
@sayim_bp.route('/sayimlar')
def sayim_liste():
    sayimlar = Sayim.query.order_by(Sayim.sayim_tarihi.desc()).all()
    return render_template('stok/sayim_liste.html', sayimlar=sayimlar)

# Yeni sayim baslat
@sayim_bp.route('/sayim/yeni', methods=['GET', 'POST'])
def sayim_baslat():
    if request.method == 'POST':
        yeni_sayim = Sayim(
            depo_id=request.form['depo_id'],
            sayim_tarihi=request.form['sayim_tarihi'],
            kullanici_id=1  # Gecici olarak sabit kullanici
        )
        db.session.add(yeni_sayim)
        db.session.commit()
        flash('Sayim baslatildi', 'success')
        return redirect(url_for('sayim.sayim_detay', id=yeni_sayim.id))
    
    depolar = Depo.query.filter_by(aktif=1).all()
    return render_template('stok/sayim_form.html', depolar=depolar, sayim=None)

# Sayim detay ve sayim yapma
@sayim_bp.route('/sayim/<int:id>')
def sayim_detay(id):
    sayim = Sayim.query.get_or_404(id)
    urunler = Urun.query.filter_by(aktif=1).all()
    
    # Mevcut sayim satirlarini al
    mevcut_satirlar = {d.urun_id: d for d in sayim.duzeltmeler}
    
    return render_template('stok/sayim_detay.html', sayim=sayim, urunler=urunler, mevcut_satirlar=mevcut_satirlar)

# Sayim satiri ekle/guncelle
@sayim_bp.route('/sayim/<int:sayim_id>/satir/ekle', methods=['POST'])
def sayim_satir_ekle(sayim_id):
    urun_id = request.form['urun_id']
    sayilan_miktar = float(request.form['sayilan_miktar'])
    sayim = Sayim.query.get_or_404(sayim_id)

    # DUZELTME: Sistemdeki gercek stok miktarini hesapla (giris - cikis)
    from sqlalchemy import func
    giris = db.session.query(func.sum(StokHareket.miktar)).filter(
        StokHareket.urun_id == urun_id,
        StokHareket.depo_id == sayim.depo_id,
        StokHareket.hareket_tipi == 'giris'
    ).scalar() or 0
    cikis = db.session.query(func.sum(StokHareket.miktar)).filter(
        StokHareket.urun_id == urun_id,
        StokHareket.depo_id == sayim.depo_id,
        StokHareket.hareket_tipi == 'cikis'
    ).scalar() or 0
    sistem_miktar = giris - cikis

    fark = sayilan_miktar - sistem_miktar
    
    # Mevcut satir varsa guncelle, yoksa yeni olustur
    mevcut_satir = SayimDuzeltme.query.filter_by(sayim_id=sayim_id, urun_id=urun_id).first()
    
    if mevcut_satir:
        mevcut_satir.sayilan_miktar = sayilan_miktar
        mevcut_satir.sistem_miktar = sistem_miktar
        mevcut_satir.fark = fark
    else:
        yeni_satir = SayimDuzeltme(
            sayim_id=sayim_id,
            urun_id=urun_id,
            sistem_miktar=sistem_miktar,
            sayilan_miktar=sayilan_miktar,
            fark=fark
        )
        db.session.add(yeni_satir)
    
    db.session.commit()
    flash('Sayim kaydedildi', 'success')
    return redirect(url_for('sayim.sayim_detay', id=sayim_id))

# Sayimi kapat ve farklari stok hareketine donustur
@sayim_bp.route('/sayim/<int:id>/kapat', methods=['POST'])
def sayim_kapat(id):
    sayim = Sayim.query.get_or_404(id)
    
    if sayim.durum == 'kapali':
        flash('Sayim zaten kapali', 'warning')
        return redirect(url_for('sayim.sayim_detay', id=id))
    
    # Her fark icin stok hareketi olustur
    for duzeltme in sayim.duzeltmeler:
        if duzeltme.fark != 0:
            hareket_tipi = 'giris' if duzeltme.fark > 0 else 'cikis'
            
            yeni_hareket = StokHareket(
                urun_id=duzeltme.urun_id,
                depo_id=sayim.depo_id,
                hareket_tipi=hareket_tipi,
                miktar=abs(duzeltme.fark),
                referans_tipi='sayim',
                referans_id=sayim.id,
                aciklama=f'Sayim duzeltme: {duzeltme.fark}'
            )
            db.session.add(yeni_hareket)
    
    sayim.durum = 'kapali'
    db.session.commit()
    flash('Sayim kapatildi ve farklar stoga islendi', 'success')
    return redirect(url_for('sayim.sayim_liste'))

# Sayim silme
@sayim_bp.route('/sayim/<int:id>/sil', methods=['POST'])
def sayim_sil(id):
    sayim = Sayim.query.get_or_404(id)
    
    if sayim.durum == 'kapali':
        flash('Kapali sayim silinemez', 'error')
        return redirect(url_for('sayim.sayim_liste'))
    
    db.session.delete(sayim)
    db.session.commit()
    flash('Sayim silindi', 'success')
    return redirect(url_for('sayim.sayim_liste'))
