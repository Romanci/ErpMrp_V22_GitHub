# Sayim sonucu olusan farklarin kaydi ve duzeltme islemleri
from app import db

class SayimDuzeltme(db.Model):
    # Tablo adi
    __tablename__ = 'sayim_duzeltme'
    
    # Birincil anahtar
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Hangi sayima ait - yabanci anahtar
    sayim_id = db.Column(db.Integer, db.ForeignKey('sayim.id'), nullable=False)
    
    # Hangi urun - yabanci anahtar
    urun_id = db.Column(db.Integer, db.ForeignKey('urun.id'), nullable=False)
    
    # Hangi parti (varsa) - yabanci anahtar
    parti_id = db.Column(db.Integer, db.ForeignKey('parti.id'), nullable=True)
    
    # Sistemde kayitli olan miktar
    sistem_miktar = db.Column(db.Float, default=0)
    
    # Sayimda sayilan gercek miktar
    sayilan_miktar = db.Column(db.Float, default=0)
    
    # Fark (sayilan - sistem) - pozitif: fazla, negatif: eksik
    fark = db.Column(db.Float, default=0)
    
    # Iliskiler
    urun = db.relationship('Urun', backref='sayim_duzeltmeler')
    parti = db.relationship('Parti', backref='sayim_duzeltmeler')
    
    def __repr__(self):
        # Duzeltme temsil metodu
        return f'<SayimDuzeltme {self.urun.urun_adi if self.urun else "Yok"}: {self.fark}>'
    
    def to_dict(self):
        # Sozluk formatina cevir
        return {
            'id': self.id,
            'sayim_id': self.sayim_id,
            'urun_id': self.urun_id,
            'urun_adi': self.urun.urun_adi if self.urun else None,
            'parti_id': self.parti_id,
            'parti_kodu': self.parti.parti_kodu if self.parti else None,
            'sistem_miktar': self.sistem_miktar,
            'sayilan_miktar': self.sayilan_miktar,
            'fark': self.fark
        }
    
    def fark_tipi(self):
        # Farkin turunu belirle
        if self.fark > 0:
            return 'Fazla'
        elif self.fark < 0:
            return 'Eksik'
        else:
            return 'Esit'
