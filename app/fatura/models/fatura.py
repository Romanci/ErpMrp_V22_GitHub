# Fatura ve Irsaliye modelleri
from app import db
from datetime import datetime


def _simdi():
    return datetime.now().strftime('%d.%m.%Y')


class Fatura(db.Model):
    """Alis ve satis faturalari"""
    __tablename__ = 'fatura'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fatura_no = db.Column(db.String(50), unique=True, nullable=False)
    fatura_tipi = db.Column(db.String(20), nullable=False)  # alis, satis
    fatura_tarihi = db.Column(db.String(20), nullable=False, default=_simdi)
    vade_tarihi = db.Column(db.String(20))

    # Taraflar
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikci.id'), nullable=True)  # alis
    musteri_adi = db.Column(db.String(200))   # satis - basit musteri adi
    musteri_vergi_no = db.Column(db.String(50))
    musteri_adres = db.Column(db.Text)

    # Tutarlar
    ara_toplam = db.Column(db.Float, default=0)
    toplam_kdv = db.Column(db.Float, default=0)
    toplam_indirim = db.Column(db.Float, default=0)
    genel_toplam = db.Column(db.Float, default=0)
    para_birimi = db.Column(db.String(10), default='TL')

    # Bagli siparis (alis faturasindan)
    siparis_id = db.Column(db.Integer, db.ForeignKey('satin_alma_siparisi.id'), nullable=True)

    # Durum
    durum = db.Column(db.String(20), default='taslak')  # taslak, kesildi, odendi, iptal
    odeme_tarihi = db.Column(db.String(20))
    aciklama = db.Column(db.Text)
    aktif = db.Column(db.Integer, default=1)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)

    # Iliskiler
    tedarikci = db.relationship('Tedarikci', backref='faturalar')
    siparis = db.relationship('SatinAlmaSiparisi', backref='faturalar')
    satirlar = db.relationship('FaturaSatir', backref='fatura', lazy=True, cascade='all, delete-orphan')
    irsaliyeler = db.relationship('Irsaliye', backref='fatura', lazy=True)

    def __repr__(self):
        return f'<Fatura {self.fatura_no} {self.fatura_tipi}>'

    def toplam_hesapla(self):
        """Satirlardan toplami yeniden hesapla"""
        ara = sum(s.miktar * s.birim_fiyat for s in self.satirlar)
        indirim = sum(s.miktar * s.birim_fiyat * s.indirim_orani / 100 for s in self.satirlar)
        kdv = sum((s.miktar * s.birim_fiyat * (1 - s.indirim_orani/100)) * s.kdv_orani / 100 for s in self.satirlar)
        self.ara_toplam = round(ara, 2)
        self.toplam_indirim = round(indirim, 2)
        self.toplam_kdv = round(kdv, 2)
        self.genel_toplam = round(ara - indirim + kdv, 2)


class FaturaSatir(db.Model):
    """Fatura kalemleri"""
    __tablename__ = 'fatura_satir'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    fatura_id = db.Column(db.Integer, db.ForeignKey('fatura.id'), nullable=False)
    urun_id = db.Column(db.Integer, db.ForeignKey('urun.id'), nullable=True)
    tanim = db.Column(db.String(300))   # serbest tanim (urun secilmemisse)
    miktar = db.Column(db.Float, nullable=False)
    birim = db.Column(db.String(20), default='adet')
    birim_fiyat = db.Column(db.Float, nullable=False)
    indirim_orani = db.Column(db.Float, default=0)
    kdv_orani = db.Column(db.Float, default=18)
    proje_kodu = db.Column(db.String(100))   # Hangi projeye ait (opsiyonel)

    # Iliskiler
    urun = db.relationship('Urun', backref='fatura_satirlari')

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
        return self.tanim or '-'

    def __repr__(self):
        return f'<FaturaSatir {self.satir_tanim} x{self.miktar}>'


class Irsaliye(db.Model):
    """Mal teslim irsaliyesi"""
    __tablename__ = 'irsaliye'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    irsaliye_no = db.Column(db.String(50), unique=True, nullable=False)
    irsaliye_tipi = db.Column(db.String(20), default='cikis')  # giris, cikis
    irsaliye_tarihi = db.Column(db.String(20), nullable=False, default=_simdi)

    # Taraflar
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikci.id'), nullable=True)
    musteri_adi = db.Column(db.String(200))
    teslim_adresi = db.Column(db.Text)

    # Bagli belgeler
    fatura_id = db.Column(db.Integer, db.ForeignKey('fatura.id'), nullable=True)
    siparis_id = db.Column(db.Integer, db.ForeignKey('satin_alma_siparisi.id'), nullable=True)

    # Taşıma
    arac_plaka = db.Column(db.String(20))
    sofor = db.Column(db.String(100))

    durum = db.Column(db.String(20), default='hazirlaniyor')  # hazirlaniyor, yolda, teslim, iptal
    aciklama = db.Column(db.Text)
    aktif = db.Column(db.Integer, default=1)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)

    # Iliskiler
    tedarikci = db.relationship('Tedarikci', backref='irsaliyeler')
    satirlar = db.relationship('IrsaliyeSatir', backref='irsaliye', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Irsaliye {self.irsaliye_no}>'


class IrsaliyeSatir(db.Model):
    """İrsaliye kalemleri"""
    __tablename__ = 'irsaliye_satir'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    irsaliye_id = db.Column(db.Integer, db.ForeignKey('irsaliye.id'), nullable=False)
    urun_id = db.Column(db.Integer, db.ForeignKey('urun.id'), nullable=True)
    tanim = db.Column(db.String(300))
    miktar = db.Column(db.Float, nullable=False)
    birim = db.Column(db.String(20), default='adet')
    aciklama = db.Column(db.Text)

    # Iliskiler
    urun = db.relationship('Urun', backref='irsaliye_satirlari')

    @property
    def satir_tanim(self):
        if self.urun:
            return self.urun.urun_adi
        return self.tanim or '-'
