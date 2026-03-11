# Bakim modulu - Bakim plani ve ariza yonetimi
import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.bakim.models import BakimPlan, BakimKayit, ArizaKayit
from app.uretim.models.tezgah import Tezgah

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
bakim_bp = Blueprint('bakim', __name__, template_folder=template_klasoru)


# ─── Bakim Dashboard ─────────────────────────────────────────────────────────
@bakim_bp.route('/')
def bakim_dashboard():
    # Acik arizalar
    acik_ariza = ArizaKayit.query.filter_by(durum='acik', aktif=1).count()
    kritik_ariza = ArizaKayit.query.filter_by(durum='acik', oncelik='kritik', aktif=1).count()

    # Yaklasan bakimlar (sonraki 7 gun icinde)
    bugun = datetime.now()
    yaklasan_bakimlar = []
    planlar = BakimPlan.query.filter_by(aktif=1).all()
    for plan in planlar:
        if plan.sonraki_bakim:
            try:
                tarih = datetime.strptime(plan.sonraki_bakim, '%d.%m.%Y')
                kalan = (tarih - bugun).days
                if kalan <= 7:
                    yaklasan_bakimlar.append({'plan': plan, 'kalan': kalan})
            except Exception:
                pass

    son_arizalar = ArizaKayit.query.filter_by(aktif=1).order_by(ArizaKayit.id.desc()).limit(8).all()
    toplam_tezgah = Tezgah.query.filter_by(aktif=1).count()

    return render_template('bakim/bakim_dashboard.html',
                           acik_ariza=acik_ariza,
                           kritik_ariza=kritik_ariza,
                           yaklasan_bakimlar=yaklasan_bakimlar,
                           son_arizalar=son_arizalar,
                           toplam_tezgah=toplam_tezgah)


# ─── Ariza Listesi ───────────────────────────────────────────────────────────
@bakim_bp.route('/arizalar')
def ariza_liste():
    durum_filtre = request.args.get('durum', '')
    q = ArizaKayit.query.filter_by(aktif=1)
    if durum_filtre:
        q = q.filter_by(durum=durum_filtre)
    arizalar = q.order_by(ArizaKayit.id.desc()).all()
    return render_template('bakim/ariza_liste.html', arizalar=arizalar, durum_filtre=durum_filtre)


# ─── Yeni Ariza ──────────────────────────────────────────────────────────────
@bakim_bp.route('/ariza/yeni', methods=['GET', 'POST'])
def ariza_ekle():
    if request.method == 'POST':
        yeni = ArizaKayit(
            tezgah_id=request.form['tezgah_id'],
            ariza_tarihi=request.form.get('ariza_tarihi') or datetime.now().strftime('%d.%m.%Y'),
            ariza_aciklama=request.form['ariza_aciklama'],
            oncelik=request.form.get('oncelik', 'normal'),
            durum='acik',
        )
        db.session.add(yeni)
        db.session.commit()
        flash('Ariza kaydi olusturuldu', 'success')
        return redirect(url_for('bakim.ariza_liste'))
    tezgahlar = Tezgah.query.filter_by(aktif=1).all()
    return render_template('bakim/ariza_form.html', ariza=None, tezgahlar=tezgahlar)


# ─── Ariza Durum Guncelle ────────────────────────────────────────────────────
@bakim_bp.route('/ariza/<int:id>/durum', methods=['POST'])
def ariza_durum(id):
    ariza = ArizaKayit.query.get_or_404(id)
    ariza.durum = request.form.get('durum', ariza.durum)
    ariza.tamir_aciklama = request.form.get('tamir_aciklama', ariza.tamir_aciklama)
    ariza.maliyet = float(request.form.get('maliyet', ariza.maliyet or 0))
    if ariza.durum == 'cozuldu' and not ariza.tamir_bitis:
        ariza.tamir_bitis = datetime.now().strftime('%d.%m.%Y')
    db.session.commit()
    flash(f'Ariza durumu guncellendi: {ariza.durum}', 'success')
    return redirect(url_for('bakim.ariza_liste'))


# ─── Bakim Planlari ──────────────────────────────────────────────────────────
@bakim_bp.route('/planlar')
def bakim_plan_liste():
    planlar = BakimPlan.query.filter_by(aktif=1).order_by(BakimPlan.sonraki_bakim).all()
    return render_template('bakim/bakim_plan_liste.html', planlar=planlar)


# ─── Yeni Bakim Plani ────────────────────────────────────────────────────────
@bakim_bp.route('/plan/yeni', methods=['GET', 'POST'])
def bakim_plan_ekle():
    if request.method == 'POST':
        periyot = int(request.form.get('periyot_gun', 30))
        son_bakim = request.form.get('son_bakim')
        # Sonraki bakimi hesapla
        sonraki = None
        if son_bakim:
            try:
                dt = datetime.strptime(son_bakim, '%d.%m.%Y')
                sonraki = (dt + timedelta(days=periyot)).strftime('%d.%m.%Y')
            except Exception:
                pass

        yeni = BakimPlan(
            tezgah_id=request.form['tezgah_id'],
            bakim_adi=request.form['bakim_adi'],
            bakim_turu=request.form.get('bakim_turu', 'periyodik'),
            periyot_gun=periyot,
            son_bakim=son_bakim,
            sonraki_bakim=sonraki,
            tahmini_sure_dk=int(request.form.get('tahmini_sure_dk', 60)),
            aciklama=request.form.get('aciklama'),
        )
        db.session.add(yeni)
        db.session.commit()
        flash('Bakim plani olusturuldu', 'success')
        return redirect(url_for('bakim.bakim_plan_liste'))
    tezgahlar = Tezgah.query.filter_by(aktif=1).all()
    return render_template('bakim/bakim_plan_form.html', plan=None, tezgahlar=tezgahlar)


# ─── Bakim Kaydi Ekle ────────────────────────────────────────────────────────
@bakim_bp.route('/plan/<int:plan_id>/kayit', methods=['POST'])
def bakim_kayit_ekle(plan_id):
    plan = BakimPlan.query.get_or_404(plan_id)
    tarih = request.form.get('bakim_tarihi') or datetime.now().strftime('%d.%m.%Y')
    yeni_kayit = BakimKayit(
        plan_id=plan_id,
        tezgah_id=plan.tezgah_id,
        bakim_tarihi=tarih,
        bakim_turu=plan.bakim_turu,
        yapilan_isler=request.form.get('yapilan_isler'),
        sure_dk=int(request.form.get('sure_dk', 0) or 0),
        maliyet=float(request.form.get('maliyet', 0) or 0),
        durum='tamamlandi',
    )
    db.session.add(yeni_kayit)

    # Plani guncelle
    plan.son_bakim = tarih
    try:
        dt = datetime.strptime(tarih, '%d.%m.%Y')
        plan.sonraki_bakim = (dt + timedelta(days=plan.periyot_gun)).strftime('%d.%m.%Y')
    except Exception:
        pass
    db.session.commit()
    flash('Bakim kaydi eklendi ve plan guncellendi', 'success')
    return redirect(url_for('bakim.bakim_plan_liste'))
