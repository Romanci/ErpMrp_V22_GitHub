# Sistem Bildirimleri
from app import db
from datetime import datetime


def _simdi():
    return datetime.now().strftime('%d.%m.%Y %H:%M')


class Bildirim(db.Model):
    __tablename__ = 'bildirim'

    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    baslik          = db.Column(db.String(100), nullable=False)
    mesaj           = db.Column(db.Text, nullable=False)
    tur             = db.Column(db.String(30), default='genel')  # proje|siparis|stok|uretim|genel
    kayit_id        = db.Column(db.Integer)
    okundu          = db.Column(db.Integer, default=0)
    kullanici_id    = db.Column(db.Integer, db.ForeignKey('kullanici.id'), nullable=True)
    olusturma_tarihi = db.Column(db.String(30), default=_simdi)

    kullanici       = db.relationship('Kullanici', backref='bildirimler', foreign_keys=[kullanici_id])

    @staticmethod
    def okunmamis_sayisi(kullanici_id=None):
        q = Bildirim.query.filter_by(okundu=0)
        if kullanici_id:
            q = q.filter(
                (Bildirim.kullanici_id == kullanici_id) |
                (Bildirim.kullanici_id == None)
            )
        return q.count()
