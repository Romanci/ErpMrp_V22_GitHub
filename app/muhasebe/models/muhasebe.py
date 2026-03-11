# Muhasebe — Gelir/Gider Takibi
from app import db
from datetime import datetime


def _simdi():
    return datetime.now().strftime('%d.%m.%Y')


HESAP_TURLERI = [
    ('gelir',  'Gelir',  '#22c55e'),
    ('gider',  'Gider',  '#ef4444'),
]

GELIR_KATEGORILERI = [
    'Satış Geliri', 'Hizmet Geliri', 'Kira Geliri',
    'Faiz Geliri', 'Diğer Gelir',
]

GIDER_KATEGORILERI = [
    'Hammadde / Malzeme', 'İşçilik', 'Kira', 'Elektrik / Su / Doğalgaz',
    'Nakliye / Lojistik', 'Bakım / Onarım', 'Personel Maaşı',
    'Vergi / Resim / Harç', 'Sigorta', 'Danışmanlık / Hizmet Alımı', 'Diğer Gider',
]


class MuhasebeKalem(db.Model):
    __tablename__ = 'muhasebe_kalem'

    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tur             = db.Column(db.String(10), nullable=False)   # gelir | gider
    kategori        = db.Column(db.String(100))
    aciklama        = db.Column(db.String(300), nullable=False)
    tutar           = db.Column(db.Float, nullable=False)
    para_birimi     = db.Column(db.String(10), default='TL')
    tarih           = db.Column(db.String(20), nullable=False, default=_simdi)

    # Kaynak bağlantıları (otomatik entegrasyon)
    kaynak          = db.Column(db.String(20))   # fatura | satin_alma | elle
    kaynak_id       = db.Column(db.Integer)
    proje_id        = db.Column(db.Integer, db.ForeignKey('proje.id'), nullable=True)
    fatura_no       = db.Column(db.String(50))

    # Meta
    olusturan_id    = db.Column(db.Integer, db.ForeignKey('kullanici.id'), nullable=True)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)

    proje           = db.relationship('Proje', backref='muhasebe_kalemleri', foreign_keys=[proje_id])
    olusturan       = db.relationship('Kullanici', backref='muhasebe_girisleri', foreign_keys=[olusturan_id])

    @property
    def tur_rengi(self):
        return '#22c55e' if self.tur == 'gelir' else '#ef4444'

    @property
    def tur_adi(self):
        return 'Gelir' if self.tur == 'gelir' else 'Gider'

    @staticmethod
    def donem_ozeti(ay=None, yil=None):
        """Belirli dönem için gelir/gider/kar özeti"""
        from sqlalchemy import func
        q = MuhasebeKalem.query
        if yil:
            q = q.filter(MuhasebeKalem.tarih.like(f'%.{yil}'))
        if ay:
            ay_str = f'{int(ay):02d}'
            q = q.filter(MuhasebeKalem.tarih.like(f'%.{ay_str}.%') if yil
                         else MuhasebeKalem.tarih.like(f'%.{ay_str}.%'))

        gelir = q.filter_by(tur='gelir').with_entities(
            func.sum(MuhasebeKalem.tutar)).scalar() or 0
        gider = q.filter_by(tur='gider').with_entities(
            func.sum(MuhasebeKalem.tutar)).scalar() or 0
        return {
            'gelir': round(gelir, 2),
            'gider': round(gider, 2),
            'kar':   round(gelir - gider, 2),
        }
