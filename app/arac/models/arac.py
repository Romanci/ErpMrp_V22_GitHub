# Araç / Ekipman Takip modelleri
from app import db
from datetime import datetime

def _simdi():
    return datetime.now().strftime('%d.%m.%Y')

class Arac(db.Model):
    __tablename__ = 'arac'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plaka = db.Column(db.String(20), unique=True)
    marka = db.Column(db.String(50))
    model = db.Column(db.String(50))
    yil = db.Column(db.Integer)
    tur = db.Column(db.String(30), default='arac')  # arac|ekipman|is_makinesi
    sase_no = db.Column(db.String(50))
    motor_no = db.Column(db.String(50))
    yakit_turu = db.Column(db.String(20))
    renk = db.Column(db.String(30))
    muayene_tarihi = db.Column(db.String(20))
    sigorta_tarihi = db.Column(db.String(20))
    kasko_tarihi = db.Column(db.String(20))
    sorumlu_personel_id = db.Column(db.Integer, db.ForeignKey('personel.id'), nullable=True)
    notlar = db.Column(db.Text)
    aktif = db.Column(db.Integer, default=1)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)

    sorumlu = db.relationship('Personel', foreign_keys=[sorumlu_personel_id])
    bakimlar = db.relationship('AracBakim', backref='arac', lazy=True, cascade='all, delete-orphan')
    yakit_kayitlari = db.relationship('YakitKayit', backref='arac', lazy=True, cascade='all, delete-orphan')

    @property
    def muayene_uyari(self):
        if not self.muayene_tarihi: return False
        try:
            from datetime import timedelta
            m = datetime.strptime(self.muayene_tarihi, '%d.%m.%Y')
            return (m - datetime.now()).days <= 30
        except: return False


class AracBakim(db.Model):
    __tablename__ = 'arac_bakim'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    arac_id = db.Column(db.Integer, db.ForeignKey('arac.id'), nullable=False)
    bakim_turu = db.Column(db.String(50))  # yag_degisimi|lastik|fren|genel
    tarih = db.Column(db.String(20), default=_simdi)
    km = db.Column(db.Integer, default=0)
    yapilan_isler = db.Column(db.Text)
    maliyet = db.Column(db.Float, default=0)
    servis_yeri = db.Column(db.String(100))
    sonraki_bakim_km = db.Column(db.Integer)
    sonraki_bakim_tarih = db.Column(db.String(20))
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)


class YakitKayit(db.Model):
    __tablename__ = 'yakit_kayit'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    arac_id = db.Column(db.Integer, db.ForeignKey('arac.id'), nullable=False)
    tarih = db.Column(db.String(20), default=_simdi)
    km = db.Column(db.Integer, default=0)
    litre = db.Column(db.Float, default=0)
    birim_fiyat = db.Column(db.Float, default=0)
    toplam = db.Column(db.Float, default=0)
    istasyon = db.Column(db.String(100))
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)
