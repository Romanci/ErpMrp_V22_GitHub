# Proje Yönetimi Modeli
from app import db
from datetime import datetime


def _simdi():
    return datetime.now().strftime('%d.%m.%Y')


PROJE_ASAMALARI = [
    ('teklif',   'Teklif'),
    ('onay',     'Onaylandı'),
    ('uretim',   'Üretimde'),
    ('sevk',     'Sevk Edildi'),
    ('kapandi',  'Kapandı'),
    ('iptal',    'İptal'),
]

ASAMA_RENK = {
    'teklif':  '#3b82f6',
    'onay':    '#f59e0b',
    'uretim':  '#8b5cf6',
    'sevk':    '#06b6d4',
    'kapandi': '#22c55e',
    'iptal':   '#ef4444',
}


class Proje(db.Model):
    __tablename__ = 'proje'

    id                  = db.Column(db.Integer, primary_key=True, autoincrement=True)
    proje_no            = db.Column(db.String(50), unique=True, nullable=False)
    proje_adi           = db.Column(db.String(200), nullable=False)
    aciklama            = db.Column(db.Text)

    # Müşteri bağlantısı (CRM)
    musteri_id          = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=True)
    musteri_adi_serbest = db.Column(db.String(200))  # CRM'de yoksa elle giriş

    # Kaynak
    teklif_id           = db.Column(db.Integer, db.ForeignKey('teklif.id'), nullable=True)

    # Aşama
    asama               = db.Column(db.String(20), default='teklif')

    # Tarihler
    baslangic_tarihi    = db.Column(db.String(20))
    bitis_tarihi        = db.Column(db.String(20))
    gercek_bitis        = db.Column(db.String(20))

    # Bütçe
    planlanan_maliyet   = db.Column(db.Float, default=0)
    para_birimi         = db.Column(db.String(10), default='TL')

    # Sorumlu
    sorumlu_id          = db.Column(db.Integer, db.ForeignKey('kullanici.id'), nullable=True)

    # Meta
    aktif               = db.Column(db.Integer, default=1)
    olusturma_tarihi    = db.Column(db.String(20), default=_simdi)
    guncellenme_tarihi  = db.Column(db.String(20), default=_simdi)

    # İlişkiler
    musteri             = db.relationship('Musteri', backref='projeler', foreign_keys=[musteri_id])
    teklif              = db.relationship('Teklif', backref='proje', foreign_keys=[teklif_id])
    sorumlu             = db.relationship('Kullanici', backref='projeler', foreign_keys=[sorumlu_id])
    gorevler            = db.relationship('ProjeGorev', backref='proje', lazy=True, cascade='all, delete-orphan')

    @property
    def musteri_adi(self):
        if self.musteri:
            return self.musteri.unvan
        return self.musteri_adi_serbest or '—'

    @property
    def asama_adi(self):
        return dict(PROJE_ASAMALARI).get(self.asama, self.asama)

    @property
    def asama_rengi(self):
        return ASAMA_RENK.get(self.asama, '#64748b')

    @property
    def gerceklesen_maliyet(self):
        """Fatura ve satın alma toplamından otomatik hesapla"""
        from app.fatura.models.fatura import FaturaSatir
        from app.fatura.models.fatura import Fatura
        try:
            toplam = 0
            faturalar = Fatura.query.filter_by(aktif=1).all()
            for f in faturalar:
                for s in f.satirlar:
                    if s.proje_kodu == self.proje_no:
                        toplam += s.satir_toplam
            return round(toplam, 2)
        except Exception:
            return 0

    @property
    def butce_kullanim_yuzdesi(self):
        if not self.planlanan_maliyet:
            return 0
        return min(round(self.gerceklesen_maliyet / self.planlanan_maliyet * 100, 1), 999)

    @property
    def tamamlanmamis_gorev_sayisi(self):
        return sum(1 for g in self.gorevler if g.durum != 'tamamlandi')


class ProjeGorev(db.Model):
    __tablename__ = 'proje_gorev'

    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    proje_id        = db.Column(db.Integer, db.ForeignKey('proje.id'), nullable=False)
    baslik          = db.Column(db.String(200), nullable=False)
    aciklama        = db.Column(db.Text)
    departman       = db.Column(db.String(50))  # depo|uretim|satin_alma|yonetim
    atanan_id       = db.Column(db.Integer, db.ForeignKey('kullanici.id'), nullable=True)
    son_tarih       = db.Column(db.String(20))
    durum           = db.Column(db.String(20), default='bekliyor')  # bekliyor|devam|tamamlandi|iptal
    oncelik         = db.Column(db.String(10), default='normal')    # dusuk|normal|yuksek|kritik
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)
    tamamlanma_tarihi = db.Column(db.String(20))

    atanan          = db.relationship('Kullanici', backref='gorevler', foreign_keys=[atanan_id])

    @property
    def oncelik_rengi(self):
        return {'dusuk': '#94a3b8', 'normal': '#3b82f6',
                'yuksek': '#f59e0b', 'kritik': '#ef4444'}.get(self.oncelik, '#64748b')

    @property
    def durum_adi(self):
        return {'bekliyor': 'Bekliyor', 'devam': 'Devam Ediyor',
                'tamamlandi': 'Tamamlandı', 'iptal': 'İptal'}.get(self.durum, self.durum)
