# Kalite Kontrol modelleri
from app import db
from datetime import datetime

def _simdi():
    return datetime.now().strftime('%d.%m.%Y')

class KaliteKontrol(db.Model):
    __tablename__ = 'kalite_kontrol'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    kontrol_no = db.Column(db.String(30), unique=True, nullable=False)
    tur = db.Column(db.String(30), nullable=False)  # gelen_malzeme|uretim_ara|uretim_cikis
    tarih = db.Column(db.String(20), default=_simdi)
    # Bağlantılar
    urun_id = db.Column(db.Integer, db.ForeignKey('urun.id'), nullable=True)
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikci.id'), nullable=True)
    satin_alma_siparis_id = db.Column(db.Integer, nullable=True)
    uretim_emri_id = db.Column(db.Integer, nullable=True)
    parti_no = db.Column(db.String(50))
    # Miktar
    kontrol_miktari = db.Column(db.Float, default=0)
    kabul_miktari = db.Column(db.Float, default=0)
    ret_miktari = db.Column(db.Float, default=0)
    # Sonuç
    sonuc = db.Column(db.String(20), default='beklemede')  # kabul|kosullu_kabul|ret|beklemede
    notlar = db.Column(db.Text)
    kontrolcu_id = db.Column(db.Integer, nullable=True)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)

    urun = db.relationship('Urun', foreign_keys=[urun_id])
    tedarikci = db.relationship('Tedarikci', foreign_keys=[tedarikci_id])
    hatalar = db.relationship('KaliteHata', backref='kontrol', lazy=True, cascade='all, delete-orphan')


class KaliteHata(db.Model):
    __tablename__ = 'kalite_hata'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    kontrol_id = db.Column(db.Integer, db.ForeignKey('kalite_kontrol.id'), nullable=False)
    hata_turu = db.Column(db.String(100), nullable=False)
    aciklama = db.Column(db.Text)
    adet = db.Column(db.Integer, default=1)
    ciddiyet = db.Column(db.String(20), default='orta')  # dusuk|orta|kritik
    fotograf = db.Column(db.String(200))
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)


class KaliteSertifika(db.Model):
    __tablename__ = 'kalite_sertifika'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ad = db.Column(db.String(100), nullable=False)
    sertifika_no = db.Column(db.String(50))
    tur = db.Column(db.String(50))  # ISO 9001, CE, TSE vb.
    veren_kurum = db.Column(db.String(100))
    baslangic = db.Column(db.String(20))
    bitis = db.Column(db.String(20))
    dosya_yolu = db.Column(db.String(200))
    notlar = db.Column(db.Text)
    aktif = db.Column(db.Integer, default=1)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)

    @property
    def suresi_doldu_mu(self):
        if not self.bitis: return False
        try:
            b = datetime.strptime(self.bitis, '%d.%m.%Y')
            return b < datetime.now()
        except: return False

    @property
    def uyari_var_mi(self):
        if not self.bitis: return False
        try:
            from datetime import timedelta
            b = datetime.strptime(self.bitis, '%d.%m.%Y')
            return (b - datetime.now()).days <= 60
        except: return False
