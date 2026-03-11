import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.crm.models.crm import Musteri, Teklif, TeklifSatir, MusteriTakip
from app.kullanici.auth import admin_gerekli, yazma_gerekli

_tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
crm_bp = Blueprint('crm', __name__, template_folder=_tpl)


@crm_bp.route('/')
def crm_dashboard():
    musteri_sayisi = Musteri.query.filter_by(aktif=1).count()
    teklif_sayisi = Teklif.query.count()
    bekleyen = Teklif.query.filter_by(durum='gonderildi').count()
    kabul = Teklif.query.filter_by(durum='kabul').count()
    son_teklifler = Teklif.query.order_by(Teklif.id.desc()).limit(8).all()
    hatirlatmalar = MusteriTakip.query.filter_by(tamamlandi=0).filter(
        MusteriTakip.hatirlatma_tarihi != None).order_by(MusteriTakip.hatirlatma_tarihi).limit(5).all()
    return render_template('crm/crm_dashboard.html',
        musteri_sayisi=musteri_sayisi, teklif_sayisi=teklif_sayisi,
        bekleyen=bekleyen, kabul=kabul,
        son_teklifler=son_teklifler, hatirlatmalar=hatirlatmalar)


# ── Müşteri ────────────────────────────────────────────────────────────────
@crm_bp.route('/musteriler')
def musteri_liste():
    q = request.args.get('q', '')
    query = Musteri.query.filter_by(aktif=1)
    if q:
        query = query.filter(Musteri.unvan.ilike(f'%{q}%') | Musteri.musteri_kodu.ilike(f'%{q}%'))
    musteriler = query.order_by(Musteri.unvan).all()
    return render_template('crm/musteri_liste.html', musteriler=musteriler, q=q)


@crm_bp.route('/musteri/yeni', methods=['GET', 'POST'])
@crm_bp.route('/musteri/<int:id>/duzenle', methods=['GET', 'POST'])
@yazma_gerekli
def musteri_form(id=None):
    m = Musteri.query.get_or_404(id) if id else Musteri()
    if request.method == 'POST':
        m.musteri_kodu = request.form.get('musteri_kodu', '').upper().strip()
        m.unvan = request.form.get('unvan', '').strip()
        m.tur = request.form.get('tur', 'firma')
        m.vergi_no = request.form.get('vergi_no', '')
        m.vergi_dairesi = request.form.get('vergi_dairesi', '')
        m.telefon = request.form.get('telefon', '')
        m.email = request.form.get('email', '')
        m.website = request.form.get('website', '')
        m.adres = request.form.get('adres', '')
        m.sehir = request.form.get('sehir', '')
        m.yetkili_ad = request.form.get('yetkili_ad', '')
        m.yetkili_tel = request.form.get('yetkili_tel', '')
        m.yetkili_email = request.form.get('yetkili_email', '')
        m.odeme_vadesi = int(request.form.get('odeme_vadesi') or 30)
        m.para_birimi = request.form.get('para_birimi', 'TRY')
        m.sektor = request.form.get('sektor', '')
        m.notlar = request.form.get('notlar', '')
        if not id: db.session.add(m)
        try:
            db.session.commit()
            flash('Müşteri kaydedildi', 'success')
            return redirect(url_for('crm.musteri_detay', id=m.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Hata: {str(e)}', 'danger')
    return render_template('crm/musteri_form.html', musteri=m)


@crm_bp.route('/musteri/<int:id>')
def musteri_detay(id):
    m = Musteri.query.get_or_404(id)
    from datetime import datetime
    return render_template('crm/musteri_detay.html', musteri=m, now=datetime.now)


# ── Teklif ─────────────────────────────────────────────────────────────────
@crm_bp.route('/teklifler')
def teklif_liste():
    musteri_id = request.args.get('musteri_id', '', type=int)
    durum = request.args.get('durum', '')
    query = Teklif.query
    if musteri_id:
        query = query.filter_by(musteri_id=musteri_id)
    if durum:
        query = query.filter_by(durum=durum)
    teklifler = query.order_by(Teklif.id.desc()).all()
    musteriler = Musteri.query.filter_by(aktif=1).order_by(Musteri.unvan).all()
    return render_template('crm/teklif_liste.html',
        teklifler=teklifler, musteriler=musteriler,
        secili_musteri=musteri_id, secili_durum=durum)


@crm_bp.route('/teklif/yeni', methods=['GET', 'POST'])
@crm_bp.route('/teklif/<int:id>/duzenle', methods=['GET', 'POST'])
@yazma_gerekli
def teklif_form(id=None):
    t = Teklif.query.get_or_404(id) if id else Teklif()
    musteriler = Musteri.query.filter_by(aktif=1).order_by(Musteri.unvan).all()
    if request.method == 'POST':
        t.musteri_id = int(request.form.get('musteri_id'))
        t.baslik = request.form.get('baslik', '')
        t.tarih = request.form.get('tarih', datetime.now().strftime('%d.%m.%Y'))
        t.gecerlilik = request.form.get('gecerlilik', '')
        t.para_birimi = request.form.get('para_birimi', 'TRY')
        t.kdv_orani = float(request.form.get('kdv_orani') or 20)
        t.notlar = request.form.get('notlar', '')
        t.durum = request.form.get('durum', 'taslak')

        if not t.teklif_no:
            son = Teklif.query.order_by(Teklif.id.desc()).first()
            no = (son.id + 1) if son else 1
            t.teklif_no = f'TKF-{datetime.now().year}-{no:04d}'

        if not id:
            db.session.add(t)
        try:
            db.session.flush()
            # Satırları güncelle
            TeklifSatir.query.filter_by(teklif_id=t.id).delete()
            satirlar_tanim = request.form.getlist('tanim')
            for i, tanim in enumerate(satirlar_tanim):
                if not tanim.strip(): continue
                s = TeklifSatir(
                    teklif_id=t.id, sira=i+1, tanim=tanim,
                    birim=request.form.getlist('birim')[i] if i < len(request.form.getlist('birim')) else 'Adet',
                    miktar=float(request.form.getlist('miktar')[i] or 1),
                    birim_fiyat=float(request.form.getlist('birim_fiyat')[i] or 0),
                    iskonto=float(request.form.getlist('iskonto')[i] or 0),
                )
                s.hesapla()
                db.session.add(s)
            db.session.flush()
            t.toplam_hesapla()
            db.session.commit()
            flash('Teklif kaydedildi', 'success')
            return redirect(url_for('crm.teklif_detay', id=t.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Hata: {str(e)}', 'danger')
    from app.stok.models import Urun
    urunler = Urun.query.filter_by(aktif=1).order_by(Urun.urun_adi).all()
    return render_template('crm/teklif_form.html', teklif=t, musteriler=musteriler, urunler=urunler)


@crm_bp.route('/teklif/<int:id>')
def teklif_detay(id):
    t = Teklif.query.get_or_404(id)
    return render_template('crm/teklif_detay.html', teklif=t)


@crm_bp.route('/teklif/<int:id>/durum', methods=['POST'])
@yazma_gerekli
def teklif_durum(id):
    t = Teklif.query.get_or_404(id)
    yeni_durum = request.form.get('durum', t.durum)
    t.durum = yeni_durum
    db.session.commit()

    # Teklif onaylandı → Otomatik sipariş ve proje oluştur
    if yeni_durum == 'onaylandi':
        try:
            from app.siparis.routes.siparis_routes import tekliften_siparis as _ts
            # Redirect yerine direkt çağır
            from app.proje.routes.proje_routes import teklif_den_proje_olustur
            teklif_den_proje_olustur(id)
            flash('Teklif onaylandı — Proje otomatik oluşturuldu', 'success')
        except Exception:
            flash(f'Teklif durumu: {t.durum}', 'success')
    else:
        flash(f'Teklif durumu: {t.durum}', 'success')
    return redirect(url_for('crm.teklif_detay', id=id))


# ── Takip ──────────────────────────────────────────────────────────────────
@crm_bp.route('/musteri/<int:musteri_id>/takip/ekle', methods=['POST'])
@yazma_gerekli
def takip_ekle(musteri_id):
    Musteri.query.get_or_404(musteri_id)
    t = MusteriTakip(
        musteri_id=musteri_id,
        tur=request.form.get('tur', 'not'),
        baslik=request.form.get('baslik', ''),
        aciklama=request.form.get('aciklama', ''),
        tarih=request.form.get('tarih', datetime.now().strftime('%d.%m.%Y')),
        hatirlatma_tarihi=request.form.get('hatirlatma_tarihi') or None,
    )
    db.session.add(t)
    db.session.commit()
    flash('Takip kaydedildi', 'success')
    return redirect(url_for('crm.musteri_detay', id=musteri_id))


@crm_bp.route('/takip/<int:id>/tamamla', methods=['POST'])
@yazma_gerekli
def takip_tamamla(id):
    t = MusteriTakip.query.get_or_404(id)
    t.tamamlandi = 1
    db.session.commit()
    return redirect(request.referrer or url_for('crm.crm_dashboard'))
