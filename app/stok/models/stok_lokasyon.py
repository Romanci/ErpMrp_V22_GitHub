# Depo icindeki spesifik lokasyonlar - raf, koridor, bolum
from app import db

class StokLokasyon(db.Model):
    # Tablo adi
    __tablename__ = 'stok_lokasyon'
    
    # Birincil anahtar
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Hangi depoda - yabanci anahtar
    depo_id = db.Column(db.Integer, db.ForeignKey('depo.id'), nullable=False)
    
    # Lokasyon kodu - depo icinde benzersiz
    lokasyon_kodu = db.Column(db.String(50), nullable=False)
    
    # Lokasyon adi - aciklama
    lokasyon_adi = db.Column(db.String(100))
    
    # Aktif mi? 0: pasif, 1: aktif
    aktif = db.Column(db.Integer, default=1)
    
    # Depo ile birlikte benzersiz olmali
    __table_args__ = (
        db.UniqueConstraint('depo_id', 'lokasyon_kodu', name='unique_depoda_lokasyon'),
    )
    
    def __repr__(self):
        # Lokasyon temsil metodu
        return f'<StokLokasyon {self.lokasyon_kodu} ({self.depo.depo_kodu if self.depo else "Yok"})>'
    
    def to_dict(self):
        # Sozluk formatina cevir
        return {
            'id': self.id,
            'depo_id': self.depo_id,
            'depo_adi': self.depo.depo_adi if self.depo else None,
            'lokasyon_kodu': self.lokasyon_kodu,
            'lokasyon_adi': self.lokasyon_adi,
            'aktif': self.aktif
        }
