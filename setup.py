#!/usr/bin/env python3
"""
ERP Kurulum Sihirbazı
=====================
Modüller seçilir, moduller.json güncellenir, veritabanı oluşturulur.

Kullanım:
  python setup.py           → Etkileşimli kurulum
  python setup.py --profil kucuk_firma
  python setup.py --tum     → Tüm modüller
"""
import json
import os
import sys
import sqlite3
import argparse
from datetime import datetime

DIZIN = os.path.dirname(os.path.abspath(__file__))
MODUL_DOSYA = os.path.join(DIZIN, 'moduller.json')
PROFIL_DIZIN = os.path.join(DIZIN, 'kurulum_profilleri')

MODUL_GRUPLARI = {
    'ÇEKİRDEK (Zorunlu)': [
        ('stok',      'Stok Yönetimi',       'Ürün, depo, hareket, sayım'),
        ('kullanici', 'Kullanıcı & Yetki',   'Giriş, roller, yetkiler'),
    ],
    'KATMAN 1 — Temel İşlemler': [
        ('satin_alma', 'Satın Alma',          'Tedarikçi, sipariş, teklif'),
        ('fatura',     'Fatura & İrsaliye',   'Alış/satış faturası'),
        ('ik',         'İK & Personel',       'Personel, izin, maaş'),
        ('crm',        'CRM & Satış',         'Müşteri, teklif, takip'),
    ],
    'KATMAN 2 — Operasyonel': [
        ('uretim',   'Üretim & MRP',          'BoM, iş emri, tezgah'),
        ('proje',    'Proje Yönetimi',         'Proje, görev, bütçe'),
        ('siparis',  'Sipariş Akışı',          'Satış siparişi, onay, görev'),
        ('muhasebe', 'Muhasebe',               'Gelir/gider, fatura entegrasyonu'),
        ('bakim',    'Bakım & Onarım',         'Makine bakım, arıza kaydı'),
        ('kalite',   'Kalite Kontrol',         'Giriş/süreç/final kalite'),
    ],
    'KATMAN 3 — İlave Modüller': [
        ('vardiya',  'Vardiya & Puantaj',      'Vardiya planı, devam takibi'),
        ('arac',     'Araç & Ekipman',         'Araç takibi, bakım, yakıt'),
        ('dokuman',  'Doküman Yönetimi',       'Belge arşivi, geçerlilik'),
    ],
}

HAZIR_PROFILLER = {
    'kucuk_firma': {
        'ad': 'Küçük Firma',
        'moduller': ['stok', 'kullanici', 'satin_alma', 'fatura', 'crm']
    },
    'orta_firma': {
        'ad': 'Orta Ölçekli Firma',
        'moduller': ['stok', 'kullanici', 'satin_alma', 'fatura', 'ik', 'crm',
                     'uretim', 'muhasebe', 'proje', 'siparis']
    },
    'tam_kurulum': {
        'ad': 'Tam Kurulum',
        'moduller': list(m for g in MODUL_GRUPLARI.values() for m, _, _ in g)
    },
}


def renk(metin, kod):
    return f"\033[{kod}m{metin}\033[0m"


def baslik(metin):
    print("\n" + "="*60)
    print(renk(f"  {metin}", "1;36"))
    print("="*60)


def moduller_kaydet(secilen):
    try:
        with open(MODUL_DOSYA, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception:
        data = {'_aciklama': 'ERP Modül Yönetimi', 'moduller': {}}

    if 'moduller' not in data:
        data['moduller'] = {}

    tum_moduller = [m for g in MODUL_GRUPLARI.values() for m, _, _ in g]
    for modul in tum_moduller:
        aktif = modul in secilen
        if modul in data['moduller'] and isinstance(data['moduller'][modul], dict):
            data['moduller'][modul]['aktif'] = aktif
        else:
            data['moduller'][modul] = {'aktif': aktif}

    with open(MODUL_DOSYA, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return True


def veritabani_kontrol():
    """Gerekli tabloları oluştur/güncelle"""
    db_yolu = os.path.join(DIZIN, 'database.db')
    sys.path.insert(0, DIZIN)
    try:
        from app import create_app, db
        app = create_app()
        with app.app_context():
            db.create_all()
        print(renk("  ✓ Veritabanı güncellendi", "32"))
    except Exception as e:
        print(renk(f"  ⚠ Veritabanı: {e}", "33"))
        print("  → Lütfen 'python veritabani_guncelle.py' komutunu çalıştırın")


def etkilesimli_kurulum():
    baslik("ERP SİSTEM KURULUM SİHİRBAZI")
    print(f"  Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print(f"  Dizin: {DIZIN}\n")

    # Hazır profil seçimi
    print("Hazır profil kullanmak ister misiniz?")
    for i, (key, profil) in enumerate(HAZIR_PROFILLER.items(), 1):
        modul_sayisi = len(profil['moduller'])
        print(f"  [{i}] {profil['ad']:25} ({modul_sayisi} modül)")
    print(f"  [4] Manuel seçim")
    print(f"  [5] Tüm modüller")

    secim = input("\nSeçiminiz (1-5): ").strip()

    if secim in ('1', '2', '3'):
        profil_key = list(HAZIR_PROFILLER.keys())[int(secim) - 1]
        secilen = set(HAZIR_PROFILLER[profil_key]['moduller'])
        print(renk(f"\n✓ {HAZIR_PROFILLER[profil_key]['ad']} profili seçildi", "32"))
    elif secim == '5':
        secilen = set(m for g in MODUL_GRUPLARI.values() for m, _, _ in g)
        print(renk("\n✓ Tüm modüller seçildi", "32"))
    else:
        # Manuel seçim
        secilen = set(['stok', 'kullanici'])  # Zorunlular
        print("\nModülleri seçin (ENTER=Evet, n=Hayır):\n")

        for grup_adi, moduller in MODUL_GRUPLARI.items():
            print(renk(f"\n{grup_adi}", "1;33"))
            for modul_key, modul_adi, aciklama in moduller:
                if modul_key in ('stok', 'kullanici'):
                    print(f"  [✓] {modul_adi:25} {aciklama}  (zorunlu)")
                    continue
                cevap = input(f"  {modul_adi:25} {aciklama} ? ").strip().lower()
                if cevap != 'n':
                    secilen.add(modul_key)

    # Özet
    baslik("KURULUM ÖZETİ")
    print(f"  Seçilen modüller ({len(secilen)} adet):\n")
    for grup_adi, moduller in MODUL_GRUPLARI.items():
        grup_secilen = [m for m, _, _ in moduller if m in secilen]
        if grup_secilen:
            print(f"  {grup_adi}:")
            for m in grup_secilen:
                modul_adi = next(a for k, a, _ in moduller if k == m)
                print(f"    ✓ {modul_adi}")

    onay = input(renk("\nBu yapılandırmayla devam edilsin mi? (ENTER=Evet): ", "1")).strip().lower()
    if onay == 'n':
        print("Kurulum iptal edildi.")
        return

    # Kaydet
    moduller_kaydet(secilen)
    print(renk("\n✓ moduller.json güncellendi", "32"))

    # Veritabanı
    print("\nVeritabanı kontrol ediliyor...")
    veritabani_kontrol()

    baslik("KURULUM TAMAMLANDI")
    print(f"  {len(secilen)} modül aktif.")
    print(f"\n  Sistemi başlatmak için:")
    print(renk("    python run.py", "1;32"))
    print(f"\n  veya Windows'ta:")
    print(renk("    baslat.bat\n", "1;32"))


def profil_ile_kur(profil_adi):
    if profil_adi in HAZIR_PROFILLER:
        profil = HAZIR_PROFILLER[profil_adi]
        secilen = set(profil['moduller'])
        moduller_kaydet(secilen)
        print(renk(f"✓ {profil['ad']} profili uygulandı ({len(secilen)} modül)", "32"))
    else:
        # Dosyadan profil yükle
        profil_yolu = os.path.join(PROFIL_DIZIN, f'{profil_adi}.json')
        if os.path.exists(profil_yolu):
            with open(profil_yolu) as f:
                data = json.load(f)
            secilen = set(data.get('moduller', {}).keys())
            moduller_kaydet(secilen)
            print(renk(f"✓ Profil uygulandı: {profil_yolu}", "32"))
        else:
            print(renk(f"✗ Profil bulunamadı: {profil_adi}", "31"))
            sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='ERP Kurulum Sihirbazı')
    parser.add_argument('--profil', help='Profil adı (kucuk_firma, orta_firma, tam_kurulum)')
    parser.add_argument('--tum', action='store_true', help='Tüm modülleri aktif et')
    parser.add_argument('--liste', action='store_true', help='Mevcut modül durumlarını göster')
    args = parser.parse_args()

    if args.liste:
        sys.path.insert(0, DIZIN)
        from app.modul_yonetici import modul_durumları
        durumlar = modul_durumları()
        baslik("MODÜL DURUMLARI")
        for modul, aktif in sorted(durumlar.items()):
            isaret = renk("✓", "32") if aktif else renk("✗", "31")
            print(f"  {isaret} {modul}")
    elif args.tum:
        secilen = set(m for g in MODUL_GRUPLARI.values() for m, _, _ in g)
        moduller_kaydet(secilen)
        print(renk(f"✓ Tüm modüller aktif edildi ({len(secilen)} adet)", "32"))
    elif args.profil:
        profil_ile_kur(args.profil)
    else:
        etkilesimli_kurulum()
