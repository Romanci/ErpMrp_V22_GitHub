# Bakim modulu - Tezgah bakim plani ve ariza kayitlari
from app import db
from datetime import datetime


def _simdi():
    return datetime.now().strftime('%d.%m.%Y')


class BakimPlan(db.Model):
    """Periyodik bakim plani - her tezgah icin"""
    __tablename__ = 'bakim_plan'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tezgah_id = db.Column(db.Integer, db.ForeignKey('tezgah.id'), nullable=False)
    bakim_adi = db.Column(db.String(200), nullable=False)
    bakim_turu = db.Column(db.String(50), default='periyodik')  # periyodik, mevsimlik, yillik
    periyot_gun = db.Column(db.Integer, default=30)  # kac gunde bir
    son_bakim = db.Column(db.String(20))
    sonraki_bakim = db.Column(db.String(20))
    tahmini_sure_dk = db.Column(db.Integer, default=60)
    aciklama = db.Column(db.Text)
    aktif = db.Column(db.Integer, default=1)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)

    # Iliskiler
    tezgah = db.relationship('Tezgah', backref='bakim_planlari')
    kayitlar = db.relationship('BakimKayit', backref='plan', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<BakimPlan {self.bakim_adi}>'


class BakimKayit(db.Model):
    """Gerceklestirilen bakim kaydi"""
    __tablename__ = 'bakim_kayit'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('bakim_plan.id'), nullable=True)
    tezgah_id = db.Column(db.Integer, db.ForeignKey('tezgah.id'), nullable=False)
    bakim_tarihi = db.Column(db.String(20), nullable=False)
    bakim_turu = db.Column(db.String(50), default='periyodik')
    yapilan_isler = db.Column(db.Text)
    sure_dk = db.Column(db.Integer, default=0)
    maliyet = db.Column(db.Float, default=0)
    personel_id = db.Column(db.Integer, nullable=True)
    sonraki_bakim = db.Column(db.String(20))
    durum = db.Column(db.String(20), default='tamamlandi')  # tamamlandi, eksik
    aciklama = db.Column(db.Text)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)

    # Iliskiler
    tezgah = db.relationship('Tezgah', backref='bakim_kayitlari')

    def __repr__(self):
        return f'<BakimKayit {self.tezgah_id} {self.bakim_tarihi}>'


class ArizaKayit(db.Model):
    """Tezgah ariza ve tamir kayitlari"""
    __tablename__ = 'ariza_kayit'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tezgah_id = db.Column(db.Integer, db.ForeignKey('tezgah.id'), nullable=False)
    ariza_tarihi = db.Column(db.String(20), nullable=False, default=_simdi)
    ariza_aciklama = db.Column(db.Text, nullable=False)
    oncelik = db.Column(db.String(20), default='normal')  # dusuk, normal, yuksek, kritik
    durum = db.Column(db.String(20), default='acik')  # acik, incelemede, cozuldu, kapandi
    tamir_baslangic = db.Column(db.String(20))
    tamir_bitis = db.Column(db.String(20))
    tamir_aciklama = db.Column(db.Text)
    maliyet = db.Column(db.Float, default=0)
    personel_id = db.Column(db.Integer, nullable=True)
    aktif = db.Column(db.Integer, default=1)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)

    # Iliskiler
    tezgah = db.relationship('Tezgah', backref='arizalar')

    def __repr__(self):
        return f'<ArizaKayit {self.tezgah_id} {self.ariza_tarihi}>'
