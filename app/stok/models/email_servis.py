"""
E-posta servisi - sipariş onayı, fatura gönderme, bildirimler
smtplib kullanır (Flask-Mail fallback)
"""
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime
from app import db


class EmailServis:
    """SMTP üzerinden e-posta gönderim servisi"""

    @staticmethod
    def _ayarlari_al():
        """Veritabanından e-posta ayarlarını al"""
        try:
            from app.stok.models.sistem_ayar import SistemAyar
            return {
                'host': SistemAyar.get('smtp_host', ''),
                'port': int(SistemAyar.get('smtp_port', '587')),
                'kullanici': SistemAyar.get('smtp_kullanici', ''),
                'sifre': SistemAyar.get('smtp_sifre', ''),
                'gonderen': SistemAyar.get('smtp_gonderen', ''),
                'firma_adi': SistemAyar.get('firma_adi', 'ERP Sistem'),
                'aktif': SistemAyar.get('smtp_aktif', '0') == '1',
                'tls': SistemAyar.get('smtp_tls', '1') == '1',
            }
        except Exception:
            return {'aktif': False}

    @staticmethod
    def gonder(alici, konu, html_icerik, metin_icerik=None, ekler=None):
        """
        E-posta gönder
        ekler: [(dosya_adi, bytes_data, mime_type), ...]
        """
        ayar = EmailServis._ayarlari_al()
        if not ayar.get('aktif'):
            return False, 'E-posta servisi aktif değil. Ayarlar > E-posta SMTP bölümünü doldurun.'
        if not ayar['host'] or not ayar['kullanici']:
            return False, 'SMTP ayarları eksik'

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = konu
            msg['From'] = f"{ayar['firma_adi']} <{ayar['gonderen'] or ayar['kullanici']}>"
            msg['To'] = alici if isinstance(alici, str) else ', '.join(alici)

            # Metin ve HTML içerik
            if metin_icerik:
                msg.attach(MIMEText(metin_icerik, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_icerik, 'html', 'utf-8'))

            # Ekler
            if ekler:
                for dosya_adi, veri, mime_type in ekler:
                    ana, alt = mime_type.split('/')
                    ek = MIMEBase(ana, alt)
                    ek.set_payload(veri)
                    encoders.encode_base64(ek)
                    ek.add_header('Content-Disposition', f'attachment; filename="{dosya_adi}"')
                    msg.attach(ek)

            # SMTP bağlantısı
            context = ssl.create_default_context()
            if ayar['tls']:
                with smtplib.SMTP(ayar['host'], ayar['port']) as server:
                    server.ehlo()
                    server.starttls(context=context)
                    server.login(ayar['kullanici'], ayar['sifre'])
                    hedefler = [alici] if isinstance(alici, str) else alici
                    server.sendmail(msg['From'], hedefler, msg.as_string())
            else:
                with smtplib.SMTP_SSL(ayar['host'], ayar['port'], context=context) as server:
                    server.login(ayar['kullanici'], ayar['sifre'])
                    hedefler = [alici] if isinstance(alici, str) else alici
                    server.sendmail(msg['From'], hedefler, msg.as_string())

            # Log kaydet
            EmailServis._log_kaydet(alici if isinstance(alici, str) else ', '.join(alici), konu, 'gonderildi')
            return True, 'E-posta gönderildi'

        except smtplib.SMTPAuthenticationError:
            EmailServis._log_kaydet(str(alici), konu, 'hata: kimlik doğrulama')
            return False, 'SMTP kimlik doğrulama hatası. Kullanıcı adı/şifre kontrol edin.'
        except smtplib.SMTPException as e:
            EmailServis._log_kaydet(str(alici), konu, f'hata: {str(e)[:50]}')
            return False, f'SMTP hatası: {str(e)}'
        except Exception as e:
            return False, f'Hata: {str(e)}'

    @staticmethod
    def _log_kaydet(alici, konu, durum):
        """E-posta log kaydı"""
        try:
            log = EmailLog(alici=alici[:200], konu=konu[:200], durum=durum)
            db.session.add(log)
            db.session.commit()
        except Exception:
            pass

    # ── Hazır Şablonlar ─────────────────────────────────────────────

    @staticmethod
    def siparis_onay_gonder(siparis):
        """Tedarikçiye sipariş onayı gönder"""
        if not siparis.tedarikci or not siparis.tedarikci.email:
            return False, 'Tedarikçi e-postası tanımlı değil'

        from app.stok.models.sistem_ayar import SistemAyar
        firma = SistemAyar.get('firma_adi', 'Firma')

        satirlar_html = ''.join([
            f'<tr><td style="padding:6px 10px;border-bottom:1px solid #eee;">{s.urun.urun_adi if s.urun else s.aciklama}</td>'
            f'<td style="padding:6px 10px;border-bottom:1px solid #eee;text-align:right;">{s.miktar} {s.birim}</td>'
            f'<td style="padding:6px 10px;border-bottom:1px solid #eee;text-align:right;">{s.birim_fiyat:.2f} TL</td></tr>'
            for s in siparis.satirlar
        ])

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#1a1a2e;padding:20px;border-radius:8px 8px 0 0;">
                <h2 style="color:#f5c518;margin:0;letter-spacing:2px;">{firma}</h2>
                <p style="color:#94a3b8;margin:4px 0 0;">Satın Alma Sistemi</p>
            </div>
            <div style="padding:24px;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;">
                <h3 style="color:#1e293b;">Sipariş Onayı — {siparis.siparis_no}</h3>
                <p>Sayın <strong>{siparis.tedarikci.unvan}</strong>,</p>
                <p>Aşağıdaki siparişimizi onayınıza sunarız.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;">
                    <tr style="background:#f8fafc;">
                        <th style="padding:8px 10px;text-align:left;font-size:12px;color:#64748b;">ÜRÜN</th>
                        <th style="padding:8px 10px;text-align:right;font-size:12px;color:#64748b;">MİKTAR</th>
                        <th style="padding:8px 10px;text-align:right;font-size:12px;color:#64748b;">BİRİM FİYAT</th>
                    </tr>
                    {satirlar_html}
                </table>
                <p style="font-size:13px;color:#475569;">Sipariş Tarihi: {siparis.siparis_tarihi}<br>
                Teslimat Tarihi: {siparis.teslim_tarihi or '—'}<br>
                Toplam: <strong>{siparis.toplam_tutar:.2f} {siparis.para_birimi}</strong></p>
                <hr style="border:none;border-top:1px solid #e2e8f0;margin:16px 0;">
                <p style="font-size:12px;color:#94a3b8;">Bu e-posta {firma} ERP sistemi tarafından otomatik gönderilmiştir.</p>
            </div>
        </div>"""

        return EmailServis.gonder(
            siparis.tedarikci.email,
            f'Sipariş Onayı — {siparis.siparis_no} — {firma}',
            html
        )

    @staticmethod
    def fatura_gonder(fatura, alici_email):
        """Fatura e-posta ile gönder (PDF eki ile)"""
        from app.stok.models.sistem_ayar import SistemAyar
        firma = SistemAyar.get('firma_adi', 'Firma')

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#1a1a2e;padding:20px;border-radius:8px 8px 0 0;">
                <h2 style="color:#f5c518;margin:0;">{firma}</h2>
            </div>
            <div style="padding:24px;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;">
                <h3>Fatura — {fatura.fatura_no}</h3>
                <p>Sayın <strong>{fatura.musteri_adi or 'Müşteri'}</strong>,</p>
                <p>{fatura.fatura_tarihi} tarihli <strong>{fatura.fatura_no}</strong> numaralı faturanız ekte sunulmaktadır.</p>
                <table style="width:100%;border-collapse:collapse;margin:16px 0;background:#f8fafc;border-radius:6px;overflow:hidden;">
                    <tr><td style="padding:10px 14px;font-size:13px;color:#64748b;">Fatura No</td><td style="padding:10px 14px;font-weight:600;">{fatura.fatura_no}</td></tr>
                    <tr><td style="padding:10px 14px;font-size:13px;color:#64748b;">Tarih</td><td style="padding:10px 14px;">{fatura.fatura_tarihi}</td></tr>
                    <tr><td style="padding:10px 14px;font-size:13px;color:#64748b;">Vade</td><td style="padding:10px 14px;">{fatura.vade_tarihi or '—'}</td></tr>
                    <tr style="background:#fff;"><td style="padding:10px 14px;font-size:13px;color:#64748b;font-weight:700;">TOPLAM</td><td style="padding:10px 14px;font-weight:700;color:#1e293b;font-size:16px;">{fatura.genel_toplam:.2f} {fatura.para_birimi}</td></tr>
                </table>
                <p style="font-size:12px;color:#94a3b8;">Bu e-posta {firma} ERP sistemi tarafından otomatik gönderilmiştir.</p>
            </div>
        </div>"""

        return EmailServis.gonder(
            alici_email,
            f'Fatura — {fatura.fatura_no} — {firma}',
            html
        )

    @staticmethod
    def kritik_stok_bildirimi_gonder(alici, kritik_liste):
        """Kritik stok uyarısı gönder"""
        from app.stok.models.sistem_ayar import SistemAyar
        firma = SistemAyar.get('firma_adi', 'Firma')

        satirlar = ''.join([
            f'<tr><td style="padding:6px 10px;border-bottom:1px solid #eee;">{u["ad"]}</td>'
            f'<td style="padding:6px 10px;border-bottom:1px solid #eee;color:#dc2626;font-weight:600;">{u["miktar"]} {u["birim"]}</td>'
            f'<td style="padding:6px 10px;border-bottom:1px solid #eee;color:#64748b;">{u["min_stok"]}</td></tr>'
            for u in kritik_liste
        ])

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;">
            <div style="background:#1a1a2e;padding:20px;border-radius:8px 8px 0 0;">
                <h2 style="color:#f5c518;margin:0;">{firma}</h2>
            </div>
            <div style="padding:24px;border:1px solid #e2e8f0;border-top:none;border-radius:0 0 8px 8px;">
                <div style="background:#fee2e2;border:1px solid #fca5a5;border-radius:6px;padding:12px 16px;margin-bottom:16px;">
                    <strong style="color:#dc2626;">⚠ Kritik Stok Uyarısı</strong>
                    <p style="margin:4px 0 0;color:#7f1d1d;font-size:13px;">{len(kritik_liste)} ürün minimum stok seviyesinin altına düştü.</p>
                </div>
                <table style="width:100%;border-collapse:collapse;">
                    <tr style="background:#f8fafc;">
                        <th style="padding:8px 10px;text-align:left;font-size:12px;">ÜRÜN</th>
                        <th style="padding:8px 10px;text-align:left;font-size:12px;">MEVCUT</th>
                        <th style="padding:8px 10px;text-align:left;font-size:12px;">MİNİMUM</th>
                    </tr>
                    {satirlar}
                </table>
                <p style="font-size:12px;color:#94a3b8;margin-top:16px;">Bu e-posta {firma} ERP sistemi tarafından otomatik gönderilmiştir.</p>
            </div>
        </div>"""

        return EmailServis.gonder(alici, f'⚠ Kritik Stok Uyarısı — {firma}', html)


class EmailLog(db.Model):
    """Gönderilen e-postaların log kaydı"""
    __tablename__ = 'email_log'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    alici = db.Column(db.String(200))
    konu = db.Column(db.String(200))
    durum = db.Column(db.String(50))
    tarih = db.Column(db.String(30), default=lambda: datetime.now().strftime('%d.%m.%Y %H:%M'))
