"""Gelişmiş Raporlama - tarih aralıklı grafikler + PDF raporlar"""
import os, io
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, jsonify, send_file
from app import db
from sqlalchemy import func

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
gelismis_rapor_bp = Blueprint('gelismis_rapor', __name__, template_folder=template_klasoru)


def _gun_listesi(gun=30):
    bitis = datetime.now()
    baslangic = bitis - timedelta(days=gun)
    gunler = []
    cur = baslangic
    while cur <= bitis:
        gunler.append(cur.strftime('%d.%m.%Y'))
        cur += timedelta(days=1)
    return gunler, baslangic.strftime('%d.%m.%Y')


@gelismis_rapor_bp.route('/raporlar/gelismis')
def rapor_panel():
    return render_template('gelismis_rapor/rapor_panel.html')


@gelismis_rapor_bp.route('/api/rapor/stok-hareketler')
def api_stok_hareketler():
    from app.stok.models import StokHareket
    gun = request.args.get('gun', 30, type=int)
    gunler, _ = _gun_listesi(gun)
    giris_v, cikis_v = [], []
    for g in gunler:
        gi = db.session.query(func.sum(StokHareket.miktar)).filter(
            StokHareket.hareket_tipi == 'giris', StokHareket.tarih.like(g + '%')).scalar() or 0
        ci = db.session.query(func.sum(StokHareket.miktar)).filter(
            StokHareket.hareket_tipi == 'cikis', StokHareket.tarih.like(g + '%')).scalar() or 0
        giris_v.append(round(float(gi), 2))
        cikis_v.append(round(float(ci), 2))
    return jsonify({'etiketler': gunler, 'giris': giris_v, 'cikis': cikis_v})


@gelismis_rapor_bp.route('/api/rapor/satin-alma-ozet')
def api_satin_alma():
    from app.satin_alma.models import SatinAlmaSiparisi
    gun = request.args.get('gun', 30, type=int)
    _, bas = _gun_listesi(gun)
    siparisler = SatinAlmaSiparisi.query.filter(
        SatinAlmaSiparisi.aktif == 1, SatinAlmaSiparisi.siparis_tarihi >= bas).all()
    durum = {}
    aylik = {}
    tedarikci = {}
    for s in siparisler:
        durum[s.durum] = durum.get(s.durum, 0) + 1
        try:
            ay = (s.siparis_tarihi or '')[:7]
            t = float(s.toplam_tutar or 0)
            aylik[ay] = aylik.get(ay, 0) + t
            if s.tedarikci:
                ad = s.tedarikci.unvan[:20]
                tedarikci[ad] = tedarikci.get(ad, 0) + t
        except Exception:
            pass
    return jsonify({
        'toplam': len(siparisler),
        'toplam_tutar': round(sum(float(s.toplam_tutar or 0) for s in siparisler), 2),
        'durum_etiketler': list(durum.keys()),
        'durum_verileri': list(durum.values()),
        'ay_etiketler': sorted(aylik.keys()),
        'ay_verileri': [round(aylik[k], 2) for k in sorted(aylik.keys())],
        'tedarikci_etiketler': list(tedarikci.keys())[:8],
        'tedarikci_verileri': [round(v, 2) for v in list(tedarikci.values())[:8]],
    })


@gelismis_rapor_bp.route('/api/rapor/uretim-ozet')
def api_uretim():
    from app.uretim.models import UretimEmri
    gun = request.args.get('gun', 30, type=int)
    _, bas = _gun_listesi(gun)
    emirler = UretimEmri.query.filter(
        UretimEmri.aktif == 1, UretimEmri.planlanan_baslangic >= bas).all()
    durum = {}
    urun_m = {}
    for e in emirler:
        durum[e.durum] = durum.get(e.durum, 0) + 1
        if e.urun:
            ad = e.urun.urun_adi[:20]
            urun_m[ad] = urun_m.get(ad, 0) + float(e.miktar or 0)
    return jsonify({
        'toplam': len(emirler),
        'durum_etiketler': list(durum.keys()),
        'durum_verileri': list(durum.values()),
        'urun_etiketler': list(urun_m.keys())[:8],
        'urun_verileri': [round(v, 2) for v in list(urun_m.values())[:8]],
    })


@gelismis_rapor_bp.route('/api/rapor/kritik-stok')
def api_kritik_stok():
    from app.stok.models import Urun, StokHareket
    urunler = Urun.query.filter_by(aktif=1).all()
    liste = []
    for u in urunler:
        if u.min_stok <= 0:
            continue
        g = db.session.query(func.sum(StokHareket.miktar)).filter(
            StokHareket.urun_id == u.id, StokHareket.hareket_tipi == 'giris').scalar() or 0
        c = db.session.query(func.sum(StokHareket.miktar)).filter(
            StokHareket.urun_id == u.id, StokHareket.hareket_tipi == 'cikis').scalar() or 0
        mevcut = round(float(g - c), 2)
        if mevcut <= u.min_stok:
            oran = round((mevcut / u.min_stok) * 100, 1) if u.min_stok else 0
            liste.append({'kod': u.stok_kodu, 'ad': u.urun_adi, 'mevcut': mevcut,
                          'min': u.min_stok, 'birim': u.birim, 'oran': oran})
    liste.sort(key=lambda x: x['oran'])
    return jsonify({'kritikler': liste})


@gelismis_rapor_bp.route('/rapor/pdf/<tur>')
def pdf_rapor(tur):
    try:
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib import colors
        from reportlab.lib.units import cm
    except ImportError:
        return "reportlab kurulu degil. pip install reportlab", 500

    from app.stok.models.sistem_ayar import SistemAyar
    firma = SistemAyar.get('firma_adi', 'ERP')
    tarih = datetime.now().strftime('%d.%m.%Y %H:%M')
    buf = io.BytesIO()

    siyah = colors.HexColor('#1e293b')
    sari = colors.HexColor('#f5c518')
    acik = colors.HexColor('#f8fafc')

    styles = getSampleStyleSheet()
    h1 = ParagraphStyle('h1', parent=styles['Heading1'], fontSize=14, textColor=siyah, spaceAfter=2)
    sub = ParagraphStyle('sub', parent=styles['Normal'], fontSize=8, textColor=colors.grey, spaceAfter=10)

    def ts(header_color=siyah):
        return TableStyle([
            ('BACKGROUND', (0,0), (-1,0), header_color),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, acik]),
            ('GRID', (0,0), (-1,-1), 0.3, colors.HexColor('#e2e8f0')),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('LEFTPADDING', (0,0), (-1,-1), 5),
        ])

    elems = [
        Paragraph(f'{firma} — {tur.upper()} RAPORU', h1),
        Paragraph(f'Oluşturma: {tarih}', sub),
    ]

    if tur == 'stok':
        from app.stok.models import Urun, StokHareket
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4), topMargin=1.5*cm, bottomMargin=1.5*cm)
        urunler = Urun.query.filter_by(aktif=1).order_by(Urun.stok_kodu).all()
        rows = [['Stok Kodu','Ürün Adı','Birim','Giriş','Çıkış','Mevcut','Min Stok','Durum']]
        for u in urunler:
            g = db.session.query(func.sum(StokHareket.miktar)).filter(
                StokHareket.urun_id==u.id, StokHareket.hareket_tipi=='giris').scalar() or 0
            c = db.session.query(func.sum(StokHareket.miktar)).filter(
                StokHareket.urun_id==u.id, StokHareket.hareket_tipi=='cikis').scalar() or 0
            mevcut = round(float(g-c), 2)
            durum = 'KRİTİK' if u.min_stok > 0 and mevcut <= u.min_stok else 'Normal'
            rows.append([u.stok_kodu, u.urun_adi[:35], u.birim,
                        round(float(g),2), round(float(c),2), mevcut, u.min_stok, durum])
        tablo = Table(rows, colWidths=[2.5*cm,7*cm,1.5*cm,2*cm,2*cm,2*cm,2*cm,2*cm])
        stil = ts()
        for i, r in enumerate(rows[1:], 1):
            if r[-1] == 'KRİTİK':
                stil.add('TEXTCOLOR', (7,i), (7,i), colors.red)
                stil.add('FONTNAME', (7,i), (7,i), 'Helvetica-Bold')
        tablo.setStyle(stil)
        elems.append(tablo)
        dosya = f'stok_raporu_{datetime.now().strftime("%Y%m%d")}.pdf'

    elif tur == 'siparis':
        from app.satin_alma.models import SatinAlmaSiparisi
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4), topMargin=1.5*cm, bottomMargin=1.5*cm)
        siparisler = SatinAlmaSiparisi.query.filter_by(aktif=1).order_by(
            SatinAlmaSiparisi.siparis_tarihi.desc()).limit(300).all()
        rows = [['Sipariş No','Tedarikçi','Tarih','Teslimat','Durum','Toplam','Para']]
        for s in siparisler:
            rows.append([s.siparis_no, (s.tedarikci.unvan[:25] if s.tedarikci else '—'),
                s.siparis_tarihi, s.teslim_tarihi or '—', s.durum,
                f'{float(s.toplam_tutar or 0):.2f}', s.para_birimi])
        tablo = Table(rows, colWidths=[3*cm,6*cm,2.5*cm,2.5*cm,2*cm,2.5*cm,1.5*cm])
        tablo.setStyle(ts())
        elems.append(tablo)
        dosya = f'siparis_raporu_{datetime.now().strftime("%Y%m%d")}.pdf'

    elif tur == 'uretim':
        from app.uretim.models import UretimEmri
        doc = SimpleDocTemplate(buf, pagesize=landscape(A4), topMargin=1.5*cm, bottomMargin=1.5*cm)
        emirler = UretimEmri.query.filter_by(aktif=1).order_by(
            UretimEmri.planlanan_baslangic.desc()).limit(300).all()
        rows = [['Emir No','Ürün','Miktar','Birim','Başlangıç','Bitiş','Durum','Öncelik']]
        for e in emirler:
            rows.append([e.emir_no, (e.urun.urun_adi[:25] if e.urun else '—'),
                round(float(e.miktar or 0),2), e.birim or '',
                e.planlanan_baslangic or '—', e.planlanan_bitis or '—', e.durum, e.oncelik or '—'])
        tablo = Table(rows, colWidths=[3*cm,6*cm,1.5*cm,1.5*cm,2.5*cm,2.5*cm,2*cm,2*cm])
        tablo.setStyle(ts())
        elems.append(tablo)
        dosya = f'uretim_raporu_{datetime.now().strftime("%Y%m%d")}.pdf'

    elif tur == 'personel':
        from app.ik.models.personel import Personel
        doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm)
        personeller = Personel.query.filter_by(aktif=1).order_by(Personel.departman, Personel.soyad).all()
        rows = [['Ad Soyad','Departman','Pozisyon','Telefon','E-posta','İşe Giriş']]
        for p in personeller:
            rows.append([f'{p.ad} {p.soyad}', p.departman or '—', p.pozisyon or '—',
                p.telefon or '—', p.email or '—', p.ise_giris_tarihi or '—'])
        tablo = Table(rows, colWidths=[4*cm,3.5*cm,3.5*cm,2.5*cm,3.5*cm,2.5*cm])
        tablo.setStyle(ts())
        elems.append(tablo)
        dosya = f'personel_raporu_{datetime.now().strftime("%Y%m%d")}.pdf'

    elif tur == 'kritik-stok':
        from app.stok.models import Urun, StokHareket
        doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=1.5*cm, bottomMargin=1.5*cm)
        urunler = Urun.query.filter_by(aktif=1).all()
        rows = [['Stok Kodu','Ürün Adı','Mevcut','Min Stok','Birim','Doluluk %']]
        for u in urunler:
            if u.min_stok <= 0: continue
            g = db.session.query(func.sum(StokHareket.miktar)).filter(
                StokHareket.urun_id==u.id, StokHareket.hareket_tipi=='giris').scalar() or 0
            c = db.session.query(func.sum(StokHareket.miktar)).filter(
                StokHareket.urun_id==u.id, StokHareket.hareket_tipi=='cikis').scalar() or 0
            mevcut = round(float(g-c), 2)
            if mevcut <= u.min_stok:
                oran = round((mevcut/u.min_stok)*100, 1) if u.min_stok else 0
                rows.append([u.stok_kodu, u.urun_adi[:35], mevcut, u.min_stok, u.birim, f'%{oran}'])
        tablo = Table(rows, colWidths=[3*cm,7*cm,2*cm,2*cm,1.5*cm,2*cm])
        stil = ts(colors.HexColor('#dc2626'))
        tablo.setStyle(stil)
        elems.append(tablo)
        dosya = f'kritik_stok_{datetime.now().strftime("%Y%m%d")}.pdf'
    else:
        return 'Bilinmeyen rapor türü', 404

    doc.build(elems)
    buf.seek(0)
    return send_file(buf, mimetype='application/pdf', as_attachment=True, download_name=dosya)
