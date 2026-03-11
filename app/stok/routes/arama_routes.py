"""Global arama - tum modullerde anlık arama"""
import os
from flask import Blueprint, request, jsonify
from app.stok.models import Urun
from app.satin_alma.models import Tedarikci, SatinAlmaSiparisi
from app.uretim.models import UretimEmri

arama_bp = Blueprint('arama', __name__)

@arama_bp.route('/api/arama')
def global_arama():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        return jsonify({'sonuclar': []})

    sonuclar = []

    # Ürünler
    urunler = Urun.query.filter(
        Urun.aktif == 1,
        (Urun.urun_adi.ilike(f'%{q}%') | Urun.stok_kodu.ilike(f'%{q}%'))
    ).limit(5).all()
    for u in urunler:
        sonuclar.append({'tur': 'Ürün', 'baslik': u.urun_adi, 'alt': u.stok_kodu, 'url': f'/stok/urun/{u.id}', 'ikon': 'fa-box'})

    # Tedarikçiler
    tedarikciler = Tedarikci.query.filter(
        Tedarikci.aktif == 1,
        Tedarikci.unvan.ilike(f'%{q}%')
    ).limit(3).all()
    for t in tedarikciler:
        sonuclar.append({'tur': 'Tedarikçi', 'baslik': t.unvan, 'alt': t.tedarikci_kodu, 'url': f'/satin-alma/tedarikciler', 'ikon': 'fa-truck'})

    # Üretim emirleri
    emirler = UretimEmri.query.filter(
        UretimEmri.aktif == 1,
        UretimEmri.emir_no.ilike(f'%{q}%')
    ).limit(3).all()
    for e in emirler:
        urun_adi = e.urun.urun_adi if e.urun else ''
        sonuclar.append({'tur': 'Üretim', 'baslik': e.emir_no, 'alt': urun_adi, 'url': f'/uretim/emirler/{e.id}', 'ikon': 'fa-industry'})

    # Siparişler
    siparisler = SatinAlmaSiparisi.query.filter(
        SatinAlmaSiparisi.aktif == 1,
        SatinAlmaSiparisi.siparis_no.ilike(f'%{q}%')
    ).limit(3).all()
    for s in siparisler:
        sonuclar.append({'tur': 'Sipariş', 'baslik': s.siparis_no, 'alt': s.tedarikci.unvan if s.tedarikci else '', 'url': f'/satin-alma/siparis/{s.id}', 'ikon': 'fa-file-alt'})

    return jsonify({'sonuclar': sonuclar[:10]})
