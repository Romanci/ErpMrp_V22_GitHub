import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.kalite.models.kalite import KaliteKontrol, KaliteHata, KaliteSertifika
from app.kullanici.auth import yazma_gerekli, admin_gerekli

_tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
kalite_bp = Blueprint('kalite', __name__, template_folder=_tpl)

TUR_ADI = {'gelen_malzeme': 'Gelen Malzeme', 'uretim_ara': 'Üretim Ara', 'uretim_cikis': 'Çıkış Kontrol'}

@kalite_bp.route('/')
def kalite_dashboard():
    toplam = KaliteKontrol.query.count()
    bekleyen = KaliteKontrol.query.filter_by(sonuc='beklemede').count()
    ret = KaliteKontrol.query.filter_by(sonuc='ret').count()
    kabul = KaliteKontrol.query.filter_by(sonuc='kabul').count()
    son_kontroller = KaliteKontrol.query.order_by(KaliteKontrol.id.desc()).limit(10).all()
    suresi_biten = [s for s in KaliteSertifika.query.filter_by(aktif=1).all() if s.uyari_var_mi]
    return render_template('kalite/kalite_dashboard.html',
        toplam=toplam, bekleyen=bekleyen, ret=ret, kabul=kabul,
        son_kontroller=son_kontroller, suresi_biten=suresi_biten, tur_adi=TUR_ADI)


@kalite_bp.route('/kontroller')
def kontrol_liste():
    tur = request.args.get('tur', '')
    sonuc = request.args.get('sonuc', '')
    q = KaliteKontrol.query
    if tur: q = q.filter_by(tur=tur)
    if sonuc: q = q.filter_by(sonuc=sonuc)
    kontroller = q.order_by(KaliteKontrol.id.desc()).limit(200).all()
    return render_template('kalite/kontrol_liste.html', kontroller=kontroller,
        secili_tur=tur, secili_sonuc=sonuc, tur_adi=TUR_ADI)


@kalite_bp.route('/kontrol/yeni', methods=['GET', 'POST'])
@kalite_bp.route('/kontrol/<int:id>/duzenle', methods=['GET', 'POST'])
@yazma_gerekli
def kontrol_form(id=None):
    k = KaliteKontrol.query.get_or_404(id) if id else KaliteKontrol()
    if request.method == 'POST':
        k.tur = request.form.get('tur', 'gelen_malzeme')
        k.tarih = request.form.get('tarih', datetime.now().strftime('%d.%m.%Y'))
        k.urun_id = request.form.get('urun_id') or None
        k.tedarikci_id = request.form.get('tedarikci_id') or None
        k.parti_no = request.form.get('parti_no', '')
        k.kontrol_miktari = float(request.form.get('kontrol_miktari') or 0)
        k.kabul_miktari = float(request.form.get('kabul_miktari') or 0)
        k.ret_miktari = float(request.form.get('ret_miktari') or 0)
        k.sonuc = request.form.get('sonuc', 'beklemede')
        k.notlar = request.form.get('notlar', '')
        if not k.kontrol_no:
            son = KaliteKontrol.query.order_by(KaliteKontrol.id.desc()).first()
            k.kontrol_no = f'KK-{datetime.now().year}-{((son.id if son else 0)+1):04d}'
        if not id: db.session.add(k)
        try:
            db.session.commit()
            flash('Kontrol kaydedildi', 'success')
            return redirect(url_for('kalite.kontrol_liste'))
        except Exception as e:
            db.session.rollback(); flash(f'Hata: {e}', 'danger')
    from app.stok.models import Urun
    from app.satin_alma.models.tedarikci import Tedarikci
    return render_template('kalite/kontrol_form.html', kontrol=k,
        urunler=Urun.query.filter_by(aktif=1).all(),
        tedarikciler=Tedarikci.query.filter_by(aktif=1).all(),
        tur_adi=TUR_ADI)


@kalite_bp.route('/sertifikalar')
def sertifika_liste():
    sertifikalar = KaliteSertifika.query.filter_by(aktif=1).order_by(KaliteSertifika.bitis).all()
    return render_template('kalite/sertifika_liste.html', sertifikalar=sertifikalar)


@kalite_bp.route('/sertifika/yeni', methods=['GET', 'POST'])
@kalite_bp.route('/sertifika/<int:id>/duzenle', methods=['GET', 'POST'])
@yazma_gerekli
def sertifika_form(id=None):
    s = KaliteSertifika.query.get_or_404(id) if id else KaliteSertifika()
    if request.method == 'POST':
        s.ad = request.form.get('ad', '')
        s.sertifika_no = request.form.get('sertifika_no', '')
        s.tur = request.form.get('tur', '')
        s.veren_kurum = request.form.get('veren_kurum', '')
        s.baslangic = request.form.get('baslangic', '')
        s.bitis = request.form.get('bitis', '')
        s.notlar = request.form.get('notlar', '')
        if not id: db.session.add(s)
        db.session.commit()
        flash('Sertifika kaydedildi', 'success')
        return redirect(url_for('kalite.sertifika_liste'))
    return render_template('kalite/sertifika_form.html', sertifika=s)
