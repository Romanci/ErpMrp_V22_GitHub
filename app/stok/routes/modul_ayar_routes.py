"""Admin - Modül Yönetim Paneli"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app.kullanici.auth import admin_gerekli
import os

modul_ayar_bp = Blueprint('modul_ayar', __name__,
    template_folder=os.path.join(os.path.dirname(__file__), '..', 'templates'))

MODUL_BILGI = {
    'stok':       {'ad': 'Stok Yönetimi',      'ikon': 'fa-boxes',         'zorunlu': True},
    'satin_alma': {'ad': 'Satın Alma',          'ikon': 'fa-shopping-cart', 'zorunlu': False},
    'uretim':     {'ad': 'Üretim / MRP',        'ikon': 'fa-industry',      'zorunlu': False},
    'fatura':     {'ad': 'Fatura',              'ikon': 'fa-file-invoice',  'zorunlu': False},
    'ik':         {'ad': 'İnsan Kaynakları',    'ikon': 'fa-users',         'zorunlu': False},
    'bakim':      {'ad': 'Bakım Yönetimi',      'ikon': 'fa-tools',         'zorunlu': False},
    'crm':        {'ad': 'Müşteri / CRM',       'ikon': 'fa-handshake',     'zorunlu': False},
    'kalite':     {'ad': 'Kalite Kontrol',      'ikon': 'fa-clipboard-check','zorunlu': False},
    'dokuman':    {'ad': 'Doküman Yönetimi',    'ikon': 'fa-folder-open',   'zorunlu': False},
    'arac':       {'ad': 'Araç / Ekipman',      'ikon': 'fa-truck',         'zorunlu': False},
    'vardiya':    {'ad': 'Vardiya Yönetimi',    'ikon': 'fa-clock',         'zorunlu': False},
    'muhasebe':   {'ad': 'Muhasebe',            'ikon': 'fa-calculator',    'zorunlu': False},
}


@modul_ayar_bp.route('/moduller')
@admin_gerekli
def modul_panel():
    from app.modul_yonetici import modul_durumları
    durumlar = modul_durumları()
    import os
    profil_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(__file__)))), 'kurulum_profilleri')
    profiller = []
    if os.path.isdir(profil_dir):
        import json
        for f in os.listdir(profil_dir):
            if f.endswith('.json'):
                try:
                    with open(os.path.join(profil_dir, f)) as fp:
                        p = json.load(fp)
                        profiller.append({'dosya': f, 'ad': p.get('profil_adi', f),
                                         'aciklama': p.get('aciklama', '')})
                except Exception:
                    pass
    return render_template('stok/modul_panel.html',
        modul_bilgi=MODUL_BILGI, durumlar=durumlar, profiller=profiller)


@modul_ayar_bp.route('/moduller/kaydet', methods=['POST'])
@admin_gerekli
def modul_kaydet():
    from app.modul_yonetici import modul_kaydet as _kaydet, modul_durumları
    durumlar = modul_durumları()
    for modul_adi, bilgi in MODUL_BILGI.items():
        if bilgi['zorunlu']:
            continue
        aktif = bool(request.form.get(modul_adi))
        _kaydet(modul_adi, aktif)
    flash('Modül ayarları kaydedildi. Değişikliklerin geçerli olması için sunucuyu yeniden başlatın.', 'success')
    return redirect(url_for('modul_ayar.modul_panel'))


@modul_ayar_bp.route('/moduller/profil-uygula', methods=['POST'])
@admin_gerekli
def profil_uygula():
    from app.modul_yonetici import profil_uygula as _uygula
    import os
    dosya = request.form.get('profil_dosya', '')
    if not dosya or '/' in dosya or '\\' in dosya:
        flash('Geçersiz profil', 'danger')
        return redirect(url_for('modul_ayar.modul_panel'))
    profil_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
        os.path.dirname(__file__)))), 'kurulum_profilleri')
    tam_yol = os.path.join(profil_dir, dosya)
    if not os.path.exists(tam_yol):
        flash('Profil dosyası bulunamadı', 'danger')
        return redirect(url_for('modul_ayar.modul_panel'))
    ad = _uygula(tam_yol)
    flash(f'"{ad}" profili uygulandı. Sunucuyu yeniden başlatın.', 'success')
    return redirect(url_for('modul_ayar.modul_panel'))
