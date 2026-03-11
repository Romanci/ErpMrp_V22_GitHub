"""
Barkod / QR Kod modülü
- Ürün barkodu oluştur (Code128)
- QR kod oluştur (ürün/stok hareketi bilgisi)
- Barkod ile ürün arama (okuyucu ile)
- Toplu barkod etiketi sayfası
"""
import os
import io
import base64
from flask import Blueprint, request, jsonify, send_file, render_template, redirect, url_for, flash
from app.stok.models import Urun

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
barkod_bp = Blueprint('barkod', __name__, template_folder=template_klasoru)


def _barkod_olustur(metin, format='code128'):
    """Barkod PNG üret, base64 döndür"""
    try:
        import barcode
        from barcode.writer import ImageWriter
        buf = io.BytesIO()
        kod = barcode.get(format, str(metin), writer=ImageWriter())
        kod.write(buf, options={
            'module_height': 8,
            'module_width': 0.2,
            'font_size': 8,
            'text_distance': 2,
            'quiet_zone': 2,
            'background': 'white',
            'foreground': 'black',
        })
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')
    except Exception as e:
        return None


def _qr_olustur(metin):
    """QR kod PNG üret, base64 döndür"""
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=4, border=2)
        qr.add_data(str(metin))
        qr.make(fit=True)
        img = qr.make_image(fill_color='black', back_color='white')
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        buf.seek(0)
        return base64.b64encode(buf.read()).decode('utf-8')
    except Exception as e:
        return None


@barkod_bp.route('/barkod')
def barkod_panel():
    """Barkod yönetim paneli"""
    urunler = Urun.query.filter_by(aktif=1).order_by(Urun.urun_adi).all()
    return render_template('barkod/barkod_panel.html', urunler=urunler)


@barkod_bp.route('/api/barkod/<int:urun_id>')
def api_barkod(urun_id):
    """Tek ürün barkod + QR JSON"""
    urun = Urun.query.get_or_404(urun_id)
    metin = urun.barkod or urun.stok_kodu

    barkod_b64 = _barkod_olustur(metin)
    qr_b64 = _qr_olustur(
        f"KOD:{urun.stok_kodu}|AD:{urun.urun_adi}|BARKOD:{metin}"
    )

    return jsonify({
        'urun_id': urun.id,
        'stok_kodu': urun.stok_kodu,
        'urun_adi': urun.urun_adi,
        'barkod': metin,
        'barkod_img': barkod_b64,
        'qr_img': qr_b64,
    })


@barkod_bp.route('/api/barkod-ara')
def barkod_ara():
    """Barkod/stok koduyla ürün ara (okuyucu entegrasyonu)"""
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify({'bulundu': False, 'mesaj': 'Barkod boş'})

    urun = Urun.query.filter(
        (Urun.barkod == q) | (Urun.stok_kodu == q)
    ).filter_by(aktif=1).first()

    if not urun:
        return jsonify({'bulundu': False, 'mesaj': f'"{q}" bulunamadı'})

    from app import db
    from app.stok.models import StokHareket
    from sqlalchemy import func
    giris = db.session.query(func.sum(StokHareket.miktar)).filter(
        StokHareket.urun_id == urun.id, StokHareket.hareket_tipi == 'giris'
    ).scalar() or 0
    cikis = db.session.query(func.sum(StokHareket.miktar)).filter(
        StokHareket.urun_id == urun.id, StokHareket.hareket_tipi == 'cikis'
    ).scalar() or 0

    return jsonify({
        'bulundu': True,
        'urun': {
            'id': urun.id,
            'stok_kodu': urun.stok_kodu,
            'urun_adi': urun.urun_adi,
            'barkod': urun.barkod or '',
            'birim': urun.birim,
            'mevcut_stok': round(giris - cikis, 2),
            'min_stok': urun.min_stok,
            'alis_fiyati': urun.alis_fiyati,
            'satis_fiyati': urun.satis_fiyati,
            'url': f'/stok/urun/{urun.id}',
        }
    })


@barkod_bp.route('/barkod/etiket')
def etiket_sayfasi():
    """Seçili ürünler için yazdırılabilir barkod etiket sayfası"""
    ids = request.args.getlist('id', type=int)
    adet = request.args.get('adet', 1, type=int)

    if not ids:
        flash('Etiket için ürün seçin', 'warning')
        return redirect(url_for('barkod.barkod_panel'))

    urunler = Urun.query.filter(Urun.id.in_(ids), Urun.aktif == 1).all()
    etiketler = []
    for u in urunler:
        metin = u.barkod or u.stok_kodu
        b64 = _barkod_olustur(metin)
        qr64 = _qr_olustur(metin)
        for _ in range(adet):
            etiketler.append({
                'urun': u,
                'barkod_img': b64,
                'qr_img': qr64,
                'metin': metin,
            })

    return render_template('barkod/etiket_yazdir.html', etiketler=etiketler)
