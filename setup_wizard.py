# -*- coding: utf-8 -*-
"""
ERP Kurulum Sihirbazı — Grafik Arayüz
======================================
PyInstaller ile setup.exe'ye dönüştürülür.
Hedef bilgisayarda Python kurulu olmak zorunda değil.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json, os, sys, subprocess, shutil, sqlite3, threading, time
from datetime import datetime

# ── Yol tespiti (hem .py hem .exe için) ──────────────────────────────────────
if getattr(sys, 'frozen', False):
    # PyInstaller exe içinden çalışıyor
    KAYNAK_DIZIN = sys._MEIPASS          # Geçici klasör (uygulama dosyaları)
    CALISMA_DIZIN = os.path.dirname(sys.executable)  # exe'nin bulunduğu yer
else:
    KAYNAK_DIZIN  = os.path.dirname(os.path.abspath(__file__))
    CALISMA_DIZIN = KAYNAK_DIZIN

MODUL_DOSYA  = os.path.join(CALISMA_DIZIN, 'moduller.json')
KURULUM_DIZIN_VARSAYILAN = r'C:\ERP'

# ── Modül tanımları ───────────────────────────────────────────────────────────
MODUL_GRUPLARI = [
    ('ÇEKİRDEK — Zorunlu', [
        ('stok',      'Stok Yönetimi',        'Ürün, depo, hareket, sayım, lot/seri takibi',         True,  True),
        ('kullanici', 'Kullanıcı & Yetki',    'Giriş, roller, yetkiler, işlem logları',               True,  True),
    ]),
    ('KATMAN 1 — Temel İşlemler', [
        ('satin_alma', 'Satın Alma',           'Tedarikçi, sipariş, teklif, çoklu döviz',              False, False),
        ('fatura',     'Fatura & İrsaliye',    'Alış/satış faturası, irsaliye',                        False, False),
        ('ik',         'İK & Personel',        'Personel, izin, maaş, devam takibi',                   False, False),
        ('crm',        'CRM & Satış',          'Müşteri, teklif, satış siparişi takibi',               False, False),
    ]),
    ('KATMAN 2 — Operasyonel', [
        ('uretim',   'Üretim & MRP',           'BoM, iş emri, operasyon, tezgah takibi',               False, False),
        ('proje',    'Proje Yönetimi',          'Proje, görev, bütçe takibi',                           False, False),
        ('siparis',  'Sipariş Akışı',           'Satış siparişi, yönetici onayı, görev dağıtımı',       False, False),
        ('muhasebe', 'Muhasebe',                'Gelir/gider takibi, fatura entegrasyonu',              False, False),
        ('bakim',    'Bakım & Onarım',          'Makine bakım planı, arıza kaydı',                      False, False),
        ('kalite',   'Kalite Kontrol',          'Giriş/süreç/final kalite, sertifika takibi',           False, False),
    ]),
    ('KATMAN 3 — İlave Modüller', [
        ('vardiya',  'Vardiya & Puantaj',       'Vardiya planı, günlük devam takibi, puantaj',          False, False),
        ('arac',     'Araç & Ekipman',          'Araç takibi, bakım, yakıt kayıtları',                  False, False),
        ('dokuman',  'Doküman Yönetimi',        'Belge arşivi, geçerlilik takibi',                      False, False),
    ]),
]

HAZIR_PROFILLER = {
    'Küçük Firma':          ['stok','kullanici','satin_alma','fatura','crm'],
    'Orta Ölçekli Firma':   ['stok','kullanici','satin_alma','fatura','ik','crm','uretim','muhasebe','proje','siparis'],
    'Üretim Firması':       ['stok','kullanici','satin_alma','fatura','ik','uretim','bakim','kalite','vardiya'],
    'Hizmet Firması':       ['stok','kullanici','fatura','ik','crm','proje','siparis','muhasebe'],
    'Tam Kurulum':          ['stok','kullanici','satin_alma','fatura','ik','crm','uretim','proje','siparis','muhasebe','bakim','kalite','vardiya','arac','dokuman'],
}


# ════════════════════════════════════════════════════════════════════════════════
class KurulumSihirbazi(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title('ERP MRP Yönetim Entegrasyon Sistemi — Kurulum Sihirbazı   ___by ®omanci,2026')
        self.geometry('820x640')
        self.resizable(False, False)
        self.configure(bg='#1e293b')

        # Değişkenler
        self.kurulum_dizin   = tk.StringVar(value=KURULUM_DIZIN_VARSAYILAN)
        self.modul_degiskenler = {}
        self.kurulum_turu    = tk.StringVar(value='yeni')  # yeni | guncelle
        self.aktif_sayfa     = tk.IntVar(value=0)

        self._stil_ayarla()
        self._sayfalari_olustur()
        self._sayfa_goster(0)

        # Ortala
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 820) // 2
        y = (self.winfo_screenheight() - 640) // 2
        self.geometry(f'820x640+{x}+{y}')

    # ── Stil ─────────────────────────────────────────────────────────────────

    def _stil_ayarla(self):
        self.stil = ttk.Style(self)
        self.stil.theme_use('clam')
        self.stil.configure('TNotebook',       background='#1e293b', borderwidth=0)
        self.stil.configure('TNotebook.Tab',   background='#334155', foreground='#94a3b8',
                            padding=[16,8], font=('Segoe UI',9))
        self.stil.map('TNotebook.Tab',
                      background=[('selected','#f59e0b')],
                      foreground=[('selected','#1e293b')])
        self.stil.configure('TProgressbar', troughcolor='#334155',
                            background='#f59e0b', thickness=8)
        self.stil.configure('TCheckbutton',
                            background='#1e293b', foreground='#e2e8f0',
                            font=('Segoe UI',9))
        self.stil.map('TCheckbutton', background=[('active','#1e293b')])

    # ── Sayfalar ─────────────────────────────────────────────────────────────

    def _sayfalari_olustur(self):
        self.sayfalar = []

        # Header
        header = tk.Frame(self, bg='#0f172a', height=70)
        header.pack(fill='x')
        header.pack_propagate(False)

        tk.Label(header, text='ERP MRP Yönetim Entegrasyon Sistemi  .V21  ___by ®omanci,2026',
                 bg='#0f172a', fg='#f59e0b',
                 font=('Segoe UI',16,'bold')).pack(side='left', padx=24, pady=16)
        tk.Label(header, text='Kurulum Sihirbazı',
                 bg='#0f172a', fg='#64748b',
                 font=('Segoe UI',10)).pack(side='left', pady=20)

        # İlerleme adım göstergesi
        self.adim_frame = tk.Frame(self, bg='#1e293b', height=40)
        self.adim_frame.pack(fill='x')
        self.adim_frame.pack_propagate(False)
        self._adim_gostergesi_olustur()

        # İçerik çerçevesi
        self.icerik_frame = tk.Frame(self, bg='#1e293b')
        self.icerik_frame.pack(fill='both', expand=True, padx=0, pady=0)

        # Sayfaları oluştur
        self.sayfalar = [
            self._sayfa_hosgeldiniz(),
            self._sayfa_kurulum_turu(),
            self._sayfa_dizin_secim(),
            self._sayfa_modul_secim(),
            self._sayfa_kurulum(),
        ]

        # Alt buton çubuğu
        buton_bar = tk.Frame(self, bg='#0f172a', height=56)
        buton_bar.pack(fill='x', side='bottom')
        buton_bar.pack_propagate(False)

        self.btn_geri  = tk.Button(buton_bar, text='← Geri',
                                   command=self._geri, **self._btn_stil('ghost'))
        self.btn_geri.pack(side='left', padx=16, pady=10)

        self.btn_iptal = tk.Button(buton_bar, text='İptal',
                                   command=self.destroy, **self._btn_stil('ghost'))
        self.btn_iptal.pack(side='left', pady=10)

        self.btn_ileri = tk.Button(buton_bar, text='İleri →',
                                   command=self._ileri, **self._btn_stil('primary'))
        self.btn_ileri.pack(side='right', padx=16, pady=10)

    def _btn_stil(self, tip):
        if tip == 'primary':
            return dict(bg='#f59e0b', fg='#1e293b', font=('Segoe UI',9,'bold'),
                       relief='flat', padx=20, pady=6, cursor='hand2',
                       activebackground='#d97706', activeforeground='#1e293b')
        return dict(bg='#334155', fg='#94a3b8', font=('Segoe UI',9),
                   relief='flat', padx=16, pady=6, cursor='hand2',
                   activebackground='#475569', activeforeground='#e2e8f0')

    def _adim_gostergesi_olustur(self):
        adimlar = ['Hoşgeldiniz', 'Kurulum Türü', 'Dizin', 'Modüller', 'Kurulum']
        for i, ad in enumerate(adimlar):
            f = tk.Frame(self.adim_frame, bg='#1e293b')
            f.pack(side='left', padx=8, pady=6)
            lbl = tk.Label(f, text=f'{i+1}. {ad}', bg='#1e293b',
                          fg='#64748b', font=('Segoe UI',8))
            lbl.pack()

    # ── Sayfa 0: Hoşgeldiniz ─────────────────────────────────────────────────

    def _sayfa_hosgeldiniz(self):
        f = tk.Frame(self.icerik_frame, bg='#1e293b')

        tk.Label(f, text='Hoşgeldiniz  ___by ®omanci,2026',
                 bg='#1e293b', fg='#f1f5f9',
                 font=('Segoe UI',20,'bold')).pack(pady=(40,8))

        tk.Label(f, text='ERP MRP Yönetim Entegrasyon Sistemi kurulum sihirbazına hoşgeldiniz.',
                 bg='#1e293b', fg='#94a3b8',
                 font=('Segoe UI',11)).pack()

        # Bilgi kutusu
        bilgi = tk.Frame(f, bg='#0f172a', padx=24, pady=20)
        bilgi.pack(padx=60, pady=30, fill='x')

        satırlar = [
            ('🏭', 'Modüler yapı',      'Sadece ihtiyacınız olan modülleri kurun'),
            ('🔄', 'Güncellenebilir',   'Verileriniz korunarak sistem güncellenir'),
            ('🌐', 'Ağ desteği',        'Tüm bilgisayarlardan erişim imkânı'),
            ('🔒', 'Yetki sistemi',     'Her kullanıcıya özel erişim hakları'),
        ]
        for emoji, baslik, aciklama in satırlar:
            satir = tk.Frame(bilgi, bg='#0f172a')
            satir.pack(fill='x', pady=4)
            tk.Label(satir, text=emoji, bg='#0f172a', font=('Segoe UI',14),
                    width=3).pack(side='left')
            tk.Label(satir, text=baslik, bg='#0f172a', fg='#f59e0b',
                    font=('Segoe UI',9,'bold'), width=16,
                    anchor='w').pack(side='left')
            tk.Label(satir, text=aciklama, bg='#0f172a', fg='#94a3b8',
                    font=('Segoe UI',9), anchor='w').pack(side='left')

        tk.Label(f, text=f'Versiyon: 21.0  |  {datetime.now().strftime("%d.%m.%Y")}  |    ___by ®omanci,2026',
                 bg='#1e293b', fg='#334155',
                 font=('Segoe UI',8)).pack(side='bottom', pady=12)
        return f

    # ── Sayfa 1: Kurulum Türü ─────────────────────────────────────────────────

    def _sayfa_kurulum_turu(self):
        f = tk.Frame(self.icerik_frame, bg='#1e293b')

        tk.Label(f, text='Kurulum Türü Seçin',
                 bg='#1e293b', fg='#f1f5f9',
                 font=('Segoe UI',16,'bold')).pack(pady=(40,24))

        secenekler = [
            ('yeni',     '🆕  Yeni Kurulum',
             'Bu bilgisayara ilk kez kurulacak.\nVeritabanı sıfırdan oluşturulur.'),
            ('guncelle', '🔄  Güncelleme',
             'Mevcut sistem üzerine güncelleme.\nVerileriniz korunur, yeni özellikler eklenir.'),
            ('modul',    '⚙️  Modül Ekle / Kaldır',
             'Mevcut kuruluma yeni modül ekleyin\nveya kullanılmayan modülleri kapatın.'),
        ]

        for deger, baslik, aciklama in secenekler:
            kart = tk.Frame(f, bg='#0f172a', padx=20, pady=16, cursor='hand2')
            kart.pack(padx=80, pady=6, fill='x')

            rb = tk.Radiobutton(kart, variable=self.kurulum_turu, value=deger,
                               bg='#0f172a', activebackground='#0f172a',
                               selectcolor='#f59e0b')
            rb.pack(side='left', padx=(0,12))

            ic = tk.Frame(kart, bg='#0f172a')
            ic.pack(side='left', fill='x', expand=True)
            tk.Label(ic, text=baslik, bg='#0f172a', fg='#f1f5f9',
                    font=('Segoe UI',10,'bold'), anchor='w').pack(fill='x')
            tk.Label(ic, text=aciklama, bg='#0f172a', fg='#64748b',
                    font=('Segoe UI',8), anchor='w', justify='left').pack(fill='x')

            kart.bind('<Button-1>', lambda e, d=deger: self.kurulum_turu.set(d))
            for w in kart.winfo_children():
                w.bind('<Button-1>', lambda e, d=deger: self.kurulum_turu.set(d))

        return f

    # ── Sayfa 2: Dizin Seçimi ─────────────────────────────────────────────────

    def _sayfa_dizin_secim(self):
        f = tk.Frame(self.icerik_frame, bg='#1e293b')

        tk.Label(f, text='Kurulum Dizini',
                 bg='#1e293b', fg='#f1f5f9',
                 font=('Segoe UI',16,'bold')).pack(pady=(40,8))
        tk.Label(f, text='ERP MRP sisteminin kurulacağı klasörü seçin.',
                 bg='#1e293b', fg='#64748b',
                 font=('Segoe UI',10)).pack(pady=(0,24))

        # Dizin seçici
        dizin_frame = tk.Frame(f, bg='#1e293b')
        dizin_frame.pack(padx=60, fill='x')

        tk.Label(dizin_frame, text='Kurulum Dizini:',
                 bg='#1e293b', fg='#94a3b8',
                 font=('Segoe UI',9)).pack(anchor='w', pady=(0,4))

        secici_frame = tk.Frame(dizin_frame, bg='#1e293b')
        secici_frame.pack(fill='x')

        self.dizin_entry = tk.Entry(secici_frame, textvariable=self.kurulum_dizin,
                                    bg='#0f172a', fg='#f1f5f9',
                                    font=('Segoe UI',10), relief='flat',
                                    insertbackground='white')
        self.dizin_entry.pack(side='left', fill='x', expand=True,
                              ipady=8, padx=(0,8))

        tk.Button(secici_frame, text='Gözat...', command=self._dizin_sec,
                  **self._btn_stil('ghost')).pack(side='right')

        # Bilgi
        bilgi_frame = tk.Frame(f, bg='#0f172a', padx=16, pady=12)
        bilgi_frame.pack(padx=60, pady=20, fill='x')

        tk.Label(bilgi_frame,
                 text='💡  Önerilen dizin: C:\\ERP\\errpr_rvr2r1r\n'
                      '     Boşluk veya Türkçe karakter içermeyen bir yol seçin.',
                 bg='#0f172a', fg='#94a3b8',
                 font=('Segoe UI',9), justify='left').pack(anchor='w')

        # Disk alanı
        self.disk_lbl = tk.Label(f, text='', bg='#1e293b', fg='#64748b',
                                 font=('Segoe UI',8))
        self.disk_lbl.pack()
        self._disk_kontrol()

        return f

    def _dizin_sec(self):
        dizin = filedialog.askdirectory(title='Kurulum Dizini Seçin')
        if dizin:
            self.kurulum_dizin.set(dizin.replace('/', '\\'))
            self._disk_kontrol()

    def _disk_kontrol(self):
        try:
            dizin = self.kurulum_dizin.get()
            surucu = dizin[:3] if len(dizin) >= 3 else dizin
            toplam, kullanilan, bos = shutil.disk_usage(surucu)
            self.disk_lbl.config(
                text=f'Disk: {bos//(1024**3)} GB boş  |  Gerekli: ~100 MB')
        except Exception:
            pass

    # ── Sayfa 3: Modül Seçimi ─────────────────────────────────────────────────

    def _sayfa_modul_secim(self):
        f = tk.Frame(self.icerik_frame, bg='#1e293b')

        baslik_frame = tk.Frame(f, bg='#1e293b')
        baslik_frame.pack(fill='x', padx=20, pady=(20,0))

        tk.Label(baslik_frame, text='Modülleri Seçin',
                 bg='#1e293b', fg='#f1f5f9',
                 font=('Segoe UI',14,'bold')).pack(side='left')

        # Hazır profiller
        profil_frame = tk.Frame(baslik_frame, bg='#1e293b')
        profil_frame.pack(side='right')
        tk.Label(profil_frame, text='Hazır profil:',
                 bg='#1e293b', fg='#64748b',
                 font=('Segoe UI',8)).pack(side='left', padx=(0,6))
        self.profil_combo = ttk.Combobox(profil_frame,
                                          values=list(HAZIR_PROFILLER.keys()),
                                          state='readonly', width=20,
                                          font=('Segoe UI',8))
        self.profil_combo.pack(side='left')
        self.profil_combo.bind('<<ComboboxSelected>>', self._profil_uygula)

        # Kaydırılabilir alan
        canvas = tk.Canvas(f, bg='#1e293b', highlightthickness=0)
        scrollbar = ttk.Scrollbar(f, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side='right', fill='y', padx=(0,4))
        canvas.pack(fill='both', expand=True, padx=(20,0), pady=8)

        ic_frame = tk.Frame(canvas, bg='#1e293b')
        canvas.create_window((0,0), window=ic_frame, anchor='nw')
        ic_frame.bind('<Configure>',
                      lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
        canvas.bind('<MouseWheel>',
                    lambda e: canvas.yview_scroll(-1*(e.delta//120), 'units'))

        # Modülleri oluştur
        for grup_adi, moduller in MODUL_GRUPLARI:
            tk.Label(ic_frame, text=grup_adi,
                     bg='#1e293b', fg='#f59e0b',
                     font=('Segoe UI',8,'bold')).pack(anchor='w', pady=(12,4))

            for key, ad, aciklama, varsayilan, zorunlu in moduller:
                var = tk.BooleanVar(value=varsayilan or zorunlu)
                self.modul_degiskenler[key] = var

                satir = tk.Frame(ic_frame, bg='#0f172a', pady=8, padx=12)
                satir.pack(fill='x', pady=2, padx=4)

                cb = ttk.Checkbutton(satir, variable=var,
                                     state='disabled' if zorunlu else 'normal')
                cb.pack(side='left', padx=(0,8))

                ic = tk.Frame(satir, bg='#0f172a')
                ic.pack(side='left', fill='x', expand=True)

                baslik_satir = tk.Frame(ic, bg='#0f172a')
                baslik_satir.pack(fill='x')
                tk.Label(baslik_satir, text=ad,
                         bg='#0f172a', fg='#f1f5f9',
                         font=('Segoe UI',9,'bold')).pack(side='left')
                if zorunlu:
                    tk.Label(baslik_satir, text='  [Zorunlu]',
                             bg='#0f172a', fg='#f59e0b',
                             font=('Segoe UI',8)).pack(side='left')

                tk.Label(ic, text=aciklama,
                         bg='#0f172a', fg='#64748b',
                         font=('Segoe UI',8)).pack(anchor='w')

        return f

    def _profil_uygula(self, event=None):
        profil_adi = self.profil_combo.get()
        if profil_adi not in HAZIR_PROFILLER:
            return
        secilen = HAZIR_PROFILLER[profil_adi]
        for key, var in self.modul_degiskenler.items():
            var.set(key in secilen)

    # ── Sayfa 4: Kurulum ──────────────────────────────────────────────────────

    def _sayfa_kurulum(self):
        f = tk.Frame(self.icerik_frame, bg='#1e293b')

        tk.Label(f, text='Kurulum',
                 bg='#1e293b', fg='#f1f5f9',
                 font=('Segoe UI',16,'bold')).pack(pady=(40,8))

        self.ozet_lbl = tk.Label(f, text='',
                                  bg='#1e293b', fg='#94a3b8',
                                  font=('Segoe UI',9), justify='left')
        self.ozet_lbl.pack(pady=(0,20))

        # İlerleme çubuğu
        self.progress = ttk.Progressbar(f, length=500, mode='determinate')
        self.progress.pack(pady=(0,8))

        self.progress_lbl = tk.Label(f, text='',
                                      bg='#1e293b', fg='#64748b',
                                      font=('Segoe UI',8))
        self.progress_lbl.pack()

        # Log
        log_frame = tk.Frame(f, bg='#0f172a')
        log_frame.pack(padx=40, pady=12, fill='both', expand=True)

        self.log_text = tk.Text(log_frame, bg='#0f172a', fg='#94a3b8',
                                 font=('Consolas',8), height=8,
                                 relief='flat', state='disabled')
        self.log_text.pack(fill='both', expand=True, padx=8, pady=8)
        self.log_text.tag_config('ok',    foreground='#22c55e')
        self.log_text.tag_config('hata',  foreground='#ef4444')
        self.log_text.tag_config('bilgi', foreground='#f59e0b')

        self.btn_baslat = tk.Button(f, text='▶  Kurulumu Başlat',
                                     command=self._kurulumu_baslat,
                                     **self._btn_stil('primary'))
        self.btn_baslat.pack(pady=8)

        return f

    def _ozet_goster(self):
        secilen = [k for k, v in self.modul_degiskenler.items() if v.get()]
        tur_metin = {
            'yeni':    'Yeni Kurulum',
            'guncelle':'Güncelleme',
            'modul':   'Modül Değişikliği'
        }.get(self.kurulum_turu.get(), '')
        self.ozet_lbl.config(
            text=f'Kurulum türü: {tur_metin}\n'
                 f'Dizin: {self.kurulum_dizin.get()}\n'
                 f'Seçilen modüller: {len(secilen)} adet  '
                 f'({", ".join(secilen)})')

    def _log(self, mesaj, tur='bilgi'):
        self.log_text.config(state='normal')
        self.log_text.insert('end', f'[{datetime.now().strftime("%H:%M:%S")}] {mesaj}\n', tur)
        self.log_text.see('end')
        self.log_text.config(state='disabled')
        self.update()

    def _progress_guncelle(self, deger, metin=''):
        self.progress['value'] = deger
        self.progress_lbl.config(text=metin)
        self.update()

    # ── Kurulum Mantığı ───────────────────────────────────────────────────────

    def _kurulumu_baslat(self):
        self.btn_baslat.config(state='disabled', text='Kuruluyor...')
        self.btn_ileri.config(state='disabled')
        threading.Thread(target=self._kurulum_thread, daemon=True).start()

    def _kurulum_thread(self):
        try:
            tur   = self.kurulum_turu.get()
            hedef = self.kurulum_dizin.get()

            # 1. Dizin oluştur
            self._progress_guncelle(5, 'Dizin oluşturuluyor...')
            self._log('Kurulum dizini hazırlanıyor...')
            os.makedirs(hedef, exist_ok=True)

            # 2. Dosyaları kopyala (yeni kurulumda)
            if tur == 'yeni':
                self._progress_guncelle(15, 'Dosyalar kopyalanıyor...')
                self._log('Uygulama dosyaları kopyalanıyor...')
                self._dosyalari_kopyala(hedef)
                self._log('Dosyalar kopyalandı', 'ok')

            elif tur == 'guncelle':
                self._progress_guncelle(15, 'Güncelleme dosyaları uygulanıyor...')
                self._log('Güncelleme uygulanıyor — veriler korunuyor...')
                db_yedek = os.path.join(hedef, 'database.db')
                if os.path.exists(db_yedek):
                    shutil.copy2(db_yedek, db_yedek + '.bak')
                    self._log('Veritabanı yedeklendi → database.db.bak', 'ok')
                self._dosyalari_kopyala(hedef)

            # 3. Modülleri kaydet
            self._progress_guncelle(50, 'Modüller yapılandırılıyor...')
            self._log('Modül seçimleri kaydediliyor...')
            self._modulleri_kaydet(hedef)
            self._log('Modüller yapılandırıldı', 'ok')

            # 4. Veritabanı
            self._progress_guncelle(70, 'Veritabanı hazırlanıyor...')
            self._log('Veritabanı oluşturuluyor/güncelleniyor...')
            self._veritabani_kur(hedef)
            self._log('Veritabanı hazır', 'ok')

            # 5. Python bağımlılıkları
            self._progress_guncelle(80, 'Python kütüphaneleri kuruluyor...')
            self._log('Kütüphaneler kuruluyor (requirements.txt)...')
            self._kutuphaneleri_kur(hedef)

            # 6. Masaüstü kısayolu
            self._progress_guncelle(92, 'Kısayol oluşturuluyor...')
            self._log('Masaüstü kısayolu oluşturuluyor...')
            self._kisayol_olustur(hedef)
            self._log('Kısayol oluşturuldu', 'ok')

            # 7. Tamamlandı
            self._progress_guncelle(100, 'Kurulum tamamlandı!')
            self._log('', '')
            self._log('✓ KURULUM TAMAMLANDI', 'ok')
            self._log(f'  Dizin: {hedef}', 'ok')
            self._log('  Başlatmak için masaüstündeki "ERP v21" kısayolunu kullanın.', 'ok')
            self._log(' Romancı iyi günler diler.                   ___by ®omanci,2026', 'ok')

            self.after(0, self._kurulum_tamam)

        except Exception as e:
            self._log(f'HATA: {e}', 'hata')
            self.after(0, lambda: self.btn_baslat.config(
                state='normal', text='▶  Tekrar Dene'))

    def _dosyalari_kopyala(self, hedef):
        """Kaynak dosyaları hedef dizine kopyala"""
        # .exe içinden çalışırken KAYNAK_DIZIN = _MEIPASS (geçici)
        # .py olarak çalışırken proje kökü
        kaynak = KAYNAK_DIZIN
        sayac = 0
        for root, dirs, files in os.walk(kaynak):
            # Gereksiz dizinleri atla
            dirs[:] = [d for d in dirs if d not in
                       ('__pycache__','.git','venv','dist','build',
                        'node_modules','.pytest_cache')]
            for dosya in files:
                if dosya.endswith('.pyc'):
                    continue
                kaynak_yol = os.path.join(root, dosya)
                goreli     = os.path.relpath(kaynak_yol, kaynak)
                hedef_yol  = os.path.join(hedef, goreli)
                os.makedirs(os.path.dirname(hedef_yol), exist_ok=True)
                # Veritabanını üzerine yazma (güncelleme modunda)
                if dosya == 'database.db' and os.path.exists(hedef_yol):
                    continue
                shutil.copy2(kaynak_yol, hedef_yol)
                sayac += 1
        self._log(f'  {sayac} dosya kopyalandı')

    def _modulleri_kaydet(self, hedef):
        modul_dosya = os.path.join(hedef, 'moduller.json')
        try:
            with open(modul_dosya, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except Exception:
            data = {'_aciklama': 'ERP Modül Yönetimi', 'moduller': {}}

        if 'moduller' not in data:
            data['moduller'] = {}

        for key, var in self.modul_degiskenler.items():
            aktif = var.get()
            if key in data['moduller'] and isinstance(data['moduller'][key], dict):
                data['moduller'][key]['aktif'] = aktif
            else:
                data['moduller'][key] = {'aktif': aktif}

        with open(modul_dosya, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        secilen = [k for k, v in self.modul_degiskenler.items() if v.get()]
        self._log(f'  Aktif modüller: {", ".join(secilen)}')

    def _veritabani_kur(self, hedef):
        vt_script = os.path.join(hedef, 'veritabani_guncelle.py')
        if os.path.exists(vt_script):
            try:
                result = subprocess.run(
                    [sys.executable, vt_script],
                    capture_output=True, text=True, cwd=hedef, timeout=60)
                if result.returncode == 0:
                    self._log('  Veritabanı tabloları hazır')
                else:
                    self._log(f'  Veritabanı uyarısı: {result.stderr[:200]}', 'hata')
            except Exception as e:
                self._log(f'  Veritabanı: {e}', 'hata')

    def _kutuphaneleri_kur(self, hedef):
        req = os.path.join(hedef, 'requirements.txt')
        if not os.path.exists(req):
            self._log('  requirements.txt bulunamadı, atlandı')
            return
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', req, '--quiet'],
                capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                self._log('  Kütüphaneler kuruldu', 'ok')
            else:
                self._log(f'  pip uyarısı: {result.stderr[:300]}', 'hata')
        except subprocess.TimeoutExpired:
            self._log('  Kütüphane kurulumu zaman aşımı — internet bağlantısı yok olabilir', 'hata')
        except Exception as e:
            self._log(f'  Kütüphane hatası: {e}', 'hata')

    def _kisayol_olustur(self, hedef):
        """Windows masaüstüne kısayol oluştur"""
        try:
            import winreg
            masaustu = os.path.join(os.path.expanduser('~'), 'Desktop')

            bat_icerik = f'@echo off\ncd /d "{hedef}"\npython basla.py\npause\n'
            bat_yol = os.path.join(hedef, 'ERP_v21_baslat.bat')
            with open(bat_yol, 'w', encoding='utf-8') as f:
                f.write(bat_icerik)

            kisayol_yol = os.path.join(masaustu, 'ERP v21.lnk')
            try:
                import win32com.client
                shell = win32com.client.Dispatch('WScript.Shell')
                kisayol = shell.CreateShortCut(kisayol_yol)
                kisayol.Targetpath = bat_yol
                kisayol.WorkingDirectory = hedef
                kisayol.IconLocation = bat_yol
                kisayol.save()
                self._log('  Masaüstü kısayolu oluşturuldu', 'ok')
            except Exception:
                # win32com yoksa .bat dosyasını masaüstüne kopyala
                shutil.copy2(bat_yol, os.path.join(masaustu, 'ERP v21.bat'))
                self._log('  Masaüstüne başlatma dosyası kopyalandı (ERP v21.bat)', 'ok')
        except Exception as e:
            self._log(f'  Kısayol oluşturulamadı: {e}')

    def _kurulum_tamam(self):
        self.btn_ileri.config(state='normal', text='✓ Kapat',
                              command=self.destroy)
        self.btn_baslat.config(state='disabled')
        messagebox.showinfo('Kurulum Tamamlandı',
            f'ERP MRP Yönetim Entegrasyon Sistemi başarıyla kuruldu!\n\n'
            f'Dizin: {self.kurulum_dizin.get()}\n\n'
            f'Başlatmak için masaüstündeki\n"ERP MRP Yönetim Entegrasyon Sistemi" kısayolunu kullanın.'
            f' Romancı iyi günler diler.                   ___by ®omanci,2026')

    # ── Sayfa Navigasyonu ─────────────────────────────────────────────────────

    def _sayfa_goster(self, idx):
        for s in self.sayfalar:
            s.pack_forget()
        self.sayfalar[idx].pack(fill='both', expand=True)
        self.aktif_sayfa.set(idx)

        # Buton durumları
        self.btn_geri.config(state='normal' if idx > 0 else 'disabled')

        son_sayfa = len(self.sayfalar) - 1
        if idx == son_sayfa:
            self.btn_ileri.config(text='Kapat', command=self.destroy)
            self._ozet_goster()
        else:
            self.btn_ileri.config(text='İleri →', command=self._ileri)

    def _ileri(self):
        idx = self.aktif_sayfa.get()
        if idx < len(self.sayfalar) - 1:
            self._sayfa_goster(idx + 1)

    def _geri(self):
        idx = self.aktif_sayfa.get()
        if idx > 0:
            self._sayfa_goster(idx - 1)


# ── Giriş noktası ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    try:
        app = KurulumSihirbazi()
        app.mainloop()
    except Exception as e:
        # tkinter yoksa konsol moduna geç
        print(f'Grafik arayüz başlatılamadı: {e}')
        print('Konsol kurulumu için: python setup.py')
