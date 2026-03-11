"""Bildirim sistemi - kritik stok, gecikmis bakim, bekleyen izin"""
import os
from flask import Blueprint, jsonify, session
from app import db
from sqlalchemy import func
from datetime import datetime

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
bildirim_bp = Blueprint('bildirim', __name__, template_folder=template_klasoru)


def _tum_bildirimleri_topla():
    """Tum modullerdeki bildirimleri tek listede topla"""
    bildirimler = []

    # 1. Kritik stok
    try:
        from app.stok.models import Urun, StokHareket
        urunler = Urun.query.filter_by(aktif=1).all()
        for urun in urunler:
            if urun.min_stok <= 0:
                continue
            giris = db.session.query(func.sum(StokHareket.miktar)).filter(
                StokHareket.urun_id == urun.id, StokHareket.hareket_tipi == 'giris'
            ).scalar() or 0
            cikis = db.session.query(func.sum(StokHareket.miktar)).filter(
                StokHareket.urun_id == urun.id, StokHareket.hareket_tipi == 'cikis'
            ).scalar() or 0
            mevcut = giris - cikis
            if mevcut <= urun.min_stok:
                bildirimler.append({
                    'tip': 'kritik',
                    'ikon': 'fas fa-exclamation-triangle',
                    'baslik': f'Kritik Stok: {urun.urun_adi}',
                    'aciklama': f'Mevcut: {round(mevcut,2)} {urun.birim} (Min: {urun.min_stok})',
                    'url': f'/stok/urun/{urun.id}',
                    'renk': 'kirmizi',
                })
    except Exception:
        pass

    # 2. Gecikmiş bakım planı
    try:
        from app.bakim.models.bakim import BakimPlan
        from datetime import datetime, timedelta
        bugun = datetime.now().strftime('%d.%m.%Y')
        planlar = BakimPlan.query.filter_by(aktif=1).all()
        for plan in planlar:
            if not plan.sonraki_bakim:
                continue
            try:
                sn = datetime.strptime(plan.sonraki_bakim, '%d.%m.%Y')
                bg = datetime.now()
                fark = (sn - bg).days
                if fark <= 0:
                    bildirimler.append({
                        'tip': 'bakim',
                        'ikon': 'fas fa-wrench',
                        'baslik': f'Gecikmiş Bakım: {plan.bakim_adi}',
                        'aciklama': f'{abs(fark)} gün gecikmiş',
                        'url': '/bakim/',
                        'renk': 'kirmizi',
                    })
                elif fark <= 7:
                    bildirimler.append({
                        'tip': 'bakim',
                        'ikon': 'fas fa-tools',
                        'baslik': f'Yaklaşan Bakım: {plan.bakim_adi}',
                        'aciklama': f'{fark} gün sonra',
                        'url': '/bakim/',
                        'renk': 'sari',
                    })
            except Exception:
                pass
    except Exception:
        pass

    # 3. Bekleyen izin talepleri (sadece admin/mudur)
    try:
        if session.get('admin'):
            from app.ik.models.personel import Izin
            bekleyen = Izin.query.filter_by(durum='beklemede').count()
            if bekleyen > 0:
                bildirimler.append({
                    'tip': 'izin',
                    'ikon': 'fas fa-calendar-times',
                    'baslik': f'{bekleyen} Bekleyen İzin Talebi',
                    'aciklama': 'Onay bekliyor',
                    'url': '/ik/',
                    'renk': 'mavi',
                })
    except Exception:
        pass

    # 4. Açık arıza bildirimleri
    try:
        from app.bakim.models.bakim import ArizaKayit
        kritik_ariza = ArizaKayit.query.filter_by(durum='acik', oncelik='kritik').count()
        if kritik_ariza > 0:
            bildirimler.append({
                'tip': 'ariza',
                'ikon': 'fas fa-bolt',
                'baslik': f'{kritik_ariza} Kritik Arıza Açık',
                'aciklama': 'Hemen müdahale gerekiyor',
                'url': '/bakim/arizalar',
                'renk': 'kirmizi',
            })
    except Exception:
        pass

    # 5. Yaklaşan SKT
    try:
        from app.stok.models.parti import Parti
        from datetime import datetime, timedelta
        simdi = datetime.now()
        uyari_gun = 7
        try:
            from app.stok.models.sistem_ayar import SistemAyar
            uyari_gun = int(SistemAyar.get('stok_uyari_gunu', 7))
        except Exception:
            pass
        partiler = Parti.query.filter_by(aktif=1).all()
        skt_sayac = 0
        for p in partiler:
            if p.son_kullanma_tarihi:
                try:
                    skt = datetime.strptime(p.son_kullanma_tarihi, '%d.%m.%Y')
                    if (skt - simdi).days <= uyari_gun:
                        skt_sayac += 1
                except Exception:
                    pass
        if skt_sayac > 0:
            bildirimler.append({
                'tip': 'skt',
                'ikon': 'fas fa-calendar-day',
                'baslik': f'{skt_sayac} Parti SKT Yaklaşıyor',
                'aciklama': f'{uyari_gun} gün içinde son kullanma tarihi dolacak',
                'url': '/stok/partiler',
                'renk': 'sari',
            })
    except Exception:
        pass

    return bildirimler


@bildirim_bp.route('/api/bildirimler')
def api_bildirimler():
    """AJAX endpoint - bildirim sayısı ve listesi"""
    bildirimler = _tum_bildirimleri_topla()
    return jsonify({
        'sayi': len(bildirimler),
        'bildirimler': bildirimler[:10]  # max 10
    })


# ─── E-POSTA BİLDİRİMİ GÖNDERİMİ ──────────────────────────────────────────────
@bildirim_bp.route('/api/bildirim-email-gonder', methods=['POST'])
def bildirim_email_gonder():
    """
    Kritik stok + gecikmiş bakım e-postasını manuel veya otomatik tetikle.
    POST /api/bildirim-email-gonder
    """
    from app.stok.models.sistem_ayar import SistemAyar
    from app.stok.models.email_servis import EmailServis
    from app.stok.models import Urun, StokHareket

    alici = SistemAyar.get('bildirim_email', '')
    smtp_aktif = SistemAyar.get('smtp_aktif', '0')

    if smtp_aktif != '1':
        return jsonify({'ok': False, 'mesaj': 'SMTP aktif değil. Ayarlar > E-posta bölümünden etkinleştirin.'})
    if not alici:
        return jsonify({'ok': False, 'mesaj': 'Bildirim e-posta adresi tanımlı değil. Ayarlar > E-posta bölümünden girin.'})

    # Kritik stokları topla
    kritik_liste = []
    try:
        urunler = Urun.query.filter_by(aktif=1).all()
        for urun in urunler:
            if urun.min_stok <= 0:
                continue
            giris = db.session.query(func.sum(StokHareket.miktar)).filter(
                StokHareket.urun_id == urun.id, StokHareket.hareket_tipi == 'giris'
            ).scalar() or 0
            cikis = db.session.query(func.sum(StokHareket.miktar)).filter(
                StokHareket.urun_id == urun.id, StokHareket.hareket_tipi == 'cikis'
            ).scalar() or 0
            mevcut = giris - cikis
            if mevcut <= urun.min_stok:
                kritik_liste.append({
                    'ad': urun.urun_adi,
                    'miktar': round(mevcut, 2),
                    'birim': urun.birim,
                    'min_stok': urun.min_stok
                })
    except Exception as e:
        return jsonify({'ok': False, 'mesaj': f'Stok sorgusu hatası: {str(e)}'})

    if not kritik_liste:
        return jsonify({'ok': True, 'mesaj': 'Kritik stok yok, e-posta gönderilmedi.'})

    # E-posta gönder
    basari = EmailServis.kritik_stok_bildirimi_gonder(alici, kritik_liste)
    if basari:
        return jsonify({'ok': True, 'mesaj': f'{len(kritik_liste)} kritik ürün bilgisi {alici} adresine gönderildi.'})
    else:
        return jsonify({'ok': False, 'mesaj': 'E-posta gönderim hatası. SMTP ayarlarını kontrol edin.'})


@bildirim_bp.route('/api/bildirim-kontrol')
def bildirim_kontrol():
    """
    Sayfada otomatik çalışan kontrol endpoint'i.
    Bildirimleri sayıyla birlikte, ayrıca yeni kritik uyarı var mı bilgisiyle döner.
    Tarayıcı Notification API için kullanılır.
    """
    bildirimler = _tum_bildirimleri_topla()
    kritikler = [b for b in bildirimler if b.get('tip') == 'kritik']
    return jsonify({
        'sayi': len(bildirimler),
        'bildirimler': bildirimler[:10],
        'kritik_sayisi': len(kritikler),
        'uyari_mesaj': f'{len(kritikler)} ürün kritik stok seviyesinde!' if kritikler else None
    })
