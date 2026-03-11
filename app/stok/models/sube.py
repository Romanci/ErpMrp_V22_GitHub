from app import db
from datetime import datetime


class Sube(db.Model):
    """Firma şubeleri - çok şubeli yapı"""
    __tablename__ = 'sube'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sube_kodu = db.Column(db.String(20), unique=True, nullable=False)
    sube_adi = db.Column(db.String(100), nullable=False)
    adres = db.Column(db.Text)
    sehir = db.Column(db.String(50))
    telefon = db.Column(db.String(20))
    email = db.Column(db.String(100))
    mudur = db.Column(db.String(100))
    merkez_mi = db.Column(db.Integer, default=0)  # 1 = merkez şube
    aktif = db.Column(db.Integer, default=1)
    olusturma_tarihi = db.Column(db.String(20), default=lambda: datetime.now().strftime('%d.%m.%Y'))

    # İlişkiler
    depolar = db.relationship('Depo', backref='sube', lazy=True, foreign_keys='Depo.sube_id')
    personeller = db.relationship('Personel', backref='sube', lazy=True, foreign_keys='Personel.sube_id')

    def __repr__(self):
        return f'<Sube {self.sube_kodu}>'
