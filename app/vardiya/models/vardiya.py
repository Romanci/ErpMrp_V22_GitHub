# Vardiya Yönetimi modelleri
from app import db
from datetime import datetime

def _simdi():
    return datetime.now().strftime('%d.%m.%Y')

class VardiyaTanim(db.Model):
    __tablename__ = 'vardiya_tanim'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ad = db.Column(db.String(50), nullable=False)  # Sabah, Öğle, Gece
    baslangic = db.Column(db.String(10), nullable=False)  # 08:00
    bitis = db.Column(db.String(10), nullable=False)       # 16:00
    renk = db.Column(db.String(10), default='#3b82f6')
    aktif = db.Column(db.Integer, default=1)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)


class VardiyaAtama(db.Model):
    __tablename__ = 'vardiya_atama'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personel_id = db.Column(db.Integer, db.ForeignKey('personel.id'), nullable=False)
    vardiya_id = db.Column(db.Integer, db.ForeignKey('vardiya_tanim.id'), nullable=False)
    tarih = db.Column(db.String(20), nullable=False)
    notlar = db.Column(db.Text)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)

    personel = db.relationship('Personel', backref=db.backref('vardiya_atamalari', lazy=True))
    vardiya = db.relationship('VardiyaTanim', backref=db.backref('atamalar', lazy=True))


class Puantaj(db.Model):
    __tablename__ = 'puantaj'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personel_id = db.Column(db.Integer, db.ForeignKey('personel.id'), nullable=False)
    yil = db.Column(db.Integer, nullable=False)
    ay = db.Column(db.Integer, nullable=False)
    calisilan_gun = db.Column(db.Float, default=0)
    izin_gun = db.Column(db.Float, default=0)
    hastalik_gun = db.Column(db.Float, default=0)
    devamsizlik_gun = db.Column(db.Float, default=0)
    resmi_tatil_gun = db.Column(db.Float, default=0)
    fazla_mesai_saat = db.Column(db.Float, default=0)
    notlar = db.Column(db.Text)
    onaylandi = db.Column(db.Integer, default=0)
    onaylayan_id = db.Column(db.Integer, nullable=True)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)

    personel = db.relationship('Personel', backref=db.backref('puantajlar', lazy=True))

    @property
    def donem_str(self):
        aylar = ['','Ocak','Şubat','Mart','Nisan','Mayıs','Haziran',
                 'Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık']
        return f'{aylar[self.ay]} {self.yil}'


class GunlukDevam(db.Model):
    """Günlük toplu devam takibi — tüm personel tek ekranda"""
    __tablename__ = 'gunluk_devam'

    id                  = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personel_id         = db.Column(db.Integer, db.ForeignKey('personel.id'), nullable=False)
    tarih               = db.Column(db.String(20), nullable=False)
    durum               = db.Column(db.String(20), default='geldi')
    # geldi | gelmedi | gec_geldi | erken_cikis | izinli | resmi_tatil
    giris_saati         = db.Column(db.String(10))
    cikis_saati         = db.Column(db.String(10))
    gecikme_dakika      = db.Column(db.Integer, default=0)
    erken_cikis_dakika  = db.Column(db.Integer, default=0)
    aciklama            = db.Column(db.Text)
    olusturan_id        = db.Column(db.Integer, db.ForeignKey('kullanici.id'), nullable=True)
    olusturma_tarihi    = db.Column(db.String(30), default=_simdi)

    personel            = db.relationship('Personel', backref='gunluk_devamlar', foreign_keys=[personel_id])
    olusturan           = db.relationship('Kullanici', backref='devam_girisleri', foreign_keys=[olusturan_id])

    __table_args__      = (db.UniqueConstraint('personel_id', 'tarih', name='uq_personel_tarih'),)

    DURUM_RENK = {
        'geldi':        '#22c55e',
        'gelmedi':      '#ef4444',
        'gec_geldi':    '#f59e0b',
        'erken_cikis':  '#f97316',
        'izinli':       '#3b82f6',
        'resmi_tatil':  '#8b5cf6',
        'yari_gun':     '#06b6d4',
    }

    DURUM_ADI = {
        'geldi':        'Geldi',
        'gelmedi':      'Gelmedi',
        'gec_geldi':    'Geç Geldi',
        'erken_cikis':  'Erken Çıktı',
        'izinli':       'İzinli',
        'resmi_tatil':  'Resmi Tatil',
        'yari_gun':     'Yarı Gün',
    }

    @property
    def durum_adi(self):
        return self.DURUM_ADI.get(self.durum, self.durum)

    @property
    def durum_rengi(self):
        return self.DURUM_RENK.get(self.durum, '#64748b')
