"""ZKTeco TRFace 200 yönetim rotaları"""
import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app.kullanici.auth import admin_gerekli

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
zk_bp = Blueprint('zkteco', __name__, template_folder=template_klasoru)


@zk_bp.route('/zkteco')
@admin_gerekli
def zk_panel():
    from app.stok.models.sistem_ayar import SistemAyar
    from app.ik.models.personel import Devamsizlik
    ayarlar = {
        'ip': SistemAyar.get('zk_ip', '192.168.1.192'),
        'port': SistemAyar.get('zk_port', '4370'),
        'timeout': SistemAyar.get('zk_timeout', '10'),
        'aktif': SistemAyar.get('zk_aktif', '1'),
        'son_senkron': SistemAyar.get('zk_son_senkron', '—'),
        'otomatik_devamsizlik': SistemAyar.get('zk_otomatik_devamsizlik', '1'),
        'calisma_baslangic': SistemAyar.get('zk_calisma_baslangic', '08:00'),
        'calisma_bitis': SistemAyar.get('zk_calisma_bitis', '17:00'),
        'gec_tolerans': SistemAyar.get('zk_gec_kalma_tolerans', '15'),
    }
    # Son 20 devamsızlık (ZKTeco kaynaklı)
    son_kayitlar = Devamsizlik.query.filter(
        Devamsizlik.aciklama.like('%ZKTeco%')
    ).order_by(Devamsizlik.id.desc()).limit(20).all()

    return render_template('ik/zkteco_panel.html', ayarlar=ayarlar, son_kayitlar=son_kayitlar)


@zk_bp.route('/zkteco/ayarlar', methods=['POST'])
@admin_gerekli
def zk_ayarlar_kaydet():
    from app.stok.models.sistem_ayar import SistemAyar
    for anahtar in ['zk_ip', 'zk_port', 'zk_timeout', 'zk_aktif',
                    'zk_otomatik_devamsizlik', 'zk_calisma_baslangic',
                    'zk_calisma_bitis', 'zk_gec_kalma_tolerans']:
        form_key = anahtar.replace('zk_', '')
        deger = request.form.get(form_key, '')
        # Checkbox'lar
        if anahtar in ('zk_aktif', 'zk_otomatik_devamsizlik'):
            deger = '1' if request.form.get(form_key) else '0'
        if deger:
            SistemAyar.set(anahtar, deger)
    from app import db
    db.session.commit()
    flash('ZKTeco ayarları kaydedildi', 'success')
    return redirect(url_for('zkteco.zk_panel'))


@zk_bp.route('/api/zkteco/baglan-test')
@admin_gerekli
def api_baglan_test():
    """Cihaz bağlantı testi ve bilgi al"""
    from app.ik.models.zkteco import cihaz_bilgisi_al, zk_baglanabilir_mi
    # Önce TCP kontrolü
    if not zk_baglanabilir_mi():
        return jsonify({
            'basarili': False,
            'mesaj': 'Cihaza ulaşılamıyor. IP/Port kontrol edin veya cihazın açık olduğundan emin olun.'
        })
    bilgi = cihaz_bilgisi_al()
    if bilgi.get('bagli'):
        return jsonify({
            'basarili': True,
            'mesaj': 'Bağlantı başarılı',
            'bilgi': bilgi,
        })
    else:
        return jsonify({'basarili': False, 'mesaj': bilgi.get('hata', 'Bilinmeyen hata')})


@zk_bp.route('/api/zkteco/senkronize', methods=['POST'])
@admin_gerekli
def api_senkronize():
    """Manuel senkronizasyon"""
    from app.ik.models.zkteco import senkronize_et
    gun = request.json.get('gun', 7) if request.is_json else int(request.form.get('gun', 7))
    baslangic = datetime.now() - timedelta(days=gun)
    sonuc = senkronize_et(baslangic_tarihi=baslangic)
    return jsonify(sonuc)


@zk_bp.route('/api/zkteco/kullanicilar')
@admin_gerekli
def api_kullanicilar():
    """Cihazdaki kullanıcı listesi"""
    from app.ik.models.zkteco import cihaz_kullanicilari_al
    from app.ik.models.personel import Personel
    kullanicilar = cihaz_kullanicilari_al()
    # ERP personelleriyle eşleştir
    for k in kullanicilar:
        p = Personel.query.filter_by(sicil_no=str(k['user_id']), aktif=1).first()
        k['erp_personel'] = p.tam_ad if p else None
        k['eslesti'] = p is not None
    return jsonify({'kullanicilar': kullanicilar, 'toplam': len(kullanicilar)})


@zk_bp.route('/api/zkteco/personel-yukle/<int:personel_id>', methods=['POST'])
@admin_gerekli
def api_personel_yukle(personel_id):
    """Personeli cihaza yükle"""
    from app.ik.models.zkteco import personel_cihaza_yukle
    from app.ik.models.personel import Personel
    p = Personel.query.get_or_404(personel_id)
    basarili, mesaj = personel_cihaza_yukle(p)
    return jsonify({'basarili': basarili, 'mesaj': mesaj})


@zk_bp.route('/api/zkteco/saat-ayarla', methods=['POST'])
@admin_gerekli
def api_saat_ayarla():
    """Cihaz saatini sunucu saatiyle senkronize et"""
    from app.ik.models.zkteco import cihaz_saatini_ayarla
    basarili, mesaj = cihaz_saatini_ayarla()
    return jsonify({'basarili': basarili, 'mesaj': mesaj})


@zk_bp.route('/api/zkteco/ham-loglar')
@admin_gerekli
def api_ham_loglar():
    """Son N günün ham giriş/çıkış loglarını göster"""
    from app.ik.models.zkteco import zk_baglanti_ac, zk_baglanabilir_mi
    from app.ik.models.personel import Personel
    gun = request.args.get('gun', 1, type=int)
    baslangic = datetime.now() - timedelta(days=gun)

    if not zk_baglanabilir_mi():
        return jsonify({'basarili': False, 'mesaj': 'Cihaza ulaşılamıyor'})

    try:
        zk = zk_baglanti_ac()
        conn = zk.connect()
        try:
            attendance = conn.get_attendance()
        finally:
            conn.disconnect()

        kayitlar = []
        for a in attendance:
            if a.timestamp >= baslangic:
                p = Personel.query.filter_by(sicil_no=str(a.user_id), aktif=1).first()
                kayitlar.append({
                    'user_id': a.user_id,
                    'timestamp': a.timestamp.strftime('%d.%m.%Y %H:%M:%S'),
                    'status': a.status,
                    'punch': a.punch,
                    'personel': p.tam_ad if p else f'ID:{a.user_id} (ERP\'de yok)',
                    'eslesti': p is not None,
                })
        kayitlar.sort(key=lambda x: x['timestamp'], reverse=True)
        return jsonify({'basarili': True, 'kayitlar': kayitlar[:200], 'toplam': len(kayitlar)})
    except Exception as e:
        return jsonify({'basarili': False, 'mesaj': str(e)})
