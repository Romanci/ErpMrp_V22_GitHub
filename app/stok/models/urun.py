# Urun karti modeli - tum urunlerin temel bilgileri
from app import db
from datetime import datetime

class Urun(db.Model):
    # Tablo adi
    __tablename__ = 'urun'
    
    # Birincil anahtar - otomatik artan sayi
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Stok kodu - benzersiz ve zorunlu
    stok_kodu = db.Column(db.String(50), unique=True, nullable=False)
    
    # Barkod - opsiyonel
    barkod = db.Column(db.String(50))
    
    # Urun adi - zorunlu
    urun_adi = db.Column(db.String(200), nullable=False)
    
    # Birim: adet, kg, mt, koli vb.
    birim = db.Column(db.String(20), nullable=False)
    
    # Kategori baglantisi - yabanci anahtar
    kategori_id = db.Column(db.Integer, db.ForeignKey('kategori.id'))
    
    # Minimum stok seviyesi - varsayilan 0
    min_stok = db.Column(db.Float, default=0)
    
    # Maksimum stok seviyesi - varsayilan 0 (sinirsiz)
    max_stok = db.Column(db.Float, default=0)
    
    # Parti takibi yapilsin mi? 0: hayir, 1: evet
    parti_takibi = db.Column(db.Integer, default=0)
    
    # Aktif mi? 0: pasif, 1: aktif
    aktif = db.Column(db.Integer, default=1)
    
    # Alis fiyati - maliyet hesaplama icin
    alis_fiyati = db.Column(db.Float, default=0)

    # Satis fiyati
    satis_fiyati = db.Column(db.Float, default=0)

    # KDV orani (%)
    kdv_orani = db.Column(db.Float, default=18)

    # Varsayilan tedarikci - yabanci anahtar (opsiyonel)
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikci.id'), nullable=True)

    # Olusturma tarihi - otomatik
    olusturma_tarihi = db.Column(db.String(20), default=lambda: datetime.now().strftime('%d.%m.%Y'))

    # Kategori ile iliski - ters yon
    kategori = db.relationship('Kategori', backref='urunler')

    # Varsayilan tedarikci ile iliski
    tedarikci = db.relationship('Tedarikci', backref='urunler', foreign_keys=[tedarikci_id])
    
    def __repr__(self):
        # Urun temsil metodu
        return f'<Urun {self.stok_kodu} - {self.urun_adi}>'
    
    def to_dict(self):
        # Sozluk formatina cevir (JSON icin)
        return {
            'id': self.id,
            'stok_kodu': self.stok_kodu,
            'barkod': self.barkod,
            'urun_adi': self.urun_adi,
            'birim': self.birim,
            'kategori_id': self.kategori_id,
            'min_stok': self.min_stok,
            'max_stok': self.max_stok,
            'alis_fiyati': self.alis_fiyati,
            'satis_fiyati': self.satis_fiyati,
            'kdv_orani': self.kdv_orani,
            'tedarikci_id': self.tedarikci_id,
            'parti_takibi': self.parti_takibi,
            'aktif': self.aktif,
            'olusturma_tarihi': self.olusturma_tarihi
        }
