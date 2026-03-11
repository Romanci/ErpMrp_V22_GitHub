from app import db
from datetime import datetime

class Tedarikci(db.Model):
    __tablename__ = 'tedarikci'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tedarikci_kodu = db.Column(db.String(50), unique=True, nullable=False)
    unvan = db.Column(db.String(200), nullable=False)
    yetkili_adi = db.Column(db.String(100))
    telefon = db.Column(db.String(20))
    email = db.Column(db.String(100))
    adres = db.Column(db.Text)
    vergi_dairesi = db.Column(db.String(100))
    vergi_no = db.Column(db.String(50))
    para_birimi = db.Column(db.String(10), default='TL')  # TL, USD, EUR
    banka_bilgisi = db.Column(db.Text)       # EKLENDI: banka adi, iban vb.
    notlar = db.Column(db.Text)              # EKLENDI: genel notlar
    olusturma_tarihi = db.Column(db.String(20), default=lambda: datetime.now().strftime('%d.%m.%Y'))  # EKLENDI
    aktif = db.Column(db.Integer, default=1)
    
    # Iliskiler
    siparisler = db.relationship('SatinAlmaSiparisi', backref='tedarikci', lazy=True)
    
    def __repr__(self):
        return f'<Tedarikci {self.tedarikci_kodu} - {self.unvan}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tedarikci_kodu': self.tedarikci_kodu,
            'unvan': self.unvan,
            'yetkili_adi': self.yetkili_adi,
            'telefon': self.telefon,
            'email': self.email,
            'para_birimi': self.para_birimi,
            'aktif': self.aktif
        }
