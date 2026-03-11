import os
from app.kullanici.auth import admin_gerekli
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from app import db
from app.kullanici.models import Kullanici, Rol, KullaniciRol
from datetime import datetime

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
kullanici_bp = Blueprint('kullanici', __name__, template_folder=template_klasoru)


# ─── Kullanici Listesi ───────────────────────────────────────────────────────
@kullanici_bp.route('/kullanicilar')
@admin_gerekli
def kullanici_liste():
    kullanicilar = Kullanici.query.filter_by(aktif=1).order_by(Kullanici.ad).all()
    return render_template('kullanici/kullanici_liste.html', kullanicilar=kullanicilar)


# ─── Yeni Kullanici ──────────────────────────────────────────────────────────
@kullanici_bp.route('/kullanici/yeni', methods=['GET', 'POST'])
@admin_gerekli
def kullanici_ekle():
    if request.method == 'POST':
        # Kullanici adi bos mu?
        if not request.form.get('kullanici_adi') or not request.form.get('sifre'):
            flash('Kullanici adi ve sifre zorunludur', 'danger')
            return redirect(url_for('kullanici.kullanici_ekle'))

        # Mevcut kullanici adi var mi?
        mevcut = Kullanici.query.filter_by(kullanici_adi=request.form['kullanici_adi']).first()
        if mevcut:
            flash('Bu kullanici adi zaten kullaniliyor', 'danger')
            roller = Rol.query.filter_by(aktif=1).all()
            return render_template('kullanici/kullanici_form.html', kullanici=None, roller=roller)

        yeni = Kullanici(
            kullanici_adi=request.form['kullanici_adi'],
            sifre_hash=Kullanici.sifrele(request.form['sifre']),
            ad=request.form['ad'],
            soyad=request.form['soyad'],
            email=request.form.get('email'),
            telefon=request.form.get('telefon'),
            departman=request.form.get('departman'),
        )
        db.session.add(yeni)
        db.session.flush()  # ID al

        # Rol ata
        rol_id = request.form.get('rol_id')
        if rol_id:
            kr = KullaniciRol(kullanici_id=yeni.id, rol_id=int(rol_id))
            db.session.add(kr)

        db.session.commit()
        flash(f'{yeni.tam_ad} kullanicisi olusturuldu', 'success')
        return redirect(url_for('kullanici.kullanici_liste'))

    roller = Rol.query.filter_by(aktif=1).all()
    return render_template('kullanici/kullanici_form.html', kullanici=None, roller=roller)


# ─── Kullanici Duzenle ───────────────────────────────────────────────────────
@kullanici_bp.route('/kullanici/<int:id>/duzenle', methods=['GET', 'POST'])
def kullanici_duzenle(id):
    kullanici = Kullanici.query.get_or_404(id)

    if request.method == 'POST':
        kullanici.ad = request.form['ad']
        kullanici.soyad = request.form['soyad']
        kullanici.email = request.form.get('email')
        kullanici.telefon = request.form.get('telefon')
        kullanici.departman = request.form.get('departman')

        # Sifre guncelle (bos birakilirsa degistirme)
        yeni_sifre = request.form.get('sifre')
        if yeni_sifre:
            kullanici.sifre_hash = Kullanici.sifrele(yeni_sifre)

        # Rol guncelle
        rol_id = request.form.get('rol_id')
        if rol_id:
            # Eski rolleri sil, yenisini ekle
            KullaniciRol.query.filter_by(kullanici_id=kullanici.id).delete()
            kr = KullaniciRol(kullanici_id=kullanici.id, rol_id=int(rol_id))
            db.session.add(kr)

        db.session.commit()
        flash('Kullanici guncellendi', 'success')
        return redirect(url_for('kullanici.kullanici_liste'))

    roller = Rol.query.filter_by(aktif=1).all()
    mevcut_rol_id = kullanici.roller[0].rol_id if kullanici.roller else None
    return render_template('kullanici/kullanici_form.html',
                           kullanici=kullanici, roller=roller, mevcut_rol_id=mevcut_rol_id)


# ─── Kullanici Sil ───────────────────────────────────────────────────────────
@kullanici_bp.route('/kullanici/<int:id>/sil', methods=['POST'])
def kullanici_sil(id):
    kullanici = Kullanici.query.get_or_404(id)
    kullanici.aktif = 0
    db.session.commit()
    flash('Kullanici devre disi birakildi', 'success')
    return redirect(url_for('kullanici.kullanici_liste'))


# ─── Kullanici Detay ─────────────────────────────────────────────────────────
@kullanici_bp.route('/kullanici/<int:id>')
def kullanici_detay(id):
    kullanici = Kullanici.query.get_or_404(id)
    return render_template('kullanici/kullanici_detay.html', kullanici=kullanici)


# ─── Rol Listesi ─────────────────────────────────────────────────────────────
@kullanici_bp.route('/roller')
@admin_gerekli
def rol_liste():
    roller = Rol.query.filter_by(aktif=1).all()
    return render_template('kullanici/rol_liste.html', roller=roller)


# ─── Yeni Rol ────────────────────────────────────────────────────────────────
@kullanici_bp.route('/rol/yeni', methods=['GET', 'POST'])
def rol_ekle():
    if request.method == 'POST':
        yeni_rol = Rol(
            rol_adi=request.form['rol_adi'],
            aciklama=request.form.get('aciklama'),
            stok_erisim=1 if request.form.get('stok_erisim') else 0,
            satin_alma_erisim=1 if request.form.get('satin_alma_erisim') else 0,
            uretim_erisim=1 if request.form.get('uretim_erisim') else 0,
            ik_erisim=1 if request.form.get('ik_erisim') else 0,
            bakim_erisim=1 if request.form.get('bakim_erisim') else 0,
            yazma_izni=1 if request.form.get('yazma_izni') else 0,
            silme_izni=1 if request.form.get('silme_izni') else 0,
        )
        db.session.add(yeni_rol)
        db.session.commit()
        flash('Rol olusturuldu', 'success')
        return redirect(url_for('kullanici.rol_liste'))
    return render_template('kullanici/rol_form.html', rol=None)


# ─── Rol Duzenle ─────────────────────────────────────────────────────────────
@kullanici_bp.route('/rol/<int:id>/duzenle', methods=['GET', 'POST'])
def rol_duzenle(id):
    rol = Rol.query.get_or_404(id)
    if request.method == 'POST':
        rol.rol_adi = request.form['rol_adi']
        rol.aciklama = request.form.get('aciklama')
        rol.stok_erisim = 1 if request.form.get('stok_erisim') else 0
        rol.satin_alma_erisim = 1 if request.form.get('satin_alma_erisim') else 0
        rol.uretim_erisim = 1 if request.form.get('uretim_erisim') else 0
        rol.ik_erisim = 1 if request.form.get('ik_erisim') else 0
        rol.bakim_erisim = 1 if request.form.get('bakim_erisim') else 0
        rol.yazma_izni = 1 if request.form.get('yazma_izni') else 0
        rol.silme_izni = 1 if request.form.get('silme_izni') else 0
        db.session.commit()
        flash('Rol guncellendi', 'success')
        return redirect(url_for('kullanici.rol_liste'))
    return render_template('kullanici/rol_form.html', rol=rol)


# ─── Giris / Cikis ───────────────────────────────────────────────────────────
@kullanici_bp.route('/giris', methods=['GET', 'POST'])
def giris():
    if request.method == 'POST':
        kullanici_adi = request.form.get('kullanici_adi', '').strip()
        sifre = request.form.get('sifre', '')

        kullanici = Kullanici.query.filter_by(kullanici_adi=kullanici_adi, aktif=1).first()
        if kullanici and kullanici.sifre_dogru_mu(sifre):
            session['kullanici_id'] = kullanici.id
            session['kullanici_adi'] = kullanici.kullanici_adi
            session['tam_ad'] = kullanici.tam_ad
            session['admin'] = kullanici.admin_mi()

            # Son giris guncelle
            kullanici.son_giris = datetime.now().strftime('%d.%m.%Y %H:%M')
            db.session.commit()
            flash(f'Hos geldiniz, {kullanici.tam_ad}!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Kullanici adi veya sifre yanlis', 'danger')

    return render_template('kullanici/giris.html')


@kullanici_bp.route('/cikis')
def cikis():
    session.clear()
    flash('Cikis yapildi', 'info')
    return redirect(url_for('kullanici.giris'))


@kullanici_bp.route('/profil', methods=['GET', 'POST'])
def profil():
    """Oturum acik kullanicinin kendi profil sayfasi"""
    from flask import session
    from app.kullanici.models import Kullanici
    kullanici = Kullanici.query.get_or_404(session.get('kullanici_id'))

    if request.method == 'POST':
        aksiyon = request.form.get('aksiyon')

        if aksiyon == 'bilgi':
            kullanici.ad = request.form.get('ad', kullanici.ad)
            kullanici.soyad = request.form.get('soyad', kullanici.soyad)
            kullanici.email = request.form.get('email', kullanici.email)
            kullanici.telefon = request.form.get('telefon', kullanici.telefon)
            kullanici.departman = request.form.get('departman', kullanici.departman)
            db.session.commit()
            # Session'daki tam_ad güncelle
            session['tam_ad'] = f"{kullanici.ad} {kullanici.soyad}"
            flash('Profil bilgileri güncellendi', 'success')

        elif aksiyon == 'sifre':
            mevcut = request.form.get('mevcut_sifre', '')
            yeni = request.form.get('yeni_sifre', '')
            tekrar = request.form.get('sifre_tekrar', '')
            if not kullanici.sifre_dogru_mu(mevcut):
                flash('Mevcut şifre yanlış', 'danger')
            elif len(yeni) < 6:
                flash('Yeni şifre en az 6 karakter olmalı', 'danger')
            elif yeni != tekrar:
                flash('Şifreler eşleşmiyor', 'danger')
            else:
                kullanici.sifre_hash = Kullanici.sifrele(yeni)
                db.session.commit()
                flash('Şifre başarıyla değiştirildi', 'success')

        return redirect(url_for('kullanici.profil'))

    return render_template('kullanici/profil.html', kullanici=kullanici)
