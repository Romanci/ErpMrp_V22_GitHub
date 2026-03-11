# Satin alma siparisi modeli
from app import db
from datetime import datetime

class SatinAlmaSiparisi(db.Model):
    __tablename__ = 'satin_alma_siparisi'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    siparis_no = db.Column(db.String(50), unique=True, nullable=False)
    tedarikci_id = db.Column(db.Integer, db.ForeignKey('tedarikci.id'), nullable=False)
    siparis_tarihi = db.Column(db.String(20), default=lambda: datetime.now().strftime('%d.%m.%Y'))
    teslim_tarihi = db.Column(db.String(20))
    durum = db.Column(db.String(20), default='acik')  # acik, kismi, tamamlandi, iptal
    para_birimi = db.Column(db.String(10), default='TL')
    toplam_tutar = db.Column(db.Float, default=0)
    onaylayan_kullanici_id = db.Column(db.Integer, nullable=True)   # EKLENDI
    onay_tarihi = db.Column(db.String(20), nullable=True)           # EKLENDI
    aciklama = db.Column(db.Text)
    aktif = db.Column(db.Integer, default=1)
    
    # Iliskiler
    satirlar = db.relationship('SatinAlmaSiparisiSatir', backref='siparis', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<SatinAlmaSiparisi {self.siparis_no}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'siparis_no': self.siparis_no,
            'tedarikci_id': self.tedarikci_id,
            'tedarikci_unvan': self.tedarikci.unvan if self.tedarikci else None,
            'siparis_tarihi': self.siparis_tarihi,
            'teslim_tarihi': self.teslim_tarihi,
            'durum': self.durum,
            'para_birimi': self.para_birimi,
            'toplam_tutar': self.toplam_tutar,
            'aktif': self.aktif
        }

class SatinAlmaSiparisiSatir(db.Model):
    __tablename__ = 'satin_alma_siparisi_satir'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    siparis_id = db.Column(db.Integer, db.ForeignKey('satin_alma_siparisi.id'), nullable=False)
    urun_id = db.Column(db.Integer, db.ForeignKey('urun.id'), nullable=False)
    miktar = db.Column(db.Float, nullable=False)
    birim_fiyat = db.Column(db.Float, nullable=False)
    indirim_orani = db.Column(db.Float, default=0)
    kdv_orani = db.Column(db.Float, default=18)
    teslim_edilen_miktar = db.Column(db.Float, default=0)
    aciklama = db.Column(db.Text)
    
    # Iliskiler
    urun = db.relationship('Urun', backref='siparis_satirlari')
    
    def hesapla_tutar(self):
        # DUZELTME: toplam_tutar kolonu ile isim catismasini onlemek icin yeniden adlandirildi
        ara_toplam = self.miktar * self.birim_fiyat
        indirim = ara_toplam * (self.indirim_orani / 100)
        kdv = (ara_toplam - indirim) * (self.kdv_orani / 100)
        return ara_toplam - indirim + kdv

    def to_dict(self):
        return {
            'id': self.id,
            'siparis_id': self.siparis_id,
            'urun_id': self.urun_id,
            'urun_adi': self.urun.urun_adi if self.urun else None,
            'miktar': self.miktar,
            'birim_fiyat': self.birim_fiyat,
            'indirim_orani': self.indirim_orani,
            'kdv_orani': self.kdv_orani,
            'teslim_edilen_miktar': self.teslim_edilen_miktar,
            'hesaplanan_tutar': self.hesapla_tutar()
        }
    
    def __repr__(self):
        return f'<SatinAlmaSiparisiSatir {self.id} - {self.miktar} adet>'
