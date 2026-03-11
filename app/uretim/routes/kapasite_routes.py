# Kapasite Planlama - Tezgah bazli is yuku ve kapasite analizi
import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request
from app import db
from app.uretim.models import UretimEmri, UretimOperasyonu
from app.uretim.models.tezgah import Tezgah

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
kapasite_bp = Blueprint('kapasite', __name__, template_folder=template_klasoru)


def _tezgah_is_yuku(tezgah_id, baslangic=None, bitis=None):
    """
    Bir tezgah icin belirlenen donemde toplam planlanan sure (dakika)
    ve aktif operasyon sayisini hesapla.
    """
    q = UretimOperasyonu.query.filter_by(tezgah_id=tezgah_id)
    q = q.filter(UretimOperasyonu.durum.in_(['beklemede', 'devam']))

    operasyonlar = q.all()
    toplam_sure = sum(o.planlanan_sure for o in operasyonlar if o.planlanan_sure)
    return {
        'operasyon_sayisi': len(operasyonlar),
        'toplam_sure_dk': toplam_sure,
        'toplam_sure_saat': round(toplam_sure / 60, 1),
    }


@kapasite_bp.route('/kapasite')
def kapasite_analiz():
    """Tum tezgahlar icin kapasite ozeti"""
    tezgahlar = Tezgah.query.filter_by(aktif=1).all()

    # Her tezgah icin is yuku hesapla
    tezgah_verileri = []
    for tezgah in tezgahlar:
        yuk = _tezgah_is_yuku(tezgah.id)

        # Tezgah gunluk kapasite (dakika) - varsayilan 8 saat = 480 dk
        # Tezgah modelinde kapasite alanı eklenebilir, şimdilik 480 dk varsayılan
        gunluk_kapasite_dk = getattr(tezgah, 'gunluk_kapasite_dk', 480) or 480

        # Kac gunluk is var
        kac_gun = round(yuk['toplam_sure_dk'] / gunluk_kapasite_dk, 1) if gunluk_kapasite_dk > 0 else 0

        # Yukluluk yuzdesi (7 gunluk donem icin)
        haftalik_kapasite = gunluk_kapasite_dk * 5  # 5 is gunu
        yukluluk = min(100, round(yuk['toplam_sure_dk'] / haftalik_kapasite * 100, 1)) if haftalik_kapasite > 0 else 0

        tezgah_verileri.append({
            'tezgah': tezgah,
            'operasyon_sayisi': yuk['operasyon_sayisi'],
            'toplam_sure_dk': yuk['toplam_sure_dk'],
            'toplam_sure_saat': yuk['toplam_sure_saat'],
            'kac_gun': kac_gun,
            'yukluluk': yukluluk,
            'durum': 'asiri' if yukluluk > 90 else ('yogun' if yukluluk > 60 else 'normal'),
        })

    # Ozet istatistikler
    aktif_operasyon = sum(v['operasyon_sayisi'] for v in tezgah_verileri)
    toplam_is_saati = sum(v['toplam_sure_saat'] for v in tezgah_verileri)
    asiri_yuklu = sum(1 for v in tezgah_verileri if v['durum'] == 'asiri')

    # Uretim emri ozeti
    bekleyen_emir = UretimEmri.query.filter_by(aktif=1, durum='beklemede').count()
    devam_eden = UretimEmri.query.filter_by(aktif=1, durum='devam').count()

    return render_template(
        'uretim/kapasite_analiz.html',
        tezgah_verileri=tezgah_verileri,
        aktif_operasyon=aktif_operasyon,
        toplam_is_saati=toplam_is_saati,
        asiri_yuklu=asiri_yuklu,
        bekleyen_emir=bekleyen_emir,
        devam_eden=devam_eden,
    )


@kapasite_bp.route('/kapasite/tezgah/<int:tezgah_id>')
def tezgah_kapasite_detay(tezgah_id):
    """Tek tezgah icin kapasite ve operasyon detayi"""
    tezgah = Tezgah.query.get_or_404(tezgah_id)

    # Aktif operasyonlar
    aktif_ops = UretimOperasyonu.query.filter_by(
        tezgah_id=tezgah_id
    ).filter(UretimOperasyonu.durum.in_(['beklemede', 'devam']))\
     .order_by(UretimOperasyonu.durum.desc(), UretimOperasyonu.operasyon_sirasi).all()

    # Tamamlanan son 20 operasyon
    tamamlanan = UretimOperasyonu.query.filter_by(
        tezgah_id=tezgah_id, durum='tamamlandi'
    ).order_by(UretimOperasyonu.id.desc()).limit(20).all()

    # Verimlilik hesabi (gerceklesen/planlanan)
    verimlilik_verileri = []
    for op in tamamlanan:
        if op.planlanan_sure and op.planlanan_sure > 0 and op.gerceklesen_sure:
            verimlilik = round(op.planlanan_sure / op.gerceklesen_sure * 100, 1)
            verimlilik_verileri.append(verimlilik)
    ort_verimlilik = round(sum(verimlilik_verileri) / len(verimlilik_verileri), 1) if verimlilik_verileri else None

    toplam_aktif_sure = sum(o.planlanan_sure for o in aktif_ops if o.planlanan_sure)

    return render_template(
        'uretim/tezgah_kapasite_detay.html',
        tezgah=tezgah,
        aktif_ops=aktif_ops,
        tamamlanan=tamamlanan,
        ort_verimlilik=ort_verimlilik,
        toplam_aktif_sure=toplam_aktif_sure,
        toplam_aktif_saat=round(toplam_aktif_sure / 60, 1),
    )
