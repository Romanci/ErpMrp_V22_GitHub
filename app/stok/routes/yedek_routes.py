"""
Yedekleme ve Geri Yükleme Modülü
- SQLite veritabanı yedeği al (ZIP)
- Yedek listesi görüntüle
- Yedekten geri yükle
- Otomatik yedek (isteğe bağlı)
"""
import os
import io
import shutil
import zipfile
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, jsonify
from app.kullanici.auth import admin_gerekli

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
yedek_bp = Blueprint('yedek', __name__, template_folder=template_klasoru)

YEDEK_KLASORU = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'yedekler')


def _yedek_klasoru_hazirla():
    os.makedirs(YEDEK_KLASORU, exist_ok=True)
    return YEDEK_KLASORU


def _db_yolu():
    """Veritabanı dosya yolunu döndür"""
    from flask import current_app
    uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if uri.startswith('sqlite:///'):
        return uri.replace('sqlite:///', '')
    return None


def _yedek_listesi():
    """Yedek klasöründeki dosyaları listele"""
    klasor = _yedek_klasoru_hazirla()
    dosyalar = []
    for f in sorted(os.listdir(klasor), reverse=True):
        if f.endswith('.zip'):
            tam_yol = os.path.join(klasor, f)
            boyut = os.path.getsize(tam_yol)
            tarih_str = f.replace('yedek_', '').replace('.zip', '')
            try:
                tarih = datetime.strptime(tarih_str, '%Y%m%d_%H%M%S')
                tarih_goster = tarih.strftime('%d.%m.%Y %H:%M:%S')
            except Exception:
                tarih_goster = tarih_str
            dosyalar.append({
                'dosya_adi': f,
                'tam_yol': tam_yol,
                'boyut': boyut,
                'boyut_kb': round(boyut / 1024, 1),
                'tarih': tarih_goster,
            })
    return dosyalar


@yedek_bp.route('/yedekler')
@admin_gerekli
def yedek_panel():
    yedekler = _yedek_listesi()
    return render_template('yedek/yedek_panel.html', yedekler=yedekler)


@yedek_bp.route('/yedek/al', methods=['POST'])
@admin_gerekli
def yedek_al():
    """Anlık yedek oluştur"""
    db_yolu = _db_yolu()
    if not db_yolu or not os.path.exists(db_yolu):
        flash('Veritabanı dosyası bulunamadı', 'danger')
        return redirect(url_for('yedek.yedek_panel'))

    klasor = _yedek_klasoru_hazirla()
    zaman = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_adi = f'yedek_{zaman}.zip'
    zip_yolu = os.path.join(klasor, zip_adi)

    try:
        with zipfile.ZipFile(zip_yolu, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(db_yolu, 'database.db')
            # Meta bilgi
            meta = (
                f"Yedek Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n"
                f"Dosya: {os.path.basename(db_yolu)}\n"
                f"Boyut: {os.path.getsize(db_yolu)} byte\n"
            )
            zf.writestr('yedek_bilgi.txt', meta)

        boyut = round(os.path.getsize(zip_yolu) / 1024, 1)
        flash(f'✓ Yedek alındı: {zip_adi} ({boyut} KB)', 'success')

        # 30'dan fazla yedek varsa en eskiyi sil
        yedekler = _yedek_listesi()
        if len(yedekler) > 30:
            for eski in yedekler[30:]:
                try:
                    os.remove(eski['tam_yol'])
                except Exception:
                    pass
    except Exception as e:
        flash(f'Yedek alınamadı: {str(e)}', 'danger')

    return redirect(url_for('yedek.yedek_panel'))


@yedek_bp.route('/yedek/indir/<dosya_adi>')
@admin_gerekli
def yedek_indir(dosya_adi):
    """Yedek dosyasını indir"""
    # Güvenlik: sadece yedek klasöründeki .zip dosyaları
    if '..' in dosya_adi or '/' in dosya_adi or not dosya_adi.endswith('.zip'):
        flash('Geçersiz dosya adı', 'danger')
        return redirect(url_for('yedek.yedek_panel'))
    tam_yol = os.path.join(YEDEK_KLASORU, dosya_adi)
    if not os.path.exists(tam_yol):
        flash('Dosya bulunamadı', 'danger')
        return redirect(url_for('yedek.yedek_panel'))
    return send_file(tam_yol, as_attachment=True, download_name=dosya_adi)


@yedek_bp.route('/yedek/geri-yukle', methods=['POST'])
@admin_gerekli
def geri_yukle():
    """Yedekten geri yükle"""
    db_yolu = _db_yolu()
    if not db_yolu:
        flash('Veritabanı yolu alınamadı', 'danger')
        return redirect(url_for('yedek.yedek_panel'))

    # Yüklenen dosya
    if 'yedek_dosya' in request.files and request.files['yedek_dosya'].filename:
        dosya = request.files['yedek_dosya']
        if not dosya.filename.endswith('.zip'):
            flash('Sadece .zip yedek dosyası kabul edilir', 'danger')
            return redirect(url_for('yedek.yedek_panel'))

        try:
            # Önce mevcut durumu yedekle
            zaman = datetime.now().strftime('%Y%m%d_%H%M%S')
            klasor = _yedek_klasoru_hazirla()
            onceki_yedek = os.path.join(klasor, f'geri_yukle_oncesi_{zaman}.zip')
            if os.path.exists(db_yolu):
                with zipfile.ZipFile(onceki_yedek, 'w') as zf:
                    zf.write(db_yolu, 'database.db')

            # ZIP'ten veritabanını çıkar
            with zipfile.ZipFile(dosya, 'r') as zf:
                if 'database.db' not in zf.namelist():
                    flash('Geçersiz yedek dosyası (database.db bulunamadı)', 'danger')
                    return redirect(url_for('yedek.yedek_panel'))
                # Geçici dosyaya çıkar, sonra yerleştir
                gecici = db_yolu + '.tmp'
                with zf.open('database.db') as kaynak, open(gecici, 'wb') as hedef:
                    hedef.write(kaynak.read())

            # Mevcut DB'yi yenisiyle değiştir
            os.replace(gecici, db_yolu)
            flash('✓ Geri yükleme başarılı! Sayfayı yenileyin.', 'success')
        except Exception as e:
            flash(f'Geri yükleme hatası: {str(e)}', 'danger')

    # Sistemdeki yedekten geri yükle
    elif request.form.get('secili_yedek'):
        dosya_adi = request.form.get('secili_yedek')
        if '..' in dosya_adi or '/' in dosya_adi:
            flash('Geçersiz dosya', 'danger')
            return redirect(url_for('yedek.yedek_panel'))
        tam_yol = os.path.join(YEDEK_KLASORU, dosya_adi)
        if not os.path.exists(tam_yol):
            flash('Yedek dosyası bulunamadı', 'danger')
            return redirect(url_for('yedek.yedek_panel'))
        try:
            with zipfile.ZipFile(tam_yol, 'r') as zf:
                gecici = db_yolu + '.tmp'
                with zf.open('database.db') as kaynak, open(gecici, 'wb') as hedef:
                    hedef.write(kaynak.read())
            os.replace(gecici, db_yolu)
            flash(f'✓ {dosya_adi} yedeğinden geri yüklendi!', 'success')
        except Exception as e:
            flash(f'Hata: {str(e)}', 'danger')
    else:
        flash('Yedek dosyası seçilmedi', 'warning')

    return redirect(url_for('yedek.yedek_panel'))


@yedek_bp.route('/yedek/sil/<dosya_adi>', methods=['POST'])
@admin_gerekli
def yedek_sil(dosya_adi):
    if '..' in dosya_adi or '/' in dosya_adi:
        flash('Geçersiz dosya adı', 'danger')
        return redirect(url_for('yedek.yedek_panel'))
    tam_yol = os.path.join(YEDEK_KLASORU, dosya_adi)
    try:
        os.remove(tam_yol)
        flash(f'{dosya_adi} silindi', 'success')
    except Exception as e:
        flash(f'Silinemedi: {str(e)}', 'danger')
    return redirect(url_for('yedek.yedek_panel'))


@yedek_bp.route('/api/yedek/otomatik', methods=['POST'])
def otomatik_yedek():
    """Zamanlanmış görev veya cron için endpoint"""
    db_yolu = _db_yolu()
    if not db_yolu or not os.path.exists(db_yolu):
        return jsonify({'basarili': False, 'mesaj': 'DB bulunamadı'})
    try:
        klasor = _yedek_klasoru_hazirla()
        zaman = datetime.now().strftime('%Y%m%d_%H%M%S')
        zip_yolu = os.path.join(klasor, f'yedek_{zaman}.zip')
        with zipfile.ZipFile(zip_yolu, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(db_yolu, 'database.db')
        boyut = round(os.path.getsize(zip_yolu) / 1024, 1)
        # En fazla 30 yedek tut
        yedekler = _yedek_listesi()
        for eski in yedekler[30:]:
            try:
                os.remove(eski['tam_yol'])
            except Exception:
                pass
        return jsonify({'basarili': True, 'dosya': f'yedek_{zaman}.zip', 'boyut_kb': boyut})
    except Exception as e:
        return jsonify({'basarili': False, 'mesaj': str(e)})
