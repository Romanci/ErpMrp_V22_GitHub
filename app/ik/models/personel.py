# IK Modulu - Personel, Izin, Maas, Devamsizlik, Tatil, KKD/Zimmet modelleri
from app import db
from datetime import datetime


def _simdi():
    return datetime.now().strftime('%d.%m.%Y')


class Personel(db.Model):
    """Sirket personeli"""
    __tablename__ = 'personel'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sicil_no = db.Column(db.String(30), unique=True, nullable=False)
    ad = db.Column(db.String(100), nullable=False)
    soyad = db.Column(db.String(100), nullable=False)
    tc_kimlik = db.Column(db.String(11))
    dogum_tarihi = db.Column(db.String(20))
    cinsiyet = db.Column(db.String(10))

    # Iletisim
    telefon = db.Column(db.String(20))
    email = db.Column(db.String(150))
    adres = db.Column(db.Text)

    # Is bilgileri
    departman = db.Column(db.String(100))
    pozisyon = db.Column(db.String(100))
    ise_baslama = db.Column(db.String(20))
    isten_ayrilma = db.Column(db.String(20))
    calisma_turu = db.Column(db.String(20), default='tam_zamanli')
    maas = db.Column(db.Float, default=0)
    para_birimi = db.Column(db.String(10), default='TL')

    # Sube / durum
    sube_id = db.Column(db.Integer, db.ForeignKey('sube.id'), nullable=True)
    aktif = db.Column(db.Integer, default=1)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)

    # Iliskiler
    izinler = db.relationship('Izin', backref='personel', lazy=True, cascade='all, delete-orphan')
    maas_kayitlari = db.relationship('Maas', backref='personel', lazy=True, cascade='all, delete-orphan')

    @property
    def tam_ad(self):
        return f'{self.ad} {self.soyad}'

    @property
    def yas(self):
        if not self.dogum_tarihi:
            return None
        try:
            d = datetime.strptime(self.dogum_tarihi, '%d.%m.%Y')
            return int((datetime.now() - d).days / 365.25)
        except Exception:
            return None

    @property
    def kidem_yil(self):
        if not self.ise_baslama:
            return 0
        try:
            b = datetime.strptime(self.ise_baslama, '%d.%m.%Y')
            return round((datetime.now() - b).days / 365.25, 1)
        except Exception:
            return 0

    def __repr__(self):
        return f'<Personel {self.sicil_no} - {self.tam_ad}>'

    def to_dict(self):
        return {
            'id': self.id,
            'sicil_no': self.sicil_no,
            'ad': self.ad,
            'soyad': self.soyad,
            'departman': self.departman,
            'pozisyon': self.pozisyon,
            'ise_baslama': self.ise_baslama,
            'maas': self.maas,
            'aktif': self.aktif,
        }


class PersonelEkBilgi(db.Model):
    """Personel fiziksel, saglik ve olcu bilgileri"""
    __tablename__ = 'personel_ek_bilgi'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personel_id = db.Column(db.Integer, db.ForeignKey('personel.id'), nullable=False, unique=True)

    # Saglik
    kan_grubu = db.Column(db.String(10))
    boy = db.Column(db.Float)
    kilo = db.Column(db.Float)
    kronik_hastalik = db.Column(db.Text)
    ilac_kullanimi = db.Column(db.Text)

    # Acil iletisim
    acil_ad = db.Column(db.String(100))
    acil_tel = db.Column(db.String(20))
    acil_yakinlik = db.Column(db.String(50))

    # Beden olculeri (KKD / kiyafet icin)
    ust_beden = db.Column(db.String(10))
    alt_beden = db.Column(db.String(10))
    ayak_numarasi = db.Column(db.String(10))
    baret_bedeni = db.Column(db.String(10))

    guncelleme = db.Column(db.String(20), default=_simdi)
    personel = db.relationship('Personel', backref=db.backref('ek_bilgi', uselist=False))


class Izin(db.Model):
    """
    Personel izin kayitlari
    izin_turu: yillik | hastalik | mazeret | ucretsiz | babalik | annelik |
               vefat | resmi_tatil | firma_tatili
    """
    __tablename__ = 'izin'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personel_id = db.Column(db.Integer, db.ForeignKey('personel.id'), nullable=False)
    izin_turu = db.Column(db.String(50), nullable=False)
    baslangic = db.Column(db.String(20), nullable=False)
    bitis = db.Column(db.String(20), nullable=False)
    gun_sayisi = db.Column(db.Float, nullable=False)
    durum = db.Column(db.String(20), default='beklemede')  # beklemede | onaylandi | reddedildi
    onaylayan_id = db.Column(db.Integer, nullable=True)
    onay_tarihi = db.Column(db.String(20))
    red_nedeni = db.Column(db.Text)
    talep_turu = db.Column(db.String(20), default='talep')  # talep | direkt
    # Vefat izni
    vefat_yakin = db.Column(db.String(50))   # anne | baba | es | cocuk | kardes
    # Hastalik
    rapor_no = db.Column(db.String(50))
    rapor_hastane = db.Column(db.String(100))
    aciklama = db.Column(db.Text)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)

    def __repr__(self):
        ad = self.personel.tam_ad if self.personel else '-'
        return f'<Izin {ad} {self.baslangic}>'

    @staticmethod
    def yillik_izin_hakki(personel):
        """Turk Is Kanunu + 50 yas kurali"""
        if not personel.ise_baslama:
            return 14
        try:
            baslama = datetime.strptime(personel.ise_baslama, '%d.%m.%Y')
            kidem = (datetime.now() - baslama).days / 365.25
            if kidem < 1:
                return 0
            if kidem < 5:
                temel = 14
            elif kidem < 15:
                temel = 20
            else:
                temel = 26
            # 50 yas kurali
            yas = personel.yas or 0
            if yas >= 50:
                return max(temel, 20)
            return temel
        except Exception:
            return 14

    @staticmethod
    def kullanilan_yillik(personel_id, yil=None):
        """Bu yil kullanilan yillik izin gunleri"""
        if not yil:
            yil = datetime.now().year
        bas = f'01.01.{yil}'
        bit = f'31.12.{yil}'
        izinler = Izin.query.filter_by(
            personel_id=personel_id, izin_turu='yillik', durum='onaylandi'
        ).all()
        return sum(iz.gun_sayisi for iz in izinler if bas <= iz.baslangic <= bit)


class Devamsizlik(db.Model):
    """Gelmeme, gec gelme, erken ayrilma kayitlari"""
    __tablename__ = 'devamsizlik'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personel_id = db.Column(db.Integer, db.ForeignKey('personel.id'), nullable=False)
    tarih = db.Column(db.String(20), nullable=False)
    tur = db.Column(db.String(30), nullable=False)  # gelmedi | gec_geldi | erken_ayrildi | yarim_gun
    sure_dakika = db.Column(db.Integer, default=0)
    aciklama = db.Column(db.Text)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)

    personel = db.relationship('Personel', backref=db.backref('devamsizliklar', lazy=True))


class Tatil(db.Model):
    """Resmi tatiller ve firma ozel tatilleri"""
    __tablename__ = 'tatil'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ad = db.Column(db.String(100), nullable=False)
    tarih = db.Column(db.String(20), nullable=False)
    bitis_tarihi = db.Column(db.String(20))
    tur = db.Column(db.String(20), default='resmi')  # resmi | dini | firma
    yillik_tekrar = db.Column(db.Integer, default=1)
    aciklama = db.Column(db.Text)
    aktif = db.Column(db.Integer, default=1)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)


class KkdTanim(db.Model):
    """KKD ve is kiyafeti tanim listesi"""
    __tablename__ = 'kkd_tanim'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    kod = db.Column(db.String(30), unique=True, nullable=False)
    ad = db.Column(db.String(100), nullable=False)
    tur = db.Column(db.String(30), default='kkd')   # kkd | kiyafet | ekipman
    aciklama = db.Column(db.Text)
    yenileme_ay = db.Column(db.Integer, default=12)
    stok_urun_id = db.Column(db.Integer, db.ForeignKey('urun.id'), nullable=True)
    aktif = db.Column(db.Integer, default=1)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)

    stok_urun = db.relationship('Urun', backref='kkd_tanimlari', foreign_keys=[stok_urun_id])
    zimmetler = db.relationship('Zimmet', backref='kkd', lazy=True)


class Zimmet(db.Model):
    """Personele verilen KKD / kiyafet zimmet kayitlari"""
    __tablename__ = 'zimmet'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personel_id = db.Column(db.Integer, db.ForeignKey('personel.id'), nullable=False)
    kkd_tanim_id = db.Column(db.Integer, db.ForeignKey('kkd_tanim.id'), nullable=False)
    miktar = db.Column(db.Float, default=1)
    beden = db.Column(db.String(20))
    verilis_tarihi = db.Column(db.String(20), nullable=False, default=_simdi)
    yenileme_tarihi = db.Column(db.String(20))
    durum = db.Column(db.String(30), default='aktif')
    # aktif | iade_edildi | kirik | bozuk | ozelligini_kaybetti
    iade_tarihi = db.Column(db.String(20))
    onceki_zimmet_id = db.Column(db.Integer, db.ForeignKey('zimmet.id'), nullable=True)
    aciklama = db.Column(db.Text)
    stoktan_dusuldu = db.Column(db.Integer, default=0)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)

    personel = db.relationship('Personel', backref=db.backref('zimmetler', lazy=True))
    onceki = db.relationship('Zimmet', remote_side='Zimmet.id', foreign_keys=[onceki_zimmet_id])

    @property
    def yenileme_gerekiyor(self):
        if not self.yenileme_tarihi or self.durum != 'aktif':
            return False
        try:
            yn = datetime.strptime(self.yenileme_tarihi, '%d.%m.%Y')
            return (yn - datetime.now()).days <= 30
        except Exception:
            return False


class Maas(db.Model):
    """Personel maas odemesi kayitlari"""
    __tablename__ = 'maas'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    personel_id = db.Column(db.Integer, db.ForeignKey('personel.id'), nullable=False)
    donem = db.Column(db.String(10), nullable=False)
    brut_maas = db.Column(db.Float, nullable=False)
    prim = db.Column(db.Float, default=0)
    kesinti = db.Column(db.Float, default=0)
    net_maas = db.Column(db.Float, nullable=False)
    odeme_tarihi = db.Column(db.String(20))
    odendi_mi = db.Column(db.Integer, default=0)
    aciklama = db.Column(db.Text)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)

    def __repr__(self):
        ad = self.personel.tam_ad if self.personel else '-'
        return f'<Maas {ad} {self.donem}>'
