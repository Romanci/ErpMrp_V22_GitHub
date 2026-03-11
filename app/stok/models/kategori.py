# Urun kategorisi modeli - hiyerarsik kategori yapisi
from app import db

class Kategori(db.Model):
    # Tablo adi
    __tablename__ = 'kategori'
    
    # Birincil anahtar
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Kategori adi - zorunlu
    kategori_adi = db.Column(db.String(100), nullable=False)
    
    # Ust kategori baglantisi - yabanci anahtar (null olabilir)
    ust_kategori_id = db.Column(db.Integer, db.ForeignKey('kategori.id'), nullable=True)
    
    # Ust kategori ile iliski - ters yon (alt kategoriler icin)
    alt_kategoriler = db.relationship('Kategori', backref=db.backref('ust_kategori', remote_side=[id]))
    
    def __repr__(self):
        # Kategori temsil metodu
        return f'<Kategori {self.kategori_adi}>'
    
    def to_dict(self):
        # Sozluk formatina cevir
        return {
            'id': self.id,
            'kategori_adi': self.kategori_adi,
            'ust_kategori_id': self.ust_kategori_id
        }
    
    def tam_yol(self):
        # Ust kategorileri dahil tam kategori adi
        if self.ust_kategori:
            return f"{self.ust_kategori.tam_yol()} > {self.kategori_adi}"
        return self.kategori_adi
