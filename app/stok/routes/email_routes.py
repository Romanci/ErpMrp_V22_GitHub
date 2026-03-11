import os
from app.kullanici.auth import admin_gerekli
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.stok.models.sistem_ayar import SistemAyar
from app.stok.models.email_servis import EmailServis, EmailLog

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
email_bp = Blueprint('email', __name__, template_folder=template_klasoru)


@email_bp.route('/ayarlar/email', methods=['GET', 'POST'])
@admin_gerekli
def email_ayarlar():
    """SMTP ayar sayfası"""
    if request.method == 'POST':
        alanlar = ['smtp_aktif', 'smtp_host', 'smtp_port', 'smtp_kullanici',
                   'smtp_sifre', 'smtp_gonderen', 'smtp_tls', 'bildirim_email']
        for alan in alanlar:
            deger = request.form.get(alan, '0' if alan in ['smtp_aktif', 'smtp_tls'] else '')
            SistemAyar.set(alan, deger)
        flash('E-posta ayarları kaydedildi', 'success')
        return redirect(url_for('email.email_ayarlar'))

    ayarlar = {a.anahtar: a.deger for a in SistemAyar.query.all()}
    loglar = EmailLog.query.order_by(EmailLog.id.desc()).limit(20).all()
    return render_template('email/email_ayarlar.html', ayarlar=ayarlar, loglar=loglar)


@email_bp.route('/api/email-test', methods=['POST'])
def email_test():
    """Test e-postası gönder"""
    test_alici = request.json.get('alici', '')
    if not test_alici:
        return jsonify({'basarili': False, 'mesaj': 'Alıcı adresi gerekli'})

    from app.stok.models.sistem_ayar import SistemAyar
    firma = SistemAyar.get('firma_adi', 'ERP')
    html = f"""<div style="font-family:Arial;padding:20px;">
        <h3 style="color:#1a1a2e;">Test E-postası — {firma}</h3>
        <p>Bu bir test e-postasıdır. SMTP ayarlarınız doğru çalışıyor!</p>
        <p style="font-size:12px;color:#94a3b8;">Gönderim zamanı: {__import__('datetime').datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
    </div>"""

    ok, mesaj = EmailServis.gonder(test_alici, f'Test E-postası — {firma}', html)
    return jsonify({'basarili': ok, 'mesaj': mesaj})


@email_bp.route('/api/siparis-email/<int:id>', methods=['POST'])
def siparis_email_gonder(id):
    """Sipariş onayını e-posta ile gönder"""
    from app.satin_alma.models import SatinAlmaSiparisi
    siparis = SatinAlmaSiparisi.query.get_or_404(id)
    ok, mesaj = EmailServis.siparis_onay_gonder(siparis)
    if ok:
        flash('Sipariş onayı e-posta ile gönderildi', 'success')
    else:
        flash(f'E-posta gönderilemedi: {mesaj}', 'danger')
    return redirect(url_for('siparis.siparis_detay', id=id))


@email_bp.route('/api/fatura-email/<int:id>', methods=['POST'])
def fatura_email_gonder(id):
    """Faturayı e-posta ile gönder"""
    from app.fatura.models.fatura import Fatura
    fatura = Fatura.query.get_or_404(id)
    alici = request.form.get('alici_email', '')
    if not alici:
        flash('Alıcı e-posta adresi gerekli', 'danger')
        return redirect(url_for('fatura.fatura_detay', id=id))
    ok, mesaj = EmailServis.fatura_gonder(fatura, alici)
    if ok:
        flash('Fatura e-posta ile gönderildi', 'success')
    else:
        flash(f'E-posta gönderilemedi: {mesaj}', 'danger')
    return redirect(url_for('fatura.fatura_detay', id=id))


@email_bp.route('/api/kritik-stok-email', methods=['POST'])
def kritik_stok_email():
    """Kritik stok bildirimini e-posta ile gönder"""
    from app import db
    from app.stok.models import Urun, StokHareket
    from sqlalchemy import func

    bildirim_email = SistemAyar.get('bildirim_email', '')
    if not bildirim_email:
        return jsonify({'basarili': False, 'mesaj': 'Bildirim e-postası ayarlanmamış'})

    urunler = Urun.query.filter_by(aktif=1).all()
    kritikler = []
    for u in urunler:
        if u.min_stok <= 0:
            continue
        giris = db.session.query(func.sum(StokHareket.miktar)).filter(
            StokHareket.urun_id == u.id, StokHareket.hareket_tipi == 'giris'
        ).scalar() or 0
        cikis = db.session.query(func.sum(StokHareket.miktar)).filter(
            StokHareket.urun_id == u.id, StokHareket.hareket_tipi == 'cikis'
        ).scalar() or 0
        mevcut = giris - cikis
        if mevcut <= u.min_stok:
            kritikler.append({'ad': u.urun_adi, 'miktar': round(mevcut, 2), 'birim': u.birim, 'min_stok': u.min_stok})

    if not kritikler:
        return jsonify({'basarili': True, 'mesaj': 'Kritik stok yok, e-posta gönderilmedi'})

    ok, mesaj = EmailServis.kritik_stok_bildirimi_gonder(bildirim_email, kritikler)
    return jsonify({'basarili': ok, 'mesaj': mesaj})
