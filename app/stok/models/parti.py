# Parti ve seri numarasi takibi - izlenebilirlik icin
from app import db

class Parti(db.Model):
    # Tablo adi
    __tablename__ = 'parti'
    
    # Birincil anahtar
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    # Hangi urune ait - yabanci anahtar
    urun_id = db.Column(db.Integer, db.ForeignKey('urun.id'), nullable=False)
    
    # Parti kodu - urun bazinda benzersiz olmali
    parti_kodu = db.Column(db.String(50), nullable=False)
    
    # Uretim tarihi - opsiyonel
    uretim_tarihi = db.Column(db.String(20))
    
    # Son kullanma tarihi - kritik (ozellikle gida sektoru icin)
    son_kullanma_tarihi = db.Column(db.String(20))
    
    # Mevcut miktar - stokta ne kadar kaldi
    miktar = db.Column(db.Float, default=0)
    
    # Hangi depoda - yabanci anahtar
    depo_id = db.Column(db.Integer, db.ForeignKey('depo.id'))
    
    # Aktif mi? 0: pasif, 1: aktif
    aktif = db.Column(db.Integer, default=1)
    
    # Urun ve depo ile birlikte benzersiz parti kodu
    __table_args__ = (
        db.UniqueConstraint('urun_id', 'parti_kodu', name='unique_urun_parti'),
    )
    
    # Iliskiler
    urun = db.relationship('Urun', backref='partiler')
    depo = db.relationship('Depo', backref='partiler')
    
    def __repr__(self):
        # Parti temsil metodu
        return f'<Parti {self.parti_kodu} - {self.urun.urun_adi if self.urun else "Yok"}>'
    
    def to_dict(self):
        # Sozluk formatina cevir
        return {
            'id': self.id,
            'urun_id': self.urun_id,
            'urun_adi': self.urun.urun_adi if self.urun else None,
            'parti_kodu': self.parti_kodu,
            'uretim_tarihi': self.uretim_tarihi,
            'son_kullanma_tarihi': self.son_kullanma_tarihi,
            'miktar': self.miktar,
            'depo_id': self.depo_id,
            'depo_adi': self.depo.depo_adi if self.depo else None,
            'aktif': self.aktif
        }
    
    def skt_durumu(self):
        # Son kullanma tarihi gecti mi kontrolu
        from datetime import datetime
        if not self.son_kullanma_tarihi:
            return 'Bilinmiyor'
        try:
            skt = datetime.strptime(self.son_kullanma_tarihi, '%d.%m.%Y')
            bugun = datetime.now()
            if skt < bugun:
                return 'Gecti'
            elif (skt - bugun).days <= 30:
                return 'Yaklasiyor'
            else:
                return 'Gecerli'
        except:
            return 'Hata'
