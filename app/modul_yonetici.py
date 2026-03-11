"""
Modül Yönetim Sistemi v2
-------------------------
moduller.json (yeni yapı) dosyasından aktif modülleri okur.
Geriye uyumlu — eski düz format da desteklenir.
"""
import json
import os

_MODUL_DOSYA = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'moduller.json')

_VARSAYILAN = {
    'stok': True, 'kullanici': True, 'satin_alma': True, 'uretim': True,
    'fatura': True, 'ik': True, 'bakim': True, 'crm': True, 'kalite': True,
    'dokuman': True, 'arac': True, 'vardiya': True,
    'muhasebe': True, 'proje': True, 'siparis': True,
}


def modul_durumları():
    """moduller.json oku — hem yeni (moduller:{}) hem eski (düz) formatı destekler"""
    try:
        with open(_MODUL_DOSYA, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Yeni format: {"moduller": {"stok": {"aktif": true, ...}, ...}}
        if 'moduller' in data and isinstance(data['moduller'], dict):
            sonuc = {}
            for k, v in data['moduller'].items():
                if isinstance(v, dict):
                    sonuc[k] = v.get('aktif', True)
                else:
                    sonuc[k] = bool(v)
            return sonuc

        # Eski format: {"stok": true, ...}
        sonuc = dict(_VARSAYILAN)
        sonuc.update({k: bool(v) for k, v in data.items() if not k.startswith('_')})
        return sonuc

    except Exception:
        return dict(_VARSAYILAN)


def modul_meta():
    """Modül metadata bilgilerini döner (ad, versiyon, kategori, vb.)"""
    try:
        with open(_MODUL_DOSYA, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if 'moduller' in data:
            return data['moduller']
    except Exception:
        pass
    return {}


def modul_aktif_mi(modul_adi: str) -> bool:
    return modul_durumları().get(modul_adi, False)


def modul_kaydet(modul_adi: str, aktif: bool):
    """Tek modülün aktif/pasif durumunu güncelle"""
    try:
        with open(_MODUL_DOSYA, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if 'moduller' in data and isinstance(data['moduller'], dict):
            if modul_adi in data['moduller']:
                if isinstance(data['moduller'][modul_adi], dict):
                    data['moduller'][modul_adi]['aktif'] = aktif
                else:
                    data['moduller'][modul_adi] = aktif
            else:
                data['moduller'][modul_adi] = {'aktif': aktif}
        else:
            data[modul_adi] = aktif

        with open(_MODUL_DOSYA, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Modül kaydetme hatası: {e}")


def profil_uygula(profil_yolu: str):
    """Kurulum profili JSON'ını moduller.json'a uygula"""
    with open(profil_yolu, 'r', encoding='utf-8') as f:
        profil = json.load(f)
    for modul, aktif in profil.get('moduller', {}).items():
        modul_kaydet(modul, aktif)
    return profil.get('profil_adi', '?')
