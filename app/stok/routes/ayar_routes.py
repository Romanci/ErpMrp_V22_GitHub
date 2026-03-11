import os
from werkzeug.utils import secure_filename

LOGO_KLASORU  = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'static', 'img')
IZIN_UZANTILAR = {'.png', '.jpg', '.jpeg', '.svg', '.webp'}
from app.kullanici.auth import admin_gerekli
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.stok.models.sistem_ayar import SistemAyar

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
ayar_bp = Blueprint('ayar', __name__, template_folder=template_klasoru)


@ayar_bp.route('/ayarlar', methods=['GET', 'POST'])
@admin_gerekli
def ayarlar():
    if request.method == 'POST':
        ayar_anahtarlari = [
            'firma_adi', 'firma_alt_baslik', 'firma_vergi_no', 'firma_vergi_dairesi',
            'firma_adres', 'firma_telefon', 'firma_email', 'firma_web',
            'kdv_orani', 'para_birimi', 'stok_uyari_gunu', 'bakim_uyari_gunu', 'sayfa_baslik'
        ]
        for anahtar in ayar_anahtarlari:
            deger = request.form.get(anahtar, '')
            SistemAyar.set(anahtar, deger)
        flash('Ayarlar kaydedildi', 'success')
        return redirect(url_for('ayar.ayarlar'))

    ayarlar_dict = {a.anahtar: a.deger for a in SistemAyar.query.all()}
    return render_template('ayarlar.html', ayarlar=ayarlar_dict)


@ayar_bp.route('/ayarlar/logo-yukle', methods=['POST'])
@admin_gerekli
def logo_yukle():
    if 'logo' not in request.files or not request.files['logo'].filename:
        flash('Dosya seçilmedi', 'danger')
        return redirect(url_for('ayar.ayarlar'))

    dosya = request.files['logo']
    uzanti = os.path.splitext(dosya.filename)[1].lower()
    if uzanti not in IZIN_UZANTILAR:
        flash('Sadece PNG, JPG, SVG veya WEBP yükleyebilirsiniz', 'danger')
        return redirect(url_for('ayar.ayarlar'))

    # Eski logoyu sil
    eski = SistemAyar.get('firma_logo', '')
    if eski:
        eski_yol = os.path.join(LOGO_KLASORU, eski)
        if os.path.exists(eski_yol) and not eski_yol.endswith(('logo_sol.png','logo_sag.png','nanmak_HAT.png')):
            try: os.remove(eski_yol)
            except: pass

    dosya_adi = 'firma_logo' + uzanti
    kayit_yolu = os.path.join(LOGO_KLASORU, dosya_adi)
    dosya.save(kayit_yolu)
    SistemAyar.set('firma_logo', dosya_adi, 'Firma logosu')
    flash('✓ Logo yüklendi', 'success')
    return redirect(url_for('ayar.ayarlar'))


@ayar_bp.route('/ayarlar/logo-sil')
@admin_gerekli
def logo_sil():
    mevcut = SistemAyar.get('firma_logo', '')
    if mevcut:
        yol = os.path.join(LOGO_KLASORU, mevcut)
        if os.path.exists(yol) and not mevcut in ('logo_sol.png','logo_sag.png','nanmak_HAT.png'):
            try: os.remove(yol)
            except: pass
    SistemAyar.set('firma_logo', '')
    flash('Logo kaldırıldı', 'info')
    return redirect(url_for('ayar.ayarlar'))
