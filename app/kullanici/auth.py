"""Yetki kontrol sistemi - rol bazlı erişim kontrolü"""
from functools import wraps
from flask import session, redirect, url_for, flash, request

def _rol_al():
    try:
        from app.kullanici.models import Kullanici
        uid = session.get('kullanici_id')
        if not uid:
            return None
        k = Kullanici.query.get(uid)
        return k.birincil_rol() if k else None
    except Exception:
        return None


def giris_gerekli(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'kullanici_id' not in session:
            flash('Giriş yapmanız gerekiyor', 'warning')
            return redirect(url_for('kullanici.giris', next=request.path))
        return f(*args, **kwargs)
    return decorated


def admin_gerekli(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'kullanici_id' not in session:
            return redirect(url_for('kullanici.giris'))
        if not session.get('admin'):
            flash('Bu işlem için yönetici yetkisi gerekli', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


def yazma_gerekli(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'kullanici_id' not in session:
            return redirect(url_for('kullanici.giris'))
        if session.get('admin'):
            return f(*args, **kwargs)
        rol = _rol_al()
        if not rol or not rol.yazma_izni:
            flash('Bu işlem için yazma yetkisi gerekli', 'danger')
            return redirect(request.referrer or url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


def silme_gerekli(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'kullanici_id' not in session:
            return redirect(url_for('kullanici.giris'))
        if session.get('admin'):
            return f(*args, **kwargs)
        rol = _rol_al()
        if not rol or not rol.silme_izni:
            flash('Bu işlem için silme yetkisi gerekli', 'danger')
            return redirect(request.referrer or url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


def modul_gerekli(alan):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'kullanici_id' not in session:
                return redirect(url_for('kullanici.giris'))
            if session.get('admin'):
                return f(*args, **kwargs)
            rol = _rol_al()
            if not rol or not getattr(rol, alan, 0):
                flash('Bu modüle erişim yetkiniz yok', 'danger')
                return redirect(url_for('main.dashboard'))
            return f(*args, **kwargs)
        return decorated
    return decorator


def kullanici_yetkileri():
    if 'kullanici_id' not in session:
        return {}
    if session.get('admin'):
        return {'yetki': {
            'stok': True, 'satin_alma': True, 'uretim': True,
            'ik': True, 'bakim': True, 'yazma': True, 'silme': True, 'admin': True,
        }}
    rol = _rol_al()
    if not rol:
        return {'yetki': {}}
    return {'yetki': {
        'stok': bool(rol.stok_erisim),
        'satin_alma': bool(rol.satin_alma_erisim),
        'uretim': bool(rol.uretim_erisim),
        'ik': bool(rol.ik_erisim),
        'bakim': bool(rol.bakim_erisim),
        'yazma': bool(rol.yazma_izni),
        'silme': bool(rol.silme_izni),
        'admin': False,
    }}
