# CRM - Müşteri, Teklif, Takip modelleri
from app import db
from datetime import datetime

def _simdi():
    return datetime.now().strftime('%d.%m.%Y')

class Musteri(db.Model):
    __tablename__ = 'musteri'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    musteri_kodu = db.Column(db.String(30), unique=True, nullable=False)
    unvan = db.Column(db.String(150), nullable=False)
    tur = db.Column(db.String(20), default='firma')  # firma | bireysel
    vergi_no = db.Column(db.String(20))
    vergi_dairesi = db.Column(db.String(100))
    # İletişim
    telefon = db.Column(db.String(20))
    email = db.Column(db.String(150))
    website = db.Column(db.String(150))
    adres = db.Column(db.Text)
    sehir = db.Column(db.String(50))
    ulke = db.Column(db.String(50), default='Türkiye')
    # Yetkili
    yetkili_ad = db.Column(db.String(100))
    yetkili_tel = db.Column(db.String(20))
    yetkili_email = db.Column(db.String(150))
    # Ticari
    odeme_vadesi = db.Column(db.Integer, default=30)
    para_birimi = db.Column(db.String(10), default='TRY')
    kredi_limiti = db.Column(db.Float, default=0)
    sektor = db.Column(db.String(100))
    notlar = db.Column(db.Text)
    aktif = db.Column(db.Integer, default=1)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)

    teklifler = db.relationship('Teklif', backref='musteri', lazy=True)

    @property
    def tam_ad(self): return self.unvan

    def __repr__(self): return f'<Musteri {self.musteri_kodu}>'


class Teklif(db.Model):
    __tablename__ = 'teklif'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    teklif_no = db.Column(db.String(30), unique=True, nullable=False)
    musteri_id = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=False)
    baslik = db.Column(db.String(200))
    tarih = db.Column(db.String(20), nullable=False, default=_simdi)
    gecerlilik = db.Column(db.String(20))
    para_birimi = db.Column(db.String(10), default='TRY')
    kdv_orani = db.Column(db.Float, default=20)
    toplam_tutar = db.Column(db.Float, default=0)
    kdv_tutari = db.Column(db.Float, default=0)
    genel_toplam = db.Column(db.Float, default=0)
    durum = db.Column(db.String(30), default='taslak')  # taslak|gonderildi|kabul|red|iptal
    notlar = db.Column(db.Text)
    olusturan_id = db.Column(db.Integer, nullable=True)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)

    satirlar = db.relationship('TeklifSatir', backref='teklif', lazy=True, cascade='all, delete-orphan')

    def toplam_hesapla(self):
        self.toplam_tutar = sum(s.toplam for s in self.satirlar)
        self.kdv_tutari = self.toplam_tutar * self.kdv_orani / 100
        self.genel_toplam = self.toplam_tutar + self.kdv_tutari


class TeklifSatir(db.Model):
    __tablename__ = 'teklif_satir'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    teklif_id = db.Column(db.Integer, db.ForeignKey('teklif.id'), nullable=False)
    sira = db.Column(db.Integer, default=1)
    urun_id = db.Column(db.Integer, db.ForeignKey('urun.id'), nullable=True)
    tanim = db.Column(db.String(200), nullable=False)
    birim = db.Column(db.String(20), default='Adet')
    miktar = db.Column(db.Float, default=1)
    birim_fiyat = db.Column(db.Float, default=0)
    iskonto = db.Column(db.Float, default=0)  # yüzde
    toplam = db.Column(db.Float, default=0)

    urun = db.relationship('Urun', foreign_keys=[urun_id])

    def hesapla(self):
        self.toplam = self.miktar * self.birim_fiyat * (1 - self.iskonto / 100)


class MusteriTakip(db.Model):
    __tablename__ = 'musteri_takip'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    musteri_id = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=False)
    tur = db.Column(db.String(30), default='not')  # not|arama|email|ziyaret|hatirlatma
    baslik = db.Column(db.String(200))
    aciklama = db.Column(db.Text)
    tarih = db.Column(db.String(20), default=_simdi)
    hatirlatma_tarihi = db.Column(db.String(20))
    tamamlandi = db.Column(db.Integer, default=0)
    olusturan_id = db.Column(db.Integer, nullable=True)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)

    musteri = db.relationship('Musteri', backref=db.backref('takipler', lazy=True))
