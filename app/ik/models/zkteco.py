"""
ZKTeco TRFace 200 Entegrasyon Modülü
-------------------------------------
pyzk kütüphanesi üzerinden ZKTeco cihazına bağlanır,
giriş/çıkış loglarını çeker ve ERP devamsızlık sistemine aktarır.

Kurulum: pip install pyzk
"""
import socket
from datetime import datetime, timedelta


# ─── Bağlantı Yardımcısı ─────────────────────────────────────────────────────

def zk_baglanti_ac(ip=None, port=None, timeout=None):
    """
    ZKTeco cihazına bağlan, ZK nesnesi döndür.
    Hata durumunda None döndürür (uygulama çökmez).
    """
    try:
        from zk import ZK
    except ImportError:
        raise ImportError("pyzk kurulu değil. Çalıştırın: pip install pyzk")

    from app.stok.models.sistem_ayar import SistemAyar
    _ip = ip or SistemAyar.get('zk_ip', '192.168.1.192')
    _port = int(port or SistemAyar.get('zk_port', '4370'))
    _timeout = int(timeout or SistemAyar.get('zk_timeout', '10'))

    zk = ZK(_ip, port=_port, timeout=_timeout, password=0, force_udp=False, ommit_ping=False)
    return zk


def zk_baglanabilir_mi(ip=None, port=None):
    """Cihaza ping atmadan TCP bağlantı kontrolü yap"""
    from app.stok.models.sistem_ayar import SistemAyar
    _ip = ip or SistemAyar.get('zk_ip', '192.168.1.192')
    _port = int(port or SistemAyar.get('zk_port', '4370'))
    try:
        s = socket.create_connection((_ip, _port), timeout=3)
        s.close()
        return True
    except Exception:
        return False


# ─── Senkronizasyon ──────────────────────────────────────────────────────────

def senkronize_et(baslangic_tarihi=None):
    """
    Cihazdan tüm giriş/çıkış loglarını çek, ERP'ye kaydet.
    baslangic_tarihi: datetime — sadece bu tarihten sonrakileri al (None = son 7 gün)
    Döndürür: {'basarili': True/False, 'islenen': int, 'yeni': int, 'hatalar': [str]}
    """
    from app import db
    from app.ik.models.personel import Personel, Devamsizlik
    from app.stok.models.sistem_ayar import SistemAyar

    sonuc = {'basarili': False, 'islenen': 0, 'yeni': 0, 'hatalar': [], 'kayitlar': []}

    if SistemAyar.get('zk_aktif', '1') != '1':
        sonuc['hatalar'].append('ZKTeco entegrasyonu pasif (Ayarlar > ZKTeco)')
        return sonuc

    if baslangic_tarihi is None:
        baslangic_tarihi = datetime.now() - timedelta(days=7)

    try:
        zk = zk_baglanti_ac()
        conn = zk.connect()
        conn.disable_device()  # işlem sırasında yeni kayıt alınmasın

        try:
            attendance = conn.get_attendance()
        finally:
            conn.enable_device()
            conn.disconnect()

    except ImportError as e:
        sonuc['hatalar'].append(str(e))
        return sonuc
    except Exception as e:
        sonuc['hatalar'].append(f'Cihaz bağlantı hatası: {str(e)}')
        return sonuc

    # Cihaz kullanıcı ID → Personel eşleştir (sicil_no kullanılır)
    # ZKTeco'da user_id = sicil numarası olarak programlanmalı
    baslangic_str = baslangic_tarihi.strftime('%d.%m.%Y')
    islem_tarihleri = {}  # personel_id → {tarih: [saatler]}

    for kayit in attendance:
        sonuc['islenen'] += 1
        try:
            zk_user_id = str(kayit.user_id).strip()
            zaman = kayit.timestamp  # datetime nesnesi

            if zaman < baslangic_tarihi:
                continue

            tarih_str = zaman.strftime('%d.%m.%Y')
            saat_str = zaman.strftime('%H:%M')

            # Sicil no ile personel bul
            personel = Personel.query.filter_by(sicil_no=zk_user_id, aktif=1).first()
            if not personel:
                sonuc['hatalar'].append(f'Personel bulunamadı: ZK ID={zk_user_id}')
                continue

            if personel.id not in islem_tarihleri:
                islem_tarihleri[personel.id] = {}
            if tarih_str not in islem_tarihleri[personel.id]:
                islem_tarihleri[personel.id][tarih_str] = []
            islem_tarihleri[personel.id][tarih_str].append(saat_str)

        except Exception as e:
            sonuc['hatalar'].append(f'Kayıt işleme hatası: {str(e)[:60]}')

    # Devamsızlık analizi
    if SistemAyar.get('zk_otomatik_devamsizlik', '1') == '1':
        calisma_bas = SistemAyar.get('zk_calisma_baslangic', '08:00')
        tolerans = int(SistemAyar.get('zk_gec_kalma_tolerans', '15'))
        toleransli_bas = _saat_ekle(calisma_bas, tolerans)

        for personel_id, gunler in islem_tarihleri.items():
            for tarih_str, saatler in gunler.items():
                saatler_sorted = sorted(saatler)
                ilk_giris = saatler_sorted[0]
                sonuc['kayitlar'].append({
                    'personel_id': personel_id,
                    'tarih': tarih_str,
                    'giris': ilk_giris,
                    'cikis': saatler_sorted[-1] if len(saatler_sorted) > 1 else None,
                    'isaret_sayisi': len(saatler_sorted),
                })

                # Geç kalma kontrolü
                if ilk_giris > toleransli_bas:
                    # Zaten kayıtlı mı?
                    mevcut = Devamsizlik.query.filter_by(
                        personel_id=personel_id, tarih=tarih_str, tur='gec_geldi'
                    ).first()
                    if not mevcut:
                        fark_dk = _saat_farki_dakika(calisma_bas, ilk_giris)
                        d = Devamsizlik(
                            personel_id=personel_id,
                            tarih=tarih_str,
                            tur='gec_geldi',
                            sure_dakika=fark_dk,
                            aciklama=f'ZKTeco otomatik — Giriş: {ilk_giris} (Beklenen: {calisma_bas})',
                        )
                        db.session.add(d)
                        sonuc['yeni'] += 1

        db.session.commit()

    # Son senkron tarihini güncelle
    SistemAyar.set('zk_son_senkron', datetime.now().strftime('%d.%m.%Y %H:%M'))

    sonuc['basarili'] = True
    return sonuc


def cihaz_bilgisi_al():
    """Cihaz firmware, seri no, kullanıcı sayısı bilgilerini al"""
    try:
        zk = zk_baglanti_ac()
        conn = zk.connect()
        try:
            bilgi = {
                'firmware': conn.get_firmware_version(),
                'seri_no': conn.get_serialnumber(),
                'platform': conn.get_platform(),
                'kullanici_sayisi': len(conn.get_users()),
                'log_sayisi': len(conn.get_attendance()),
                'bagli': True,
            }
        finally:
            conn.disconnect()
        return bilgi
    except Exception as e:
        return {'bagli': False, 'hata': str(e)}


def cihaz_kullanicilari_al():
    """Cihazdaki kullanıcı listesini al"""
    try:
        zk = zk_baglanti_ac()
        conn = zk.connect()
        try:
            users = conn.get_users()
            return [{'uid': u.uid, 'user_id': u.user_id, 'name': u.name,
                     'privilege': u.privilege} for u in users]
        finally:
            conn.disconnect()
    except Exception as e:
        return []


def personel_cihaza_yukle(personel):
    """
    Bir personeli ZKTeco cihazına yükle.
    user_id = sicil_no olarak ayarlanır.
    """
    try:
        from zk import ZK
        from zk.user import User
        zk = zk_baglanti_ac()
        conn = zk.connect()
        try:
            conn.set_user(
                uid=personel.id,
                name=f'{personel.ad} {personel.soyad}'[:24],
                privilege=0,
                user_id=str(personel.sicil_no),
            )
            return True, 'Başarıyla yüklendi'
        finally:
            conn.disconnect()
    except Exception as e:
        return False, str(e)


def cihaz_saatini_ayarla():
    """Cihaz saatini sunucu saatiyle senkronize et"""
    try:
        zk = zk_baglanti_ac()
        conn = zk.connect()
        try:
            conn.set_time(datetime.now())
            return True, 'Saat ayarlandı'
        finally:
            conn.disconnect()
    except Exception as e:
        return False, str(e)


# ─── Yardımcı Fonksiyonlar ────────────────────────────────────────────────────

def _saat_ekle(saat_str, dakika):
    """'08:00' + 15 dakika → '08:15'"""
    try:
        h, m = map(int, saat_str.split(':'))
        total = h * 60 + m + dakika
        return f'{total // 60:02d}:{total % 60:02d}'
    except Exception:
        return saat_str


def _saat_farki_dakika(erken_str, gec_str):
    """İki saat string arasındaki farkı dakika olarak hesapla"""
    try:
        h1, m1 = map(int, erken_str.split(':'))
        h2, m2 = map(int, gec_str.split(':'))
        return max(0, (h2 * 60 + m2) - (h1 * 60 + m1))
    except Exception:
        return 0
