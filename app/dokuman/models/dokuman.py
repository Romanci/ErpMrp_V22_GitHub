# Doküman Yönetim Sistemi modelleri
from app import db
from datetime import datetime

def _simdi():
    return datetime.now().strftime('%d.%m.%Y')

KATEGORILER = [
    ('personel',   'Personel Belgeleri'),
    ('urun',       'Ürün Teknik / SDS'),
    ('kalite',     'Kalite Sertifikaları'),
    ('arac',       'Araç / Bakım'),
    ('genel',      'Genel Firma'),
    ('kys',        'Kalite Yönetim Sistemi'),
    ('el_kitabi',  'Kalite El Kitabı'),
    ('resmi',      'Resmi Evraklar'),
]

class Dokuman(db.Model):
    __tablename__ = 'dokuman'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    baslik = db.Column(db.String(200), nullable=False)
    kategori = db.Column(db.String(50), nullable=False)
    revizyon = db.Column(db.String(20), default='1.0')
    aciklama = db.Column(db.Text)
    dosya_adi = db.Column(db.String(200))
    dosya_boyut = db.Column(db.Integer, default=0)  # byte
    dosya_tur = db.Column(db.String(50))  # pdf, docx, xlsx...
    # Bağlantılar (opsiyonel)
    personel_id = db.Column(db.Integer, db.ForeignKey('personel.id'), nullable=True)
    urun_id = db.Column(db.Integer, db.ForeignKey('urun.id'), nullable=True)
    # Geçerlilik
    gecerlilik_tarihi = db.Column(db.String(20))
    # Meta
    yukleven_id = db.Column(db.Integer, nullable=True)
    etiketler = db.Column(db.String(200))
    gizli = db.Column(db.Integer, default=0)
    aktif = db.Column(db.Integer, default=1)
    olusturma_tarihi = db.Column(db.String(20), default=_simdi)
    guncelleme_tarihi = db.Column(db.String(20), default=_simdi)

    personel = db.relationship('Personel', foreign_keys=[personel_id],
                               backref=db.backref('dokumanlar', lazy=True))
    urun = db.relationship('Urun', foreign_keys=[urun_id])

    @property
    def boyut_str(self):
        b = self.dosya_boyut or 0
        if b < 1024: return f'{b} B'
        if b < 1024**2: return f'{b/1024:.1f} KB'
        return f'{b/1024**2:.1f} MB'

    @property
    def suresi_dolacak_mi(self):
        if not self.gecerlilik_tarihi: return False
        try:
            from datetime import timedelta
            g = datetime.strptime(self.gecerlilik_tarihi, '%d.%m.%Y')
            return (g - datetime.now()).days <= 30
        except: return False
