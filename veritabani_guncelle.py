#!/usr/bin/env python3
"""
Veritabanı Güncelleme Aracı
============================
Mevcut veritabanına yeni tabloları ve kolonları ekler.
Mevcut verilere dokunmaz.

Kullanım: python veritabani_guncelle.py
"""
import sqlite3, os, sys

DIZIN = os.path.dirname(os.path.abspath(__file__))
DB_YOLU = os.path.join(DIZIN, 'database.db')


def guncelle():
    if not os.path.exists(DB_YOLU):
        print("Veritabanı bulunamadı — yeni oluşturulacak.")

    conn = sqlite3.connect(DB_YOLU)
    cur  = conn.cursor()
    cur.execute("PRAGMA foreign_keys = OFF")

    # Mevcut tabloları al
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    mevcut_tablolar = {r[0] for r in cur.fetchall()}

    hatalar  = []
    eklenen  = []

    # ── Tablo ekleme yardımcısı ───────────────────────────────────────────
    def tablo_ekle(ad, sql):
        if ad not in mevcut_tablolar:
            try:
                cur.execute(sql)
                eklenen.append(f"TABLO: {ad}")
                mevcut_tablolar.add(ad)
            except Exception as e:
                hatalar.append(f"{ad}: {e}")

    # ── Kolon ekleme yardımcısı ───────────────────────────────────────────
    def kolon_ekle(tablo, kolon, tanim):
        if tablo not in mevcut_tablolar:
            return
        cur.execute(f"PRAGMA table_info({tablo})")
        mevcutlar = {r[1] for r in cur.fetchall()}
        if kolon not in mevcutlar:
            try:
                cur.execute(f"ALTER TABLE {tablo} ADD COLUMN {kolon} {tanim}")
                eklenen.append(f"KOLON: {tablo}.{kolon}")
            except Exception as e:
                hatalar.append(f"{tablo}.{kolon}: {e}")

    # ════════════════════════════════════════════════════════════════════════
    # ÇEKİRDEK TABLOLAR
    # ════════════════════════════════════════════════════════════════════════

    tablo_ekle('kullanici', """CREATE TABLE kullanici (
        id INTEGER PRIMARY KEY AUTOINCREMENT, kullanici_adi VARCHAR(50) UNIQUE NOT NULL,
        sifre_hash VARCHAR(256), ad VARCHAR(50), soyad VARCHAR(50), email VARCHAR(100),
        telefon VARCHAR(20), aktif INTEGER DEFAULT 1, admin INTEGER DEFAULT 0,
        son_giris VARCHAR(30), olusturma_tarihi VARCHAR(20), tema VARCHAR(20) DEFAULT 'light')""")

    tablo_ekle('rol', """CREATE TABLE rol (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ad VARCHAR(50) UNIQUE NOT NULL,
        aciklama TEXT, aktif INTEGER DEFAULT 1)""")

    tablo_ekle('kullanici_rol', """CREATE TABLE kullanici_rol (
        id INTEGER PRIMARY KEY AUTOINCREMENT, kullanici_id INTEGER REFERENCES kullanici(id),
        rol_id INTEGER REFERENCES rol(id))""")

    tablo_ekle('sistem_ayar', """CREATE TABLE sistem_ayar (
        id INTEGER PRIMARY KEY AUTOINCREMENT, anahtar VARCHAR(100) UNIQUE NOT NULL,
        deger TEXT, grup VARCHAR(50), aciklama TEXT)""")

    tablo_ekle('audit_log', """CREATE TABLE audit_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, kullanici_id INTEGER REFERENCES kullanici(id),
        aksiyon VARCHAR(50), tablo VARCHAR(50), kayit_id INTEGER, eski_deger TEXT,
        yeni_deger TEXT, ip_adresi VARCHAR(50), olusturma_tarihi VARCHAR(30))""")

    tablo_ekle('bildirim', """CREATE TABLE bildirim (
        id INTEGER PRIMARY KEY AUTOINCREMENT, baslik VARCHAR(100) NOT NULL,
        mesaj TEXT NOT NULL, tur VARCHAR(30) DEFAULT 'genel', kayit_id INTEGER,
        okundu INTEGER DEFAULT 0, kullanici_id INTEGER REFERENCES kullanici(id),
        olusturma_tarihi VARCHAR(30))""")

    # ════════════════════════════════════════════════════════════════════════
    # STOK
    # ════════════════════════════════════════════════════════════════════════

    tablo_ekle('kategori', """CREATE TABLE kategori (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ad VARCHAR(100) NOT NULL, ust_id INTEGER)""")

    tablo_ekle('sube', """CREATE TABLE sube (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ad VARCHAR(100), adres TEXT, telefon VARCHAR(30),
        email VARCHAR(100), aktif INTEGER DEFAULT 1, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('depo', """CREATE TABLE depo (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ad VARCHAR(100) NOT NULL, sube_id INTEGER REFERENCES sube(id),
        aciklama TEXT, aktif INTEGER DEFAULT 1)""")

    tablo_ekle('urun', """CREATE TABLE urun (
        id INTEGER PRIMARY KEY AUTOINCREMENT, stok_kodu VARCHAR(50) UNIQUE NOT NULL,
        urun_adi VARCHAR(200) NOT NULL, kategori_id INTEGER REFERENCES kategori(id),
        birim VARCHAR(20) DEFAULT 'Adet', satis_fiyati FLOAT DEFAULT 0,
        alis_fiyati FLOAT DEFAULT 0, kdv_orani FLOAT DEFAULT 18,
        min_stok FLOAT DEFAULT 0, max_stok FLOAT DEFAULT 0,
        aciklama TEXT, aktif INTEGER DEFAULT 1, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('stok_hareket', """CREATE TABLE stok_hareket (
        id INTEGER PRIMARY KEY AUTOINCREMENT, urun_id INTEGER NOT NULL REFERENCES urun(id),
        hareket_tipi VARCHAR(10) NOT NULL, miktar FLOAT NOT NULL, depo_id INTEGER REFERENCES depo(id),
        referans_no VARCHAR(50), belge_tipi VARCHAR(30), aciklama TEXT,
        kullanici_id INTEGER REFERENCES kullanici(id), olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('stok_lokasyon', """CREATE TABLE stok_lokasyon (
        id INTEGER PRIMARY KEY AUTOINCREMENT, urun_id INTEGER REFERENCES urun(id),
        depo_id INTEGER REFERENCES depo(id), raf VARCHAR(20), miktar FLOAT DEFAULT 0)""")

    tablo_ekle('parti', """CREATE TABLE parti (
        id INTEGER PRIMARY KEY AUTOINCREMENT, urun_id INTEGER REFERENCES urun(id),
        parti_no VARCHAR(50), seri_no VARCHAR(50), skt VARCHAR(20),
        miktar FLOAT, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('sayim', """CREATE TABLE sayim (
        id INTEGER PRIMARY KEY AUTOINCREMENT, sayim_tarihi VARCHAR(20), durum VARCHAR(20) DEFAULT 'taslak',
        aciklama TEXT, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('sayim_duzeltme', """CREATE TABLE sayim_duzeltme (
        id INTEGER PRIMARY KEY AUTOINCREMENT, sayim_id INTEGER REFERENCES sayim(id),
        urun_id INTEGER REFERENCES urun(id), beklenen FLOAT, gercek FLOAT,
        fark FLOAT, onaylandi INTEGER DEFAULT 0, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('email_log', """CREATE TABLE email_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT, konu VARCHAR(200), alici VARCHAR(200),
        durum VARCHAR(20), olusturma_tarihi VARCHAR(30))""")

    # ════════════════════════════════════════════════════════════════════════
    # SATIN ALMA
    # ════════════════════════════════════════════════════════════════════════

    tablo_ekle('tedarikci', """CREATE TABLE tedarikci (
        id INTEGER PRIMARY KEY AUTOINCREMENT, tedarikci_kodu VARCHAR(50) UNIQUE,
        unvan VARCHAR(200) NOT NULL, vergi_no VARCHAR(50), vergi_dairesi VARCHAR(100),
        telefon VARCHAR(50), email VARCHAR(100), adres TEXT, sehir VARCHAR(50),
        ulke VARCHAR(50) DEFAULT 'Türkiye', web VARCHAR(100), notlar TEXT,
        aktif INTEGER DEFAULT 1, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('satin_alma_siparisi', """CREATE TABLE satin_alma_siparisi (
        id INTEGER PRIMARY KEY AUTOINCREMENT, siparis_no VARCHAR(50) UNIQUE NOT NULL,
        tedarikci_id INTEGER REFERENCES tedarikci(id), siparis_tarihi VARCHAR(20),
        teslim_tarihi VARCHAR(20), durum VARCHAR(20) DEFAULT 'taslak',
        toplam_tutar FLOAT DEFAULT 0, para_birimi VARCHAR(10) DEFAULT 'TL',
        notlar TEXT, aktif INTEGER DEFAULT 1, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('satin_alma_siparisi_satir', """CREATE TABLE satin_alma_siparisi_satir (
        id INTEGER PRIMARY KEY AUTOINCREMENT, siparis_id INTEGER REFERENCES satin_alma_siparisi(id),
        urun_id INTEGER REFERENCES urun(id), tanim VARCHAR(300), miktar FLOAT,
        birim VARCHAR(20), birim_fiyat FLOAT DEFAULT 0, kdv_orani FLOAT DEFAULT 18,
        teslim_tarihi VARCHAR(20), teslim_miktari FLOAT DEFAULT 0)""")

    # ════════════════════════════════════════════════════════════════════════
    # FATURA
    # ════════════════════════════════════════════════════════════════════════

    tablo_ekle('fatura', """CREATE TABLE fatura (
        id INTEGER PRIMARY KEY AUTOINCREMENT, fatura_no VARCHAR(50) UNIQUE NOT NULL,
        fatura_tipi VARCHAR(20) NOT NULL, fatura_tarihi VARCHAR(20), vade_tarihi VARCHAR(20),
        tedarikci_id INTEGER REFERENCES tedarikci(id), musteri_adi VARCHAR(200),
        musteri_vergi_no VARCHAR(50), musteri_adres TEXT,
        ara_toplam FLOAT DEFAULT 0, toplam_kdv FLOAT DEFAULT 0,
        toplam_indirim FLOAT DEFAULT 0, genel_toplam FLOAT DEFAULT 0,
        para_birimi VARCHAR(10) DEFAULT 'TL', siparis_id INTEGER REFERENCES satin_alma_siparisi(id),
        durum VARCHAR(20) DEFAULT 'taslak', odeme_tarihi VARCHAR(20), aciklama TEXT,
        aktif INTEGER DEFAULT 1, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('fatura_satir', """CREATE TABLE fatura_satir (
        id INTEGER PRIMARY KEY AUTOINCREMENT, fatura_id INTEGER REFERENCES fatura(id),
        urun_id INTEGER REFERENCES urun(id), tanim VARCHAR(300), miktar FLOAT,
        birim VARCHAR(20) DEFAULT 'adet', birim_fiyat FLOAT, indirim_orani FLOAT DEFAULT 0,
        kdv_orani FLOAT DEFAULT 18, proje_kodu VARCHAR(100))""")

    tablo_ekle('irsaliye', """CREATE TABLE irsaliye (
        id INTEGER PRIMARY KEY AUTOINCREMENT, irsaliye_no VARCHAR(50) UNIQUE NOT NULL,
        irsaliye_tipi VARCHAR(20) DEFAULT 'cikis', irsaliye_tarihi VARCHAR(20),
        tedarikci_id INTEGER REFERENCES tedarikci(id), musteri_adi VARCHAR(200),
        teslim_adresi TEXT, fatura_id INTEGER REFERENCES fatura(id),
        siparis_id INTEGER REFERENCES satin_alma_siparisi(id), arac_plaka VARCHAR(20),
        sofor VARCHAR(100), durum VARCHAR(20) DEFAULT 'hazirlaniyor', aciklama TEXT,
        aktif INTEGER DEFAULT 1, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('irsaliye_satir', """CREATE TABLE irsaliye_satir (
        id INTEGER PRIMARY KEY AUTOINCREMENT, irsaliye_id INTEGER REFERENCES irsaliye(id),
        urun_id INTEGER REFERENCES urun(id), tanim VARCHAR(300), miktar FLOAT,
        birim VARCHAR(20) DEFAULT 'adet', aciklama TEXT)""")

    # ════════════════════════════════════════════════════════════════════════
    # İK
    # ════════════════════════════════════════════════════════════════════════

    tablo_ekle('personel', """CREATE TABLE personel (
        id INTEGER PRIMARY KEY AUTOINCREMENT, sicil_no VARCHAR(20) UNIQUE,
        ad VARCHAR(50) NOT NULL, soyad VARCHAR(50) NOT NULL, tc_no VARCHAR(11),
        dogum_tarihi VARCHAR(20), cinsiyet VARCHAR(10), email VARCHAR(100),
        telefon VARCHAR(30), departman VARCHAR(50), pozisyon VARCHAR(100),
        ise_baslama VARCHAR(20), isten_cikis VARCHAR(20), maas FLOAT DEFAULT 0,
        iban VARCHAR(50), adres TEXT, kan_grubu VARCHAR(5), aktif INTEGER DEFAULT 1,
        olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('personel_ek_bilgi', """CREATE TABLE personel_ek_bilgi (
        id INTEGER PRIMARY KEY AUTOINCREMENT, personel_id INTEGER REFERENCES personel(id),
        egitim VARCHAR(100), universite VARCHAR(100), bolum VARCHAR(100),
        yabanci_dil VARCHAR(100), sertifikalar TEXT, acil_kisi VARCHAR(100),
        acil_telefon VARCHAR(30), ozel_not TEXT, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('izin', """CREATE TABLE izin (
        id INTEGER PRIMARY KEY AUTOINCREMENT, personel_id INTEGER REFERENCES personel(id),
        izin_turu VARCHAR(30), baslangic VARCHAR(20), bitis VARCHAR(20), gun_sayisi FLOAT,
        aciklama TEXT, durum VARCHAR(20) DEFAULT 'bekliyor', onaylayan_id INTEGER REFERENCES kullanici(id),
        onay_tarihi VARCHAR(20), olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('devamsizlik', """CREATE TABLE devamsizlik (
        id INTEGER PRIMARY KEY AUTOINCREMENT, personel_id INTEGER REFERENCES personel(id),
        tarih VARCHAR(20), neden VARCHAR(100), aciklama TEXT, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('maas', """CREATE TABLE maas (
        id INTEGER PRIMARY KEY AUTOINCREMENT, personel_id INTEGER REFERENCES personel(id),
        donem VARCHAR(20), brut FLOAT, net FLOAT, sgk_kesinti FLOAT DEFAULT 0,
        gelir_vergisi FLOAT DEFAULT 0, diger_kesinti FLOAT DEFAULT 0,
        odenme_tarihi VARCHAR(20), durum VARCHAR(20) DEFAULT 'bekliyor', notlar TEXT)""")

    tablo_ekle('tatil', """CREATE TABLE tatil (
        id INTEGER PRIMARY KEY AUTOINCREMENT, tarih VARCHAR(20), bitis_tarihi VARCHAR(20),
        ad VARCHAR(100), tur VARCHAR(20) DEFAULT 'resmi', tekrarlayan INTEGER DEFAULT 0,
        aciklama TEXT, aktif INTEGER DEFAULT 1, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('kkd_tanim', """CREATE TABLE kkd_tanim (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ad VARCHAR(100) NOT NULL, kod VARCHAR(30),
        periyot_gun INTEGER DEFAULT 365, aciklama TEXT, aktif INTEGER DEFAULT 1,
        olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('zimmet', """CREATE TABLE zimmet (
        id INTEGER PRIMARY KEY AUTOINCREMENT, personel_id INTEGER REFERENCES personel(id),
        malzeme VARCHAR(200), seri_no VARCHAR(100), verilis_tarihi VARCHAR(20),
        iade_tarihi VARCHAR(20), durum VARCHAR(20) DEFAULT 'aktif', notlar TEXT,
        olusturma_tarihi VARCHAR(20))""")

    # ════════════════════════════════════════════════════════════════════════
    # CRM
    # ════════════════════════════════════════════════════════════════════════

    tablo_ekle('musteri', """CREATE TABLE musteri (
        id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_kodu VARCHAR(50) UNIQUE,
        unvan VARCHAR(200) NOT NULL, musteri_tipi VARCHAR(20) DEFAULT 'kurumsal',
        vergi_no VARCHAR(50), vergi_dairesi VARCHAR(100), telefon VARCHAR(50),
        email VARCHAR(100), adres TEXT, sehir VARCHAR(50), ulke VARCHAR(50) DEFAULT 'Türkiye',
        web VARCHAR(100), notlar TEXT, aktif INTEGER DEFAULT 1, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('teklif', """CREATE TABLE teklif (
        id INTEGER PRIMARY KEY AUTOINCREMENT, teklif_no VARCHAR(50) UNIQUE NOT NULL,
        musteri_id INTEGER REFERENCES musteri(id), konu VARCHAR(200), tarih VARCHAR(20),
        gecerlilik VARCHAR(20), durum VARCHAR(20) DEFAULT 'taslak', toplam_tutar FLOAT DEFAULT 0,
        para_birimi VARCHAR(10) DEFAULT 'TL', notlar TEXT,
        hazirlayan_id INTEGER REFERENCES kullanici(id), aktif INTEGER DEFAULT 1,
        olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('teklif_satir', """CREATE TABLE teklif_satir (
        id INTEGER PRIMARY KEY AUTOINCREMENT, teklif_id INTEGER REFERENCES teklif(id),
        urun_id INTEGER REFERENCES urun(id), tanim VARCHAR(300), miktar FLOAT DEFAULT 1,
        birim VARCHAR(20) DEFAULT 'Adet', birim_fiyat FLOAT DEFAULT 0,
        indirim_orani FLOAT DEFAULT 0, kdv_orani FLOAT DEFAULT 18)""")

    tablo_ekle('musteri_takip', """CREATE TABLE musteri_takip (
        id INTEGER PRIMARY KEY AUTOINCREMENT, musteri_id INTEGER REFERENCES musteri(id),
        tur VARCHAR(20) DEFAULT 'not', baslik VARCHAR(200), aciklama TEXT, tarih VARCHAR(20),
        hatirlatma_tarihi VARCHAR(20), kullanici_id INTEGER REFERENCES kullanici(id),
        olusturma_tarihi VARCHAR(20))""")

    # ════════════════════════════════════════════════════════════════════════
    # ÜRETİM
    # ════════════════════════════════════════════════════════════════════════

    tablo_ekle('bom', """CREATE TABLE bom (
        id INTEGER PRIMARY KEY AUTOINCREMENT, urun_id INTEGER REFERENCES urun(id),
        revizyon VARCHAR(10) DEFAULT '1', aktif INTEGER DEFAULT 1,
        aciklama TEXT, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('bom_satir', """CREATE TABLE bom_satir (
        id INTEGER PRIMARY KEY AUTOINCREMENT, bom_id INTEGER REFERENCES bom(id),
        hammadde_id INTEGER REFERENCES urun(id), miktar FLOAT, birim VARCHAR(20),
        fire_orani FLOAT DEFAULT 0, aciklama TEXT)""")

    tablo_ekle('uretim_emri', """CREATE TABLE uretim_emri (
        id INTEGER PRIMARY KEY AUTOINCREMENT, emri_no VARCHAR(50) UNIQUE, urun_id INTEGER REFERENCES urun(id),
        bom_id INTEGER REFERENCES bom(id), miktar FLOAT, durum VARCHAR(20) DEFAULT 'planlandi',
        planlanan_baslangic VARCHAR(20), planlanan_bitis VARCHAR(20),
        gercek_baslangic VARCHAR(20), gercek_bitis VARCHAR(20), aciklama TEXT,
        aktif INTEGER DEFAULT 1, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('uretim_operasyonu', """CREATE TABLE uretim_operasyonu (
        id INTEGER PRIMARY KEY AUTOINCREMENT, emri_id INTEGER REFERENCES uretim_emri(id),
        operasyon_adi VARCHAR(100), sira INTEGER, sure_dakika INTEGER, tezgah_id INTEGER,
        personel_id INTEGER REFERENCES personel(id), baslangic VARCHAR(30), bitis VARCHAR(30),
        durum VARCHAR(20) DEFAULT 'bekliyor', aciklama TEXT, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('tezgah', """CREATE TABLE tezgah (
        id INTEGER PRIMARY KEY AUTOINCREMENT, tezgah_kodu VARCHAR(30) UNIQUE, ad VARCHAR(100) NOT NULL,
        marka VARCHAR(50), model VARCHAR(50), seri_no VARCHAR(50), departman VARCHAR(50),
        kapasite FLOAT, durum VARCHAR(20) DEFAULT 'aktif', garanti_bitis VARCHAR(20),
        sonraki_bakim VARCHAR(20), aciklama TEXT, aktif INTEGER DEFAULT 1, olusturma_tarihi VARCHAR(20))""")

    # ════════════════════════════════════════════════════════════════════════
    # PROJE
    # ════════════════════════════════════════════════════════════════════════

    tablo_ekle('proje', """CREATE TABLE proje (
        id INTEGER PRIMARY KEY AUTOINCREMENT, proje_no VARCHAR(50) UNIQUE NOT NULL,
        proje_adi VARCHAR(200) NOT NULL, aciklama TEXT,
        musteri_id INTEGER REFERENCES musteri(id), musteri_adi_serbest VARCHAR(200),
        teklif_id INTEGER REFERENCES teklif(id), asama VARCHAR(20) DEFAULT 'teklif',
        baslangic_tarihi VARCHAR(20), bitis_tarihi VARCHAR(20), gercek_bitis VARCHAR(20),
        planlanan_maliyet FLOAT DEFAULT 0, para_birimi VARCHAR(10) DEFAULT 'TL',
        sorumlu_id INTEGER REFERENCES kullanici(id), aktif INTEGER DEFAULT 1,
        olusturma_tarihi VARCHAR(20), guncellenme_tarihi VARCHAR(20))""")

    tablo_ekle('proje_gorev', """CREATE TABLE proje_gorev (
        id INTEGER PRIMARY KEY AUTOINCREMENT, proje_id INTEGER REFERENCES proje(id),
        baslik VARCHAR(200) NOT NULL, aciklama TEXT, departman VARCHAR(50),
        atanan_id INTEGER REFERENCES kullanici(id), son_tarih VARCHAR(20),
        durum VARCHAR(20) DEFAULT 'bekliyor', oncelik VARCHAR(10) DEFAULT 'normal',
        olusturma_tarihi VARCHAR(20), tamamlanma_tarihi VARCHAR(20))""")

    # ════════════════════════════════════════════════════════════════════════
    # SİPARİŞ AKIŞI
    # ════════════════════════════════════════════════════════════════════════

    tablo_ekle('satis_emri', """CREATE TABLE satis_emri (
        id INTEGER PRIMARY KEY AUTOINCREMENT, siparis_no VARCHAR(50) UNIQUE NOT NULL,
        musteri_id INTEGER REFERENCES musteri(id), musteri_adi_serbest VARCHAR(200),
        musteri_telefon VARCHAR(50), teslim_adresi TEXT, kaynak VARCHAR(20) DEFAULT 'telefon',
        teklif_id INTEGER REFERENCES teklif(id), proje_id INTEGER REFERENCES proje(id),
        siparis_tarihi VARCHAR(20), termin_tarihi VARCHAR(20),
        durum VARCHAR(20) DEFAULT 'alindi', toplam_tutar FLOAT DEFAULT 0,
        para_birimi VARCHAR(10) DEFAULT 'TL', onaylayan_id INTEGER REFERENCES kullanici(id),
        onay_tarihi VARCHAR(20), onay_notu TEXT, aciklama TEXT,
        aktif INTEGER DEFAULT 1, olusturan_id INTEGER REFERENCES kullanici(id),
        olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('satis_emri_satir', """CREATE TABLE satis_emri_satir (
        id INTEGER PRIMARY KEY AUTOINCREMENT, siparis_id INTEGER REFERENCES satis_emri(id),
        urun_id INTEGER REFERENCES urun(id), tanim VARCHAR(300), miktar FLOAT DEFAULT 1,
        birim VARCHAR(20) DEFAULT 'Adet', birim_fiyat FLOAT DEFAULT 0,
        indirim_orani FLOAT DEFAULT 0, kdv_orani FLOAT DEFAULT 18, proje_kodu VARCHAR(100),
        stok_mevcut FLOAT DEFAULT 0, uretim_gerekli INTEGER DEFAULT 0,
        satin_alma_gerekli INTEGER DEFAULT 0)""")

    # ════════════════════════════════════════════════════════════════════════
    # MUHASEBE
    # ════════════════════════════════════════════════════════════════════════

    tablo_ekle('muhasebe_kalem', """CREATE TABLE muhasebe_kalem (
        id INTEGER PRIMARY KEY AUTOINCREMENT, tur VARCHAR(10) NOT NULL, kategori VARCHAR(100),
        aciklama VARCHAR(300) NOT NULL, tutar FLOAT NOT NULL, para_birimi VARCHAR(10) DEFAULT 'TL',
        tarih VARCHAR(20) NOT NULL, kaynak VARCHAR(20), kaynak_id INTEGER,
        proje_id INTEGER REFERENCES proje(id), fatura_no VARCHAR(50),
        olusturan_id INTEGER REFERENCES kullanici(id), olusturma_tarihi VARCHAR(20))""")

    # ════════════════════════════════════════════════════════════════════════
    # BAKIM
    # ════════════════════════════════════════════════════════════════════════

    tablo_ekle('bakim_plan', """CREATE TABLE bakim_plan (
        id INTEGER PRIMARY KEY AUTOINCREMENT, tezgah_id INTEGER REFERENCES tezgah(id),
        bakim_turu VARCHAR(50), periyot_gun INTEGER, son_bakim VARCHAR(20),
        sonraki_bakim VARCHAR(20), aciklama TEXT, aktif INTEGER DEFAULT 1)""")

    tablo_ekle('bakim_kayit', """CREATE TABLE bakim_kayit (
        id INTEGER PRIMARY KEY AUTOINCREMENT, tezgah_id INTEGER REFERENCES tezgah(id),
        plan_id INTEGER REFERENCES bakim_plan(id), bakim_turu VARCHAR(50), tarih VARCHAR(20),
        sure_dakika INTEGER, maliyet FLOAT DEFAULT 0, yapan VARCHAR(100), personel_id INTEGER REFERENCES personel(id),
        aciklama TEXT, aktif INTEGER DEFAULT 1, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('ariza_kayit', """CREATE TABLE ariza_kayit (
        id INTEGER PRIMARY KEY AUTOINCREMENT, tezgah_id INTEGER REFERENCES tezgah(id),
        tarih VARCHAR(20), belirti VARCHAR(300), neden TEXT, cozum TEXT,
        sure_dakika INTEGER, maliyet FLOAT DEFAULT 0, teknisyen VARCHAR(100),
        personel_id INTEGER REFERENCES personel(id), durum VARCHAR(20) DEFAULT 'acik',
        aktif INTEGER DEFAULT 1, olusturma_tarihi VARCHAR(20))""")

    # ════════════════════════════════════════════════════════════════════════
    # KALİTE
    # ════════════════════════════════════════════════════════════════════════

    tablo_ekle('kalite_kontrol', """CREATE TABLE kalite_kontrol (
        id INTEGER PRIMARY KEY AUTOINCREMENT, kontrol_no VARCHAR(50), kontrol_tipi VARCHAR(20),
        urun_id INTEGER REFERENCES urun(id), parti_no VARCHAR(50), tarih VARCHAR(20),
        miktar FLOAT, kabul_miktari FLOAT, red_miktari FLOAT DEFAULT 0,
        durum VARCHAR(20) DEFAULT 'bekliyor', kontrol_eden_id INTEGER REFERENCES kullanici(id),
        aciklama TEXT, aktif INTEGER DEFAULT 1, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('kalite_hata', """CREATE TABLE kalite_hata (
        id INTEGER PRIMARY KEY AUTOINCREMENT, kontrol_id INTEGER REFERENCES kalite_kontrol(id),
        hata_tipi VARCHAR(100), miktar FLOAT DEFAULT 1, aciklama TEXT, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('kalite_sertifika', """CREATE TABLE kalite_sertifika (
        id INTEGER PRIMARY KEY AUTOINCREMENT, sertifika_adi VARCHAR(200) NOT NULL,
        sertifika_no VARCHAR(100), kurum VARCHAR(200), baslangic VARCHAR(20),
        bitis VARCHAR(20), dosya_yolu VARCHAR(500), aktif INTEGER DEFAULT 1, olusturma_tarihi VARCHAR(20))""")

    # ════════════════════════════════════════════════════════════════════════
    # VARDİYA
    # ════════════════════════════════════════════════════════════════════════

    tablo_ekle('vardiya_tanim', """CREATE TABLE vardiya_tanim (
        id INTEGER PRIMARY KEY AUTOINCREMENT, ad VARCHAR(100) NOT NULL,
        baslangic_saati VARCHAR(10), bitis_saati VARCHAR(10), sure_dakika INTEGER,
        renk VARCHAR(20), aktif INTEGER DEFAULT 1)""")

    tablo_ekle('vardiya_atama', """CREATE TABLE vardiya_atama (
        id INTEGER PRIMARY KEY AUTOINCREMENT, personel_id INTEGER REFERENCES personel(id),
        vardiya_id INTEGER REFERENCES vardiya_tanim(id), tarih VARCHAR(20),
        durum VARCHAR(20) DEFAULT 'planlandi', not_ TEXT, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('puantaj', """CREATE TABLE puantaj (
        id INTEGER PRIMARY KEY AUTOINCREMENT, personel_id INTEGER REFERENCES personel(id),
        tarih VARCHAR(20), giris_saati VARCHAR(10), cikis_saati VARCHAR(10),
        calisma_suresi FLOAT, fazla_mesai FLOAT DEFAULT 0,
        durum VARCHAR(20) DEFAULT 'normal', not_ TEXT, olusturma_tarihi VARCHAR(20))""")

    # ════════════════════════════════════════════════════════════════════════
    # ARAÇ
    # ════════════════════════════════════════════════════════════════════════

    tablo_ekle('arac', """CREATE TABLE arac (
        id INTEGER PRIMARY KEY AUTOINCREMENT, plaka VARCHAR(20) UNIQUE NOT NULL,
        marka VARCHAR(50), model VARCHAR(50), yil INTEGER, renk VARCHAR(30),
        arac_tipi VARCHAR(30), muayene_tarihi VARCHAR(20), sigorta_tarihi VARCHAR(20),
        kasko_tarihi VARCHAR(20), kilometre FLOAT DEFAULT 0,
        sorumlu_id INTEGER REFERENCES personel(id), aktif INTEGER DEFAULT 1, olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('arac_bakim', """CREATE TABLE arac_bakim (
        id INTEGER PRIMARY KEY AUTOINCREMENT, arac_id INTEGER REFERENCES arac(id),
        bakim_tipi VARCHAR(50), tarih VARCHAR(20), kilometre FLOAT,
        aciklama TEXT, maliyet FLOAT DEFAULT 0, yapan VARCHAR(100), olusturma_tarihi VARCHAR(20))""")

    tablo_ekle('yakit_kayit', """CREATE TABLE yakit_kayit (
        id INTEGER PRIMARY KEY AUTOINCREMENT, arac_id INTEGER REFERENCES arac(id),
        tarih VARCHAR(20), miktar FLOAT, tutar FLOAT DEFAULT 0,
        kilometre FLOAT, pompa VARCHAR(50), olusturma_tarihi VARCHAR(20))""")

    # ════════════════════════════════════════════════════════════════════════
    # DOKÜMAN
    # ════════════════════════════════════════════════════════════════════════

    tablo_ekle('dokuman', """CREATE TABLE dokuman (
        id INTEGER PRIMARY KEY AUTOINCREMENT, baslik VARCHAR(200) NOT NULL,
        kategori VARCHAR(50), dosya_adi VARCHAR(200), dosya_yolu VARCHAR(500),
        aciklama TEXT, yukleyen_id INTEGER REFERENCES kullanici(id),
        gecerlilik_tarihi VARCHAR(20), aktif INTEGER DEFAULT 1, olusturma_tarihi VARCHAR(20))""")

    # ════════════════════════════════════════════════════════════════════════
    # EK KOLONLAR (mevcut tablolara ekleme)
    # ════════════════════════════════════════════════════════════════════════

    kolon_ekle('fatura_satir', 'proje_kodu', 'VARCHAR(100)')
    kolon_ekle('urun', 'satis_fiyati', 'FLOAT DEFAULT 0')
    kolon_ekle('personel', 'aktif', 'INTEGER DEFAULT 1')

    # ════════════════════════════════════════════════════════════════════════
    conn.commit()
    conn.close()

    print(f"\n{'='*50}")
    print(f"VERİTABANI GÜNCELLEMESİ TAMAMLANDI")
    print(f"{'='*50}")
    if eklenen:
        print(f"\nEklenenler ({len(eklenen)}):")
        for e in eklenen:
            print(f"  ✓ {e}")
    else:
        print("\n✓ Veritabanı güncel, değişiklik yapılmadı.")

    if hatalar:
        print(f"\nUyarılar ({len(hatalar)}):")
        for h in hatalar:
            print(f"  ⚠ {h}")

    print(f"\nVeritabanı: {DB_YOLU}")


if __name__ == '__main__':
    guncelle()
