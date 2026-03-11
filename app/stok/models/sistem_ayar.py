from app import db
from datetime import datetime


class SistemAyar(db.Model):
    """Firma ve sistem ayarlari - key/value deposu"""
    __tablename__ = 'sistem_ayar'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    anahtar = db.Column(db.String(100), unique=True, nullable=False)
    deger = db.Column(db.Text)
    aciklama = db.Column(db.String(200))
    guncelleme = db.Column(db.String(30), default=lambda: datetime.now().strftime('%d.%m.%Y %H:%M'))

    @staticmethod
    def get(anahtar, varsayilan=''):
        """Ayar degerini getir"""
        ayar = SistemAyar.query.filter_by(anahtar=anahtar).first()
        return ayar.deger if ayar else varsayilan

    @staticmethod
    def set(anahtar, deger, aciklama=None):
        """Ayar degerini kaydet/guncelle"""
        ayar = SistemAyar.query.filter_by(anahtar=anahtar).first()
        if ayar:
            ayar.deger = deger
            ayar.guncelleme = datetime.now().strftime('%d.%m.%Y %H:%M')
        else:
            ayar = SistemAyar(anahtar=anahtar, deger=deger, aciklama=aciklama)
            db.session.add(ayar)
        db.session.commit()
        return ayar

    @staticmethod
    def varsayilanlari_olustur():
        """Ilk calistirmada varsayilan ayarlari ekle"""
        varsayilanlar = [
            ('firma_adi', 'NANMAK', 'Firma adı (header\'da görünür)'),
            ('firma_logo', '', 'Logo dosyası (static/img/ altına yükleyin, sadece dosya adı: logo.png)'),
            ('firma_alt_baslik', 'Yönetim Sistemi', 'Header alt yazısı'),
            ('firma_vergi_no', '', 'Vergi numarası'),
            ('firma_vergi_dairesi', '', 'Vergi dairesi'),
            ('firma_adres', '', 'Firma adresi'),
            ('firma_telefon', '', 'Firma telefonu'),
            ('firma_email', '', 'Firma e-postası'),
            ('firma_web', '', 'Web sitesi'),
            ('kdv_orani', '18', 'Varsayılan KDV oranı (%)'),
            ('para_birimi', 'TL', 'Varsayılan para birimi'),
            ('stok_uyari_gunu', '7', 'SKT uyarı süresi (gün)'),
            ('bakim_uyari_gunu', '7', 'Bakım uyarı süresi (gün)'),
            ('sayfa_baslik', 'NANMAK ERP', 'Tarayıcı sekme başlığı'),
            ('smtp_aktif', '0', 'E-posta servisi aktif mi (0/1)'),
            ('smtp_host', '', 'SMTP sunucu adresi (örn: smtp.gmail.com)'),
            ('smtp_port', '587', 'SMTP port (587=TLS, 465=SSL)'),
            ('smtp_kullanici', '', 'SMTP kullanıcı adı (e-posta adresi)'),
            ('smtp_sifre', '', 'SMTP şifre veya uygulama şifresi'),
            ('smtp_gonderen', '', 'Gönderen e-posta (boşsa kullanıcı adı kullanılır)'),
            ('smtp_tls', '1', 'TLS kullan (1=evet, 0=SSL)'),
            ('bildirim_email', '', 'Sistem bildirimlerinin gönderileceği e-posta'),
        ]
        for anahtar, deger, aciklama in varsayilanlar:
            if not SistemAyar.query.filter_by(anahtar=anahtar).first():
                db.session.add(SistemAyar(anahtar=anahtar, deger=deger, aciklama=aciklama))
        db.session.commit()
