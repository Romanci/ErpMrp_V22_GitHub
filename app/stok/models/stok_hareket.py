# Stok hareketleri - giris, cikis, transfer kayitlari
from app import db
from datetime import datetime

class StokHareket(db.Model):
    # Tablo adi
    __tablename__ = 'stok_hareket'
    
    # Birincil anahtar
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Hangi urun - yabanci anahtar
    urun_id = db.Column(db.Integer, db.ForeignKey('urun.id'), nullable=False)
    
    # Hangi depo - yabanci anahtar
    depo_id = db.Column(db.Integer, db.ForeignKey('depo.id'), nullable=False)
    
    # Hangi lokasyon - yabanci anahtar (opsiyonel)
    lokasyon_id = db.Column(db.Integer, db.ForeignKey('stok_lokasyon.id'))
    
    # Hangi parti - parti takipli urunler icin (EKLENDI)
    parti_id = db.Column(db.Integer, db.ForeignKey('parti.id'), nullable=True)

    # Hareket tipi: giris, cikis, transfer
    hareket_tipi = db.Column(db.String(20), nullable=False)
    
    # Miktar - pozitif sayi
    miktar = db.Column(db.Float, nullable=False)
    
    # Birim fiyat - maliyet icin (opsiyonel)
    birim_fiyat = db.Column(db.Float)
    
    # Referans tipi: siparis, sayim, fire, duzeltme, transfer
    referans_tipi = db.Column(db.String(50))
    
    # Referans ID - ilgili kaydin ID'si
    referans_id = db.Column(db.Integer)
    
    # Islemi yapan kullanici (ileride IK modulune baglanacak)
    kullanici_id = db.Column(db.Integer)
    
    # Islem tarihi - otomatik
    tarih = db.Column(db.String(20), default=lambda: datetime.now().strftime('%d.%m.%Y %H:%M'))
    
    # Aciklama - opsiyonel not
    aciklama = db.Column(db.Text)
    
    # Iliskiler
    urun = db.relationship('Urun', backref='stok_hareketler')
    depo = db.relationship('Depo', backref='stok_hareketler')
    lokasyon = db.relationship('StokLokasyon', backref='stok_hareketler')
    parti = db.relationship('Parti', backref='stok_hareketler')  # EKLENDI
    
    def __repr__(self):
        # Hareket temsil metodu
        return f'<StokHareket {self.hareket_tipi} {self.miktar} {self.urun.urun_adi if self.urun else "Yok"}>'
    
    def to_dict(self):
        # Sozluk formatina cevir
        return {
            'id': self.id,
            'urun_id': self.urun_id,
            'urun_adi': self.urun.urun_adi if self.urun else None,
            'depo_id': self.depo_id,
            'depo_adi': self.depo.depo_adi if self.depo else None,
            'lokasyon_id': self.lokasyon_id,
            'lokasyon_kodu': self.lokasyon.lokasyon_kodu if self.lokasyon else None,
            'hareket_tipi': self.hareket_tipi,
            'miktar': self.miktar,
            'birim_fiyat': self.birim_fiyat,
            'referans_tipi': self.referans_tipi,
            'referans_id': self.referans_id,
            'kullanici_id': self.kullanici_id,
            'tarih': self.tarih,
            'aciklama': self.aciklama
        }
