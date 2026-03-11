# Sayim islemi - periyodik stok sayimi kayitlari
from app import db

class Sayim(db.Model):
    # Tablo adi
    __tablename__ = 'sayim'
    
    # Birincil anahtar
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Hangi depoda sayim yapiliyor - yabanci anahtar
    depo_id = db.Column(db.Integer, db.ForeignKey('depo.id'), nullable=False)
    
    # Sayim tarihi
    sayim_tarihi = db.Column(db.String(20), nullable=False)
    
    # Durum: acik (devam ediyor), kapali (tamamlandi)
    durum = db.Column(db.String(20), default='acik')
    
    # Sayimi yapan kullanici (ileride IK modulune baglanacak)
    kullanici_id = db.Column(db.Integer)
    
    # Iliskiler
    depo = db.relationship('Depo', backref='sayimlar')
    duzeltmeler = db.relationship('SayimDuzeltme', backref='sayim', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        # Sayim temsil metodu
        return f'<Sayim {self.id} - {self.depo.depo_adi if self.depo else "Yok"} ({self.durum})>'
    
    def to_dict(self):
        # Sozluk formatina cevir
        return {
            'id': self.id,
            'depo_id': self.depo_id,
            'depo_adi': self.depo.depo_adi if self.depo else None,
            'sayim_tarihi': self.sayim_tarihi,
            'durum': self.durum,
            'kullanici_id': self.kullanici_id
        }
