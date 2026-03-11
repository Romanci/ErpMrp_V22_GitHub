import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory
from app import db
from app.dokuman.models.dokuman import Dokuman, KATEGORILER
from app.kullanici.auth import yazma_gerekli, admin_gerekli
from werkzeug.utils import secure_filename

_tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
dokuman_bp = Blueprint('dokuman', __name__, template_folder=_tpl)

YUKLE_KLASOR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))))), 'uploads', 'dokumanlar')
IZIN_UZANTI = {'pdf', 'docx', 'doc', 'xlsx', 'xls', 'pptx', 'png', 'jpg', 'jpeg', 'dwg', 'txt'}


def _uzanti_izinli(dosya_adi):
    return '.' in dosya_adi and dosya_adi.rsplit('.', 1)[1].lower() in IZIN_UZANTI


@dokuman_bp.route('/')
def dokuman_liste():
    kategori = request.args.get('kategori', '')
    q = request.args.get('q', '')
    query = Dokuman.query.filter_by(aktif=1)
    if kategori: query = query.filter_by(kategori=kategori)
    if q: query = query.filter(Dokuman.baslik.ilike(f'%{q}%') | Dokuman.etiketler.ilike(f'%{q}%'))
    dokumanlar = query.order_by(Dokuman.id.desc()).all()
    return render_template('dokuman/dokuman_liste.html',
        dokumanlar=dokumanlar, kategoriler=KATEGORILER,
        secili_kategori=kategori, q=q)


@dokuman_bp.route('/yukle', methods=['GET', 'POST'])
@yazma_gerekli
def dokuman_yukle():
    if request.method == 'POST':
        dosya = request.files.get('dosya')
        baslik = request.form.get('baslik', '').strip()
        if not baslik:
            flash('Başlık zorunlu', 'danger')
            return redirect(request.url)
        d = Dokuman(
            baslik=baslik,
            kategori=request.form.get('kategori', 'genel'),
            revizyon=request.form.get('revizyon', '1.0'),
            aciklama=request.form.get('aciklama', ''),
            gecerlilik_tarihi=request.form.get('gecerlilik_tarihi') or None,
            etiketler=request.form.get('etiketler', ''),
            personel_id=request.form.get('personel_id') or None,
            urun_id=request.form.get('urun_id') or None,
        )
        if dosya and dosya.filename and _uzanti_izinli(dosya.filename):
            os.makedirs(YUKLE_KLASOR, exist_ok=True)
            guvli_ad = secure_filename(dosya.filename)
            benzersiz = f'{datetime.now().strftime("%Y%m%d_%H%M%S")}_{guvli_ad}'
            dosya.save(os.path.join(YUKLE_KLASOR, benzersiz))
            d.dosya_adi = benzersiz
            d.dosya_boyut = os.path.getsize(os.path.join(YUKLE_KLASOR, benzersiz))
            d.dosya_tur = guvli_ad.rsplit('.', 1)[1].lower()
        db.session.add(d)
        db.session.commit()
        flash('Doküman yüklendi', 'success')
        return redirect(url_for('dokuman.dokuman_liste'))
    from app.ik.models.personel import Personel
    from app.stok.models import Urun
    return render_template('dokuman/dokuman_yukle.html',
        kategoriler=KATEGORILER,
        personeller=Personel.query.filter_by(aktif=1).order_by(Personel.ad).all(),
        urunler=Urun.query.filter_by(aktif=1).order_by(Urun.urun_adi).all())


@dokuman_bp.route('/indir/<int:id>')
def dokuman_indir(id):
    d = Dokuman.query.get_or_404(id)
    if not d.dosya_adi:
        flash('Dosya bulunamadı', 'danger')
        return redirect(url_for('dokuman.dokuman_liste'))
    return send_from_directory(YUKLE_KLASOR, d.dosya_adi, as_attachment=True,
                               download_name=d.baslik + '.' + (d.dosya_tur or 'pdf'))


@dokuman_bp.route('/sil/<int:id>', methods=['POST'])
@admin_gerekli
def dokuman_sil(id):
    d = Dokuman.query.get_or_404(id)
    if d.dosya_adi:
        try: os.remove(os.path.join(YUKLE_KLASOR, d.dosya_adi))
        except: pass
    d.aktif = 0
    db.session.commit()
    flash('Doküman silindi', 'success')
    return redirect(url_for('dokuman.dokuman_liste'))
