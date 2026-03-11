# Kullanici ve yetki sistemi modelleri
from app import db
from datetime import datetime
import hashlib
import os
import hmac


def _simdi():
    return datetime.now().strftime('%d.%m.%Y')


def sifre_hashle(sifre: str) -> str:
    """
    PBKDF2-HMAC-SHA256 ile şifre hashle.
    Format: pbkdf2$salt_hex$hash_hex
    SHA-256'ya kıyasla brute-force'a karşı 260.000 kat daha yavaş.
    """
    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac('sha256', sifre.encode('utf-8'), salt, 260000)
    return f"pbkdf2${salt.hex()}${key.hex()}"


def sifre_dogrula(sifre: str, hash_str: str) -> bool:
    """Şifreyi kaydedilmiş hash ile karşılaştır."""
    try:
        if hash_str.startswith('pbkdf2$'):
            # Yeni format
            _, salt_hex, key_hex = hash_str.split('$')
            salt = bytes.fromhex(salt_hex)
            key = bytes.fromhex(key_hex)
            test_key = hashlib.pbkdf2_hmac('sha256', sifre.encode('utf-8'), salt, 260000)
            return hmac.compare_digest(key, test_key)
        else:
            # Eski SHA-256 format (geçiş dönemi)
            eski_hash = hashlib.sha256(sifre.encode('utf-8')).hexdigest()
            return hmac.compare_digest(hash_str, eski_hash)
    except Exception:
        return False


class Rol(db.Model):
    """Sistem rolleri"""
    __tablename__ = 'rol'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rol_adi = db.Column(db.String(50), unique=True, nullable=False)
    aciklama = db.Column(db.String(200))

    # Temel modül izinleri
    stok_erisim = db.Column(db.Integer, default=1)
    satin_alma_erisim = db.Column(db.Integer, default=1)
    uretim_erisim = db.Column(db.Integer, default=1)
    ik_erisim = db.Column(db.Integer, default=0)
    bakim_erisim = db.Column(db.Integer, default=0)

    # Yeni modül izinleri
    crm_erisim = db.Column(db.Integer, default=0)
    kalite_erisim = db.Column(db.Integer, default=0)
    dokuman_erisim = db.Column(db.Integer, default=0)
    arac_erisim = db.Column(db.Integer, default=0)
    vardiya_erisim = db.Column(db.Integer, default=0)
    muhasebe_erisim = db.Column(db.Integer, default=0)

    # Yazma/silme izinleri
    yazma_izni = db.Column(db.Integer, default=1)
    silme_izni = db.Column(db.Integer, default=0)

    aktif = db.Column(db.Integer, default=1)

    def __repr__(self):
        return f'<Rol {self.rol_adi}>'

    def to_dict(self):
        return {
            'id': self.id, 'rol_adi': self.rol_adi, 'aciklama': self.aciklama,
            'stok_erisim': self.stok_erisim, 'satin_alma_erisim': self.satin_alma_erisim,
            'uretim_erisim': self.uretim_erisim, 'ik_erisim': self.ik_erisim,
            'bakim_erisim': self.bakim_erisim, 'crm_erisim': self.crm_erisim,
            'kalite_erisim': self.kalite_erisim, 'dokuman_erisim': self.dokuman_erisim,
            'arac_erisim': self.arac_erisim, 'vardiya_erisim': self.vardiya_erisim,
            'muhasebe_erisim': self.muhasebe_erisim,
            'yazma_izni': self.yazma_izni, 'silme_izni': self.silme_izni,
        }


class Kullanici(db.Model):
    """Sistem kullanicilari"""
    __tablename__ = 'kullanici'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    kullanici_adi = db.Column(db.String(50), unique=True, nullable=False)
    sifre_hash = db.Column(db.String(256), nullable=False)
    ad = db.Column(db.String(100), nullable=False)
    soyad = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True)
    telefon = db.Column(db.String(20))
    departman = db.Column(db.String(100))
    personel_id = db.Column(db.Integer, nullable=True)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)
    son_giris = db.Column(db.String(20))
    aktif = db.Column(db.Integer, default=1)

    roller = db.relationship('KullaniciRol', backref='kullanici', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Kullanici {self.kullanici_adi}>'

    @staticmethod
    def sifrele(sifre):
        """PBKDF2-HMAC-SHA256 ile hashle"""
        return sifre_hashle(sifre)

    def sifre_dogru_mu(self, sifre):
        return sifre_dogrula(sifre, self.sifre_hash)

    def birincil_rol(self):
        if self.roller:
            return self.roller[0].rol
        return None

    def admin_mi(self):
        for kr in self.roller:
            if kr.rol and kr.rol.rol_adi == 'admin':
                return True
        return False

    @property
    def tam_ad(self):
        return f'{self.ad} {self.soyad}'

    def to_dict(self):
        return {
            'id': self.id, 'kullanici_adi': self.kullanici_adi,
            'ad': self.ad, 'soyad': self.soyad, 'email': self.email,
            'telefon': self.telefon, 'departman': self.departman,
            'olusturma_tarihi': self.olusturma_tarihi,
            'son_giris': self.son_giris, 'aktif': self.aktif,
        }


class KullaniciRol(db.Model):
    """Kullanici-Rol baglantisi"""
    __tablename__ = 'kullanici_rol'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    kullanici_id = db.Column(db.Integer, db.ForeignKey('kullanici.id'), nullable=False)
    rol_id = db.Column(db.Integer, db.ForeignKey('rol.id'), nullable=False)
    atama_tarihi = db.Column(db.String(20), default=_simdi)

    rol = db.relationship('Rol', backref='kullanici_roller')
