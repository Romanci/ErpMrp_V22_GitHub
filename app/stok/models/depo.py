# Depo tanitimi modeli - stoklarin tutuldugu yerler
from app import db

class Depo(db.Model):
    # Tablo adi
    __tablename__ = 'depo'
    
    # Birincil anahtar
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Depo kodu - benzersiz ve zorunlu
    depo_kodu = db.Column(db.String(20), unique=True, nullable=False)
    
    # Depo adi - zorunlu
    depo_adi = db.Column(db.String(100), nullable=False)
    
    # Depo adresi - opsiyonel
    adres = db.Column(db.Text)
    
    # Yetkili kullanici - opsiyonel (ileride IK modulune baglanacak)
    yetkili_kullanici_id = db.Column(db.Integer, nullable=True)
    
    # Aktif mi? 0: pasif, 1: aktif
    sube_id = db.Column(db.Integer, db.ForeignKey('sube.id'), nullable=True)
    aktif = db.Column(db.Integer, default=1)
    
    # Depo ile iliski - lokasyonlar
    lokasyonlar = db.relationship('StokLokasyon', backref='depo', lazy=True)
    
    def __repr__(self):
        # Depo temsil metodu
        return f'<Depo {self.depo_kodu} - {self.depo_adi}>'
    
    def to_dict(self):
        # Sozluk formatina cevir
        return {
            'id': self.id,
            'depo_kodu': self.depo_kodu,
            'depo_adi': self.depo_adi,
            'adres': self.adres,
            'yetkili_kullanici_id': self.yetkili_kullanici_id,
            'aktif': self.aktif
        }
