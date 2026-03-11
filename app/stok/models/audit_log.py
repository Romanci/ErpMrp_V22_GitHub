"""
Audit Log - Kim ne zaman ne yaptı
Sistemdeki tüm önemli işlemleri kaydeder
"""
from app import db
from datetime import datetime


class AuditLog(db.Model):
    __tablename__ = 'audit_log'

    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    tarih           = db.Column(db.String(20), default=lambda: datetime.now().strftime('%d.%m.%Y %H:%M:%S'))
    kullanici_id    = db.Column(db.Integer, db.ForeignKey('kullanici.id'), nullable=True)
    kullanici_adi   = db.Column(db.String(50))        # Silinen kullanıcılar için
    islem           = db.Column(db.String(30))         # giris|cikis|ekle|duzenle|sil|goruntule
    modul           = db.Column(db.String(30))         # stok|fatura|crm|uretim vb.
    kayit_id        = db.Column(db.Integer)            # İşlem yapılan kaydın ID'si
    kayit_adi       = db.Column(db.String(200))        # Okunabilir açıklama (Ürün: Vida M8)
    detay           = db.Column(db.Text)               # JSON: eski_deger → yeni_deger
    ip_adresi       = db.Column(db.String(45))
    sonuc           = db.Column(db.String(10), default='basarili')  # basarili|hata

    kullanici       = db.relationship('Kullanici', foreign_keys=[kullanici_id], backref='islemler')


def log_kaydet(islem, modul, kayit_adi='', kayit_id=None, detay='', sonuc='basarili'):
    """Audit log kaydı oluştur — her yerden çağrılabilir"""
    try:
        from flask import session, request
        kullanici_id  = session.get('kullanici_id')
        kullanici_adi = session.get('kullanici_adi', 'sistem')
        ip            = request.remote_addr if request else '—'

        log = AuditLog(
            kullanici_id  = kullanici_id,
            kullanici_adi = kullanici_adi,
            islem         = islem,
            modul         = modul,
            kayit_id      = kayit_id,
            kayit_adi     = kayit_adi[:200] if kayit_adi else '',
            detay         = str(detay)[:500] if detay else '',
            ip_adresi     = ip,
            sonuc         = sonuc,
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        pass  # Log hatası ana işlemi durdurmasın
