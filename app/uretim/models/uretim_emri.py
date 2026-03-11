# Uretim emri modeli - is emri, operasyon takibi
from app import db
from datetime import datetime

class UretimEmri(db.Model):
    __tablename__ = 'uretim_emri'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    emir_no = db.Column(db.String(50), unique=True, nullable=False)
    urun_id = db.Column(db.Integer, db.ForeignKey('urun.id'), nullable=False)
    miktar = db.Column(db.Float, nullable=False)
    planlanan_baslangic = db.Column(db.String(20))
    planlanan_bitis = db.Column(db.String(20))
    gerceklesen_baslangic = db.Column(db.String(20))
    gerceklesen_bitis = db.Column(db.String(20))
    durum = db.Column(db.String(20), default='beklemede')  # beklemede, devam, tamamlandi, iptal
    oncelik = db.Column(db.String(10), default='normal')  # dusuk, normal, yuksek, acil
    olusturan_kullanici_id = db.Column(db.Integer, nullable=True)  # EKLENDI
    aciklama = db.Column(db.Text)
    aktif = db.Column(db.Integer, default=1)
    
    # Iliskiler
    urun = db.relationship('Urun', backref='uretim_emirleri')
    operasyonlar = db.relationship('UretimOperasyonu', backref='uretim_emri', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<UretimEmri {self.emir_no} - {self.urun.urun_adi if self.urun else "Yok"}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'emir_no': self.emir_no,
            'urun_id': self.urun_id,
            'urun_adi': self.urun.urun_adi if self.urun else None,
            'miktar': self.miktar,
            'planlanan_baslangic': self.planlanan_baslangic,
            'planlanan_bitis': self.planlanan_bitis,
            'durum': self.durum,
            'oncelik': self.oncelik,
            'aktif': self.aktif
        }

class UretimOperasyonu(db.Model):
    __tablename__ = 'uretim_operasyonu'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    uretim_emri_id = db.Column(db.Integer, db.ForeignKey('uretim_emri.id'), nullable=False)
    operasyon_sirasi = db.Column(db.Integer, default=1)
    operasyon_adi = db.Column(db.String(100), nullable=False)
    tezgah_id = db.Column(db.Integer, db.ForeignKey('tezgah.id'), nullable=True)
    personel_id = db.Column(db.Integer, nullable=True)  # IK modulune baglanacak
    planlanan_sure = db.Column(db.Float, default=0)  # dakika
    gerceklesen_sure = db.Column(db.Float, default=0)  # dakika
    durum = db.Column(db.String(20), default='beklemede')  # beklemede, devam, tamamlandi
    baslangic_zamani = db.Column(db.String(20))
    bitis_zamani = db.Column(db.String(20))
    fire_miktari = db.Column(db.Float, default=0)
    aciklama = db.Column(db.Text)
    
    # Iliskiler
    tezgah = db.relationship('Tezgah', backref='operasyonlar')
    
    def __repr__(self):
        return f'<UretimOperasyonu {self.operasyon_sirasi} - {self.operasyon_adi}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'uretim_emri_id': self.uretim_emri_id,
            'operasyon_sirasi': self.operasyon_sirasi,
            'operasyon_adi': self.operasyon_adi,
            'tezgah_id': self.tezgah_id,
            'planlanan_sure': self.planlanan_sure,
            'gerceklesen_sure': self.gerceklesen_sure,
            'durum': self.durum,
            'fire_miktari': self.fire_miktari
        }
