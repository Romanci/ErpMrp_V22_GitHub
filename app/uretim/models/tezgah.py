# Tezgah ve makine yonetimi
from app import db

class Tezgah(db.Model):
    __tablename__ = 'tezgah'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tezgah_kodu = db.Column(db.String(50), unique=True, nullable=False)
    tezgah_adi = db.Column(db.String(100), nullable=False)
    tezgah_tipi = db.Column(db.String(50))  # CNC, torna, freze, kaynak vb.
    marka = db.Column(db.String(100))                   # EKLENDI
    model = db.Column(db.String(100))                   # EKLENDI
    seri_no = db.Column(db.String(100))                 # EKLENDI
    garanti_bitis = db.Column(db.String(20))            # EKLENDI
    bakim_periyodu_gun = db.Column(db.Integer, default=90)  # EKLENDI: kac gunde bir bakim
    lokasyon = db.Column(db.String(100))
    kapasite = db.Column(db.Float, default=8)  # saat/gun
    verimlilik_orani = db.Column(db.Float, default=100)  # yuzde
    bakim_tarihi = db.Column(db.String(20))
    sonraki_bakim = db.Column(db.String(20))
    durum = db.Column(db.String(20), default='musait')  # musait, calisiyor, bakim, ariza
    aktif = db.Column(db.Integer, default=1)
    
    def __repr__(self):
        return f'<Tezgah {self.tezgah_kodu} - {self.tezgah_adi}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'tezgah_kodu': self.tezgah_kodu,
            'tezgah_adi': self.tezgah_adi,
            'tezgah_tipi': self.tezgah_tipi,
            'durum': self.durum,
            'aktif': self.aktif
        }
