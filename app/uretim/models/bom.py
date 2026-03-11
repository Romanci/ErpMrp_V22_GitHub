# Bill of Materials - Urun agaci, recete
from app import db
from datetime import datetime

def _bugun():
    return datetime.now().strftime('%d.%m.%Y')

class Bom(db.Model):
    __tablename__ = 'bom'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    urun_id = db.Column(db.Integer, db.ForeignKey('urun.id'), nullable=False)
    versiyon = db.Column(db.String(10), default='1.0')
    gecerli = db.Column(db.Integer, default=1)
    olusturma_tarihi = db.Column(db.String(20), default=_bugun)
    olusturan_kullanici_id = db.Column(db.Integer, nullable=True)
    aciklama = db.Column(db.Text)
    
    # Iliskiler
    urun = db.relationship('Urun', backref='bomlar')
    satirlar = db.relationship('BomSatir', backref='bom', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Bom {self.urun.urun_adi if self.urun else "Yok"} v{self.versiyon}>'

class BomSatir(db.Model):
    __tablename__ = 'bom_satir'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    bom_id = db.Column(db.Integer, db.ForeignKey('bom.id'), nullable=False)
    ham_madde_id = db.Column(db.Integer, db.ForeignKey('urun.id'), nullable=False)
    miktar = db.Column(db.Float, nullable=False)
    fire_orani = db.Column(db.Float, default=0)  # yuzde
    operasyon_sirasi = db.Column(db.Integer, default=1)
    aciklama = db.Column(db.Text)
    
    # Iliskiler
    ham_madde = db.relationship('Urun', foreign_keys=[ham_madde_id])
    
    def __repr__(self):
        return f'<BomSatir {self.ham_madde.urun_adi if self.ham_madde else "Yok"} x{self.miktar}>'
