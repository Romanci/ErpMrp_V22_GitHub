# Stok raporlari ve analizler
import os
from flask import Blueprint, render_template
from app import db
from app.stok.models import Urun, Depo, StokHareket, Parti
from sqlalchemy import func

# Blueprint tanimi
template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
rapor_bp = Blueprint('rapor', __name__, template_folder=template_klasoru)

# Mevcut stok raporu
@rapor_bp.route('/rapor/mevcut-stok')
def mevcut_stok_raporu():
    # Her urun icin toplam stok miktarini hesapla
    # Basit versiyon: tum hareketleri topla (giris - cikis)
    
    urunler = Urun.query.filter_by(aktif=1).all()
    stok_durumu = []
    
    for urun in urunler:
        # Giris hareketleri toplami
        giris_toplam = db.session.query(func.sum(StokHareket.miktar)).filter(
            StokHareket.urun_id == urun.id,
            StokHareket.hareket_tipi == 'giris'
        ).scalar() or 0
        
        # Cikis hareketleri toplami
        cikis_toplam = db.session.query(func.sum(StokHareket.miktar)).filter(
            StokHareket.urun_id == urun.id,
            StokHareket.hareket_tipi == 'cikis'
        ).scalar() or 0
        
        mevcut_stok = giris_toplam - cikis_toplam

        # Durum belirleme: max_stok 0 ise sinirsiz kabul et
        if urun.min_stok > 0 and mevcut_stok <= urun.min_stok:
            durum = 'kritik'
        elif urun.max_stok > 0 and mevcut_stok > urun.max_stok:
            durum = 'fazla'
        else:
            durum = 'normal'

        stok_durumu.append({
            'urun': urun,
            'giris': giris_toplam,
            'cikis': cikis_toplam,
            'mevcut': mevcut_stok,
            'durum': durum
        })
    
    return render_template('stok/mevcut_stok_raporu.html', stok_durumu=stok_durumu)

# Kritik stok raporu
@rapor_bp.route('/rapor/kritik-stok')
def kritik_stok_raporu():
    urunler = Urun.query.filter_by(aktif=1).all()
    kritik_urunler = []
    
    for urun in urunler:
        giris_toplam = db.session.query(func.sum(StokHareket.miktar)).filter(
            StokHareket.urun_id == urun.id,
            StokHareket.hareket_tipi == 'giris'
        ).scalar() or 0
        
        cikis_toplam = db.session.query(func.sum(StokHareket.miktar)).filter(
            StokHareket.urun_id == urun.id,
            StokHareket.hareket_tipi == 'cikis'
        ).scalar() or 0
        
        mevcut_stok = giris_toplam - cikis_toplam

        # Sadece min_stok tanimli urunleri kontrol et
        if urun.min_stok > 0 and mevcut_stok <= urun.min_stok:
            kritik_urunler.append({
                'urun': urun,
                'mevcut': mevcut_stok,
                'min_stok': urun.min_stok,
                'eksik': urun.min_stok - mevcut_stok
            })
    
    return render_template('stok/kritik_stok_raporu.html', kritik_urunler=kritik_urunler)

# SKT yaklasan partiler raporu
@rapor_bp.route('/rapor/skt-yaklasan')
def skt_yaklasan_raporu():
    partiler = Parti.query.filter_by(aktif=1).all()
    yaklasan_partiler = []
    
    for parti in partiler:
        durum = parti.skt_durumu()
        if durum in ['Yaklasiyor', 'Gecti']:
            yaklasan_partiler.append({
                'parti': parti,
                'durum': durum
            })
    
    return render_template('stok/skt_raporu.html', partiler=yaklasan_partiler)
