# Maliyet Hesaplama - BOM bazli uretim maliyeti analizi
import os
from flask import Blueprint, render_template, request
from app import db
from app.stok.models import Urun, StokHareket
from app.uretim.models import Bom, UretimEmri
from app.satin_alma.models import SatinAlmaSiparisiSatir
from sqlalchemy import func

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'stok', 'templates')
maliyet_bp = Blueprint('maliyet', __name__, template_folder=template_klasoru)


def _ortalama_alis_fiyati(urun_id):
    """Son 10 alis hareketinin agirlikli ortalama fiyatini hesapla"""
    # Once siparis satirlarindan bakilir
    son_satirlar = SatinAlmaSiparisiSatir.query.filter_by(urun_id=urun_id)\
        .order_by(SatinAlmaSiparisiSatir.id.desc()).limit(10).all()
    if son_satirlar:
        toplam_tutar = sum(s.miktar * s.birim_fiyat for s in son_satirlar)
        toplam_miktar = sum(s.miktar for s in son_satirlar)
        if toplam_miktar > 0:
            return round(toplam_tutar / toplam_miktar, 4)
    # Yoksa urun kartindaki alis fiyati
    urun = Urun.query.get(urun_id)
    return urun.alis_fiyati if urun and urun.alis_fiyati else 0


def _bom_maliyet_hesapla(urun_id, miktar=1):
    """
    Bir urunun BOM'una gore uretim maliyetini hesapla.
    Returns dict with malzeme listesi ve toplam maliyet
    """
    bom = Bom.query.filter_by(urun_id=urun_id, gecerli=1).first()
    if not bom:
        return None

    satirlar = []
    toplam_malzeme_maliyeti = 0

    for satir in bom.satirlar:
        ham_madde = satir.ham_madde
        if not ham_madde:
            continue
        fire_katsayi = 1 + (satir.fire_orani / 100.0)
        gereken_miktar = satir.miktar * miktar * fire_katsayi
        birim_fiyat = _ortalama_alis_fiyati(satir.ham_madde_id)
        satir_maliyet = gereken_miktar * birim_fiyat

        satirlar.append({
            'urun': ham_madde,
            'bom_miktar': satir.miktar,
            'fire_orani': satir.fire_orani,
            'gereken_miktar': round(gereken_miktar, 4),
            'birim_fiyat': birim_fiyat,
            'satir_maliyet': round(satir_maliyet, 2),
            'fiyat_kaynak': 'siparis' if _ortalama_alis_fiyati(satir.ham_madde_id) != ham_madde.alis_fiyati else 'kart',
        })
        toplam_malzeme_maliyeti += satir_maliyet

    return {
        'bom': bom,
        'satirlar': satirlar,
        'toplam_malzeme': round(toplam_malzeme_maliyeti, 2),
        'miktar': miktar,
    }


@maliyet_bp.route('/maliyet')
def maliyet_analiz():
    """Tüm aktif ürünler için BOM maliyet özeti"""
    urunler_bomlu = []
    urunler_bomsuz = []

    urunler = Urun.query.filter_by(aktif=1).all()
    for urun in urunler:
        sonuc = _bom_maliyet_hesapla(urun.id, 1)
        if sonuc:
            urunler_bomlu.append({
                'urun': urun,
                'maliyet': sonuc['toplam_malzeme'],
                'satir_sayisi': len(sonuc['satirlar']),
                'kar_marji': round(
                    ((urun.satis_fiyati - sonuc['toplam_malzeme']) / urun.satis_fiyati * 100), 1
                ) if urun.satis_fiyati and urun.satis_fiyati > 0 else None
            })
        else:
            urunler_bomsuz.append(urun)

    return render_template('maliyet/maliyet_analiz.html',
                           urunler_bomlu=urunler_bomlu,
                           urunler_bomsuz=urunler_bomsuz)


@maliyet_bp.route('/maliyet/urun/<int:urun_id>')
def urun_maliyet_detay(urun_id):
    """Tek bir ürünün detaylı maliyet kartı"""
    urun = Urun.query.get_or_404(urun_id)
    miktar = float(request.args.get('miktar', 1))
    sonuc = _bom_maliyet_hesapla(urun_id, miktar)

    # Uretim emirleri maliyeti (gecmis)
    emirler = UretimEmri.query.filter_by(urun_id=urun_id, aktif=1).order_by(UretimEmri.id.desc()).limit(10).all()
    emir_maliyetleri = []
    for emir in emirler:
        es = _bom_maliyet_hesapla(urun_id, emir.miktar)
        emir_maliyetleri.append({
            'emir': emir,
            'maliyet': es['toplam_malzeme'] if es else 0,
        })

    return render_template('maliyet/urun_maliyet_detay.html',
                           urun=urun,
                           sonuc=sonuc,
                           miktar=miktar,
                           emir_maliyetleri=emir_maliyetleri)
