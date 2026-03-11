import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.proje.models.proje import Proje, ProjeGorev, PROJE_ASAMALARI, ASAMA_RENK
from app.kullanici.auth import yazma_gerekli, admin_gerekli

_tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
proje_bp = Blueprint('proje', __name__, template_folder=_tpl)


def _proje_no_olustur():
    son = Proje.query.order_by(Proje.id.desc()).first()
    yil = datetime.now().year
    return f'PRJ-{yil}-{((son.id if son else 0) + 1):04d}'


# ── Dashboard ────────────────────────────────────────────────────────────────

@proje_bp.route('/')
def proje_dashboard():
    projeler = Proje.query.filter_by(aktif=1).order_by(Proje.id.desc()).all()
    asama_sayilari = {}
    for asama, _ in PROJE_ASAMALARI:
        asama_sayilari[asama] = sum(1 for p in projeler if p.asama == asama)
    aktif = [p for p in projeler if p.asama not in ('kapandi', 'iptal')]
    return render_template('proje/proje_dashboard.html',
        projeler=projeler, aktif=aktif,
        asama_sayilari=asama_sayilari,
        asamalar=PROJE_ASAMALARI, asama_renk=ASAMA_RENK)


# ── Liste ────────────────────────────────────────────────────────────────────

@proje_bp.route('/liste')
def proje_liste():
    asama = request.args.get('asama', '')
    q = Proje.query.filter_by(aktif=1)
    if asama:
        q = q.filter_by(asama=asama)
    projeler = q.order_by(Proje.id.desc()).all()
    return render_template('proje/proje_liste.html',
        projeler=projeler, secili_asama=asama,
        asamalar=PROJE_ASAMALARI, asama_renk=ASAMA_RENK)


# ── Detay ────────────────────────────────────────────────────────────────────

@proje_bp.route('/<int:id>')
def proje_detay(id):
    proje = Proje.query.get_or_404(id)
    from app.kullanici.models.kullanici import Kullanici
    kullanicilar = Kullanici.query.filter_by(aktif=1).all()
    return render_template('proje/proje_detay.html',
        proje=proje, asamalar=PROJE_ASAMALARI,
        asama_renk=ASAMA_RENK, kullanicilar=kullanicilar)


# ── Form (Yeni / Düzenle) ────────────────────────────────────────────────────

@proje_bp.route('/yeni', methods=['GET', 'POST'])
@proje_bp.route('/<int:id>/duzenle', methods=['GET', 'POST'])
@yazma_gerekli
def proje_form(id=None):
    proje = Proje.query.get_or_404(id) if id else Proje()
    if request.method == 'POST':
        proje.proje_adi           = request.form.get('proje_adi', '').strip()
        proje.aciklama            = request.form.get('aciklama', '')
        proje.musteri_id          = request.form.get('musteri_id') or None
        proje.musteri_adi_serbest = request.form.get('musteri_adi_serbest', '')
        proje.asama               = request.form.get('asama', 'teklif')
        proje.baslangic_tarihi    = request.form.get('baslangic_tarihi', '')
        proje.bitis_tarihi        = request.form.get('bitis_tarihi', '')
        proje.planlanan_maliyet   = float(request.form.get('planlanan_maliyet') or 0)
        proje.para_birimi         = request.form.get('para_birimi', 'TL')
        proje.sorumlu_id          = request.form.get('sorumlu_id') or None
        proje.guncellenme_tarihi  = datetime.now().strftime('%d.%m.%Y')

        if not proje.proje_no:
            proje.proje_no = _proje_no_olustur()

        if not proje.proje_adi:
            flash('Proje adı zorunludur', 'danger')
        else:
            if not id:
                db.session.add(proje)
            try:
                db.session.commit()
                # Bildirim gönder
                _proje_bildirimi_gonder(proje, 'yeni' if not id else 'guncelleme')
                flash(f'Proje kaydedildi: {proje.proje_no}', 'success')
                return redirect(url_for('proje.proje_detay', id=proje.id))
            except Exception as e:
                db.session.rollback()
                flash(f'Hata: {e}', 'danger')

    from app.crm.models.crm import Musteri
    from app.kullanici.models.kullanici import Kullanici
    return render_template('proje/proje_form.html',
        proje=proje, asamalar=PROJE_ASAMALARI,
        musteriler=Musteri.query.filter_by(aktif=1).all(),
        kullanicilar=Kullanici.query.filter_by(aktif=1).all())


# ── Aşama Güncelle ───────────────────────────────────────────────────────────

@proje_bp.route('/<int:id>/asama', methods=['POST'])
@yazma_gerekli
def proje_asama_guncelle(id):
    proje = Proje.query.get_or_404(id)
    yeni_asama = request.form.get('asama')
    eski_asama = proje.asama
    if yeni_asama and yeni_asama != eski_asama:
        proje.asama = yeni_asama
        proje.guncellenme_tarihi = datetime.now().strftime('%d.%m.%Y')
        if yeni_asama in ('kapandi', 'sevk'):
            proje.gercek_bitis = datetime.now().strftime('%d.%m.%Y')
        db.session.commit()
        _proje_bildirimi_gonder(proje, 'asama_degisimi', detay=f'{eski_asama} → {yeni_asama}')
        flash(f'Proje aşaması güncellendi: {proje.asama_adi}', 'success')
    return redirect(url_for('proje.proje_detay', id=id))


# ── Görev Ekle ───────────────────────────────────────────────────────────────

@proje_bp.route('/<int:proje_id>/gorev/ekle', methods=['POST'])
@yazma_gerekli
def gorev_ekle(proje_id):
    proje = Proje.query.get_or_404(proje_id)
    g = ProjeGorev(
        proje_id   = proje_id,
        baslik     = request.form.get('baslik', '').strip(),
        aciklama   = request.form.get('aciklama', ''),
        departman  = request.form.get('departman', 'yonetim'),
        atanan_id  = request.form.get('atanan_id') or None,
        son_tarih  = request.form.get('son_tarih', ''),
        oncelik    = request.form.get('oncelik', 'normal'),
        durum      = 'bekliyor',
    )
    if not g.baslik:
        flash('Görev başlığı zorunludur', 'danger')
        return redirect(url_for('proje.proje_detay', id=proje_id))
    db.session.add(g)
    db.session.commit()
    flash('Görev eklendi', 'success')
    return redirect(url_for('proje.proje_detay', id=proje_id))


# ── Görev Durum Güncelle ─────────────────────────────────────────────────────

@proje_bp.route('/gorev/<int:gorev_id>/durum', methods=['POST'])
def gorev_durum_guncelle(gorev_id):
    g = ProjeGorev.query.get_or_404(gorev_id)
    g.durum = request.form.get('durum', g.durum)
    if g.durum == 'tamamlandi':
        g.tamamlanma_tarihi = datetime.now().strftime('%d.%m.%Y')
    db.session.commit()
    flash('Görev güncellendi', 'success')
    return redirect(url_for('proje.proje_detay', id=g.proje_id))


# ── Görev Listesi (Departman Bazlı) ──────────────────────────────────────────

@proje_bp.route('/gorevler')
def gorev_listesi():
    """Giriş yapan kullanıcının departmanına göre görevleri göster"""
    admin_mi = session.get('admin', False)
    departman_filtre = request.args.get('departman', '')

    q = ProjeGorev.query.filter(ProjeGorev.durum != 'iptal')
    if not admin_mi and departman_filtre:
        q = q.filter_by(departman=departman_filtre)
    elif not admin_mi:
        # Admin değilse sadece kendi kullanıcısına atanan veya tüm departman görevleri
        kullanici_id = session.get('kullanici_id')
        q = q.filter(
            (ProjeGorev.atanan_id == kullanici_id) |
            (ProjeGorev.atanan_id == None)
        )

    gorevler = q.order_by(ProjeGorev.son_tarih.asc()).all()
    return render_template('proje/gorev_listesi.html',
        gorevler=gorevler, admin_mi=admin_mi,
        secili_departman=departman_filtre)


# ── Teklif → Proje Dönüştür ──────────────────────────────────────────────────

def teklif_den_proje_olustur(teklif_id):
    """CRM teklifinden otomatik proje oluştur — teklif onaylandığında çağrılır"""
    from app.crm.models.crm import Teklif
    teklif = Teklif.query.get(teklif_id)
    if not teklif:
        return None

    # Zaten proje oluşturulmuş mu?
    mevcut = Proje.query.filter_by(teklif_id=teklif_id).first()
    if mevcut:
        return mevcut

    proje = Proje(
        proje_no          = _proje_no_olustur(),
        proje_adi         = teklif.konu or f'Teklif {teklif.teklif_no}',
        aciklama          = f'Teklif {teklif.teklif_no} onayından otomatik oluşturuldu',
        musteri_id        = teklif.musteri_id,
        teklif_id         = teklif_id,
        asama             = 'onay',
        planlanan_maliyet = teklif.toplam_tutar or 0,
        para_birimi       = teklif.para_birimi or 'TL',
        baslangic_tarihi  = datetime.now().strftime('%d.%m.%Y'),
    )
    db.session.add(proje)
    db.session.commit()
    _proje_bildirimi_gonder(proje, 'teklif_onay')
    return proje


# ── Bildirim ─────────────────────────────────────────────────────────────────

def _proje_bildirimi_gonder(proje, olay, detay=''):
    """Proje olaylarında sistem bildirimi + email gönder"""
    try:
        mesajlar = {
            'yeni':         f'Yeni proje oluşturuldu: {proje.proje_no} — {proje.proje_adi}',
            'guncelleme':   f'Proje güncellendi: {proje.proje_no}',
            'asama_degisimi': f'Proje aşaması değişti: {proje.proje_no} → {proje.asama_adi} ({detay})',
            'teklif_onay':  f'Teklif onaylandı, proje oluşturuldu: {proje.proje_no} — {proje.proje_adi}',
        }
        mesaj = mesajlar.get(olay, f'Proje güncellendi: {proje.proje_no}')

        # Sistem bildirimi kaydet
        from app.stok.models.bildirim import Bildirim
        b = Bildirim(
            baslik   = 'Proje Bildirimi',
            mesaj    = mesaj,
            tur      = 'proje',
            kayit_id = proje.id,
        )
        db.session.add(b)
        db.session.commit()
    except Exception:
        pass
