# Satış Siparişi Modeli
from app import db
from datetime import datetime


def _simdi():
    return datetime.now().strftime('%d.%m.%Y')


SIPARIS_DURUMLARI = [
    ('alindi',       'Alındı',          '#94a3b8'),
    ('onay_bekliyor','Onay Bekliyor',    '#f59e0b'),
    ('onaylandi',    'Onaylandı',        '#3b82f6'),
    ('hazirlaniyor', 'Hazırlanıyor',     '#8b5cf6'),
    ('kismi_hazir',  'Kısmen Hazır',     '#06b6d4'),
    ('hazir',        'Hazır',            '#22c55e'),
    ('sevk_edildi',  'Sevk Edildi',      '#0ea5e9'),
    ('teslim_edildi','Teslim Edildi',    '#15803d'),
    ('iptal',        'İptal',            '#ef4444'),
]

KAYNAK_TURLERI = [
    ('teklif',   'Tekliften Dönüşüm'),
    ('telefon',  'Telefon'),
    ('email',    'E-posta'),
    ('yuz_yuze', 'Yüz Yüze'),
    ('diger',    'Diğer'),
]


class SatisEmri(db.Model):
    __tablename__ = 'satis_emri'

    id                  = db.Column(db.Integer, primary_key=True, autoincrement=True)
    siparis_no          = db.Column(db.String(50), unique=True, nullable=False)

    # Müşteri
    musteri_id          = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=True)
    musteri_adi_serbest = db.Column(db.String(200))
    musteri_telefon     = db.Column(db.String(50))
    teslim_adresi       = db.Column(db.Text)

    # Kaynak
    kaynak              = db.Column(db.String(20), default='telefon')
    teklif_id           = db.Column(db.Integer, db.ForeignKey('teklif.id'), nullable=True)
    proje_id            = db.Column(db.Integer, db.ForeignKey('proje.id'), nullable=True)

    # Tarihler
    siparis_tarihi      = db.Column(db.String(20), default=_simdi)
    termin_tarihi       = db.Column(db.String(20))

    # Durum
    durum               = db.Column(db.String(20), default='alindi')

    # Tutarlar
    toplam_tutar        = db.Column(db.Float, default=0)
    para_birimi         = db.Column(db.String(10), default='TL')

    # Onay
    onaylayan_id        = db.Column(db.Integer, db.ForeignKey('kullanici.id'), nullable=True)
    onay_tarihi         = db.Column(db.String(20))
    onay_notu           = db.Column(db.Text)

    # Meta
    aciklama            = db.Column(db.Text)
    aktif               = db.Column(db.Integer, default=1)
    olusturan_id        = db.Column(db.Integer, db.ForeignKey('kullanici.id'), nullable=True)
    olusturma_tarihi    = db.Column(db.String(20), default=_simdi)

    # İlişkiler
    musteri             = db.relationship('Musteri', backref='satis_emirleri', foreign_keys=[musteri_id])
    teklif              = db.relationship('Teklif', backref='satis_emirleri', foreign_keys=[teklif_id])
    proje               = db.relationship('Proje', backref='satis_emirleri', foreign_keys=[proje_id])
    onaylayan           = db.relationship('Kullanici', backref='onayladigi_emirler', foreign_keys=[onaylayan_id])
    olusturan           = db.relationship('Kullanici', backref='olusturdugu_emirler', foreign_keys=[olusturan_id])
    satirlar            = db.relationship('SatisEmriSatir', backref='siparis', lazy=True, cascade='all, delete-orphan')

    @property
    def musteri_adi(self):
        if self.musteri:
            return self.musteri.unvan
        return self.musteri_adi_serbest or '—'

    @property
    def durum_adi(self):
        return next((d[1] for d in SIPARIS_DURUMLARI if d[0] == self.durum), self.durum)

    @property
    def durum_rengi(self):
        return next((d[2] for d in SIPARIS_DURUMLARI if d[0] == self.durum), '#64748b')

    @property
    def kaynak_adi(self):
        return dict(KAYNAK_TURLERI).get(self.kaynak, self.kaynak)

    def toplam_hesapla(self):
        self.toplam_tutar = round(sum(s.satir_toplam for s in self.satirlar), 2)


class SatisEmriSatir(db.Model):
    __tablename__ = 'satis_emri_satir'

    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    siparis_id      = db.Column(db.Integer, db.ForeignKey('satis_emri.id'), nullable=False)
    urun_id         = db.Column(db.Integer, db.ForeignKey('urun.id'), nullable=True)
    tanim           = db.Column(db.String(300))
    miktar          = db.Column(db.Float, nullable=False, default=1)
    birim           = db.Column(db.String(20), default='Adet')
    birim_fiyat     = db.Column(db.Float, default=0)
    indirim_orani   = db.Column(db.Float, default=0)
    kdv_orani       = db.Column(db.Float, default=18)
    proje_kodu      = db.Column(db.String(100))

    # Stok durumu (yönetici onay ekranı için)
    stok_mevcut     = db.Column(db.Float, default=0)
    uretim_gerekli  = db.Column(db.Integer, default=0)
    satin_alma_gerekli = db.Column(db.Integer, default=0)

    urun            = db.relationship('Urun', backref='satis_emri_satirlari', foreign_keys=[urun_id])

    @property
    def satir_toplam(self):
        ara = self.miktar * self.birim_fiyat
        indirim = ara * (self.indirim_orani / 100)
        kdv = (ara - indirim) * (self.kdv_orani / 100)
        return round(ara - indirim + kdv, 2)

    @property
    def satir_tanim(self):
        if self.urun:
            return self.urun.urun_adi
        return self.tanim or '—'
