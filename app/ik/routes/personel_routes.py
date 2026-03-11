import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from app import db
from app.ik.models.personel import (
    Personel, PersonelEkBilgi, Izin, Devamsizlik, Tatil, KkdTanim, Zimmet, Maas
)
from app.kullanici.auth import admin_gerekli, yazma_gerekli

template_klasoru = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
ik_bp = Blueprint('ik', __name__, template_folder=template_klasoru)

IZIN_TURLERI = [
    ('yillik',       'Yıllık İzin'),
    ('hastalik',     'Hastalık İzni'),
    ('mazeret',      'Mazeret İzni'),
    ('ucretsiz',     'Ücretsiz İzin'),
    ('babalik',      'Babalık İzni'),
    ('annelik',      'Annelik İzni'),
    ('vefat',        'Vefat İzni'),
    ('resmi_tatil',  'Resmi/Bayram Tatili'),
    ('firma_tatili', 'Firma Tatili'),
]

VEFAT_YAKINLARI = ['anne', 'baba', 'es', 'cocuk', 'kardes']

# ─── Dashboard ────────────────────────────────────────
@ik_bp.route('/')
def ik_dashboard():
    personel_sayisi = Personel.query.filter_by(aktif=1).count()
    bekleyen_izin = Izin.query.filter_by(durum='beklemede').count()
    bugun = datetime.now().strftime('%d.%m.%Y')

    # Bugün izinli olanlar
    bugun_izinli = Izin.query.filter(
        Izin.durum == 'onaylandi',
        Izin.baslangic <= bugun,
        Izin.bitis >= bugun
    ).count()

    # KKD yenileme uyarıları
    kkd_uyari = 0
    zimmetler = Zimmet.query.filter_by(durum='aktif').all()
    for z in zimmetler:
        if z.yenileme_gerekiyor:
            kkd_uyari += 1

    # Bu ay devamsızlık
    ay_bas = datetime.now().strftime('01.%m.%Y')
    devamsizlik = Devamsizlik.query.filter(Devamsizlik.tarih >= ay_bas).count()

    son_izinler = Izin.query.order_by(Izin.id.desc()).limit(8).all()

    return render_template('ik/ik_dashboard.html',
        personel_sayisi=personel_sayisi,
        bekleyen_izin=bekleyen_izin,
        bugun_izinli=bugun_izinli,
        kkd_uyari=kkd_uyari,
        devamsizlik=devamsizlik,
        son_izinler=son_izinler,
    )


# ─── Personel CRUD ────────────────────────────────────
@ik_bp.route('/personel')
def personel_liste():
    departman = request.args.get('departman', '')
    q = request.args.get('q', '')
    query = Personel.query.filter_by(aktif=1)
    if departman:
        query = query.filter_by(departman=departman)
    if q:
        query = query.filter(
            (Personel.ad + ' ' + Personel.soyad).ilike(f'%{q}%') |
            Personel.sicil_no.ilike(f'%{q}%')
        )
    personeller = query.order_by(Personel.ad).all()
    departmanlar = db.session.query(Personel.departman).filter(
        Personel.aktif == 1, Personel.departman != None
    ).distinct().all()
    return render_template('ik/personel_liste.html',
        personeller=personeller,
        departmanlar=[d[0] for d in departmanlar if d[0]],
        secili_departman=departman, q=q,
    )


@ik_bp.route('/personel/yeni', methods=['GET', 'POST'])
@ik_bp.route('/personel/<int:id>/duzenle', methods=['GET', 'POST'])
@yazma_gerekli
def personel_form(id=None):
    personel = Personel.query.get_or_404(id) if id else Personel()
    if request.method == 'POST':
        personel.sicil_no = request.form.get('sicil_no', '').strip()
        personel.ad = request.form.get('ad', '').strip()
        personel.soyad = request.form.get('soyad', '').strip()
        personel.tc_kimlik = request.form.get('tc_kimlik', '').strip()
        personel.dogum_tarihi = request.form.get('dogum_tarihi', '').strip()
        personel.cinsiyet = request.form.get('cinsiyet', '').strip()
        personel.telefon = request.form.get('telefon', '').strip()
        personel.email = request.form.get('email', '').strip()
        personel.adres = request.form.get('adres', '').strip()
        personel.departman = request.form.get('departman', '').strip()
        personel.pozisyon = request.form.get('pozisyon', '').strip()
        personel.ise_baslama = request.form.get('ise_baslama', '').strip()
        personel.calisma_turu = request.form.get('calisma_turu', 'tam_zamanli')
        personel.maas = float(request.form.get('maas') or 0)
        personel.sube_id = request.form.get('sube_id') or None

        if not id:
            db.session.add(personel)
        try:
            db.session.flush()
            # Ek bilgileri kaydet
            ek = personel.ek_bilgi or PersonelEkBilgi(personel_id=personel.id)
            ek.kan_grubu = request.form.get('kan_grubu', '')
            ek.boy = float(request.form.get('boy') or 0) or None
            ek.kilo = float(request.form.get('kilo') or 0) or None
            ek.kronik_hastalik = request.form.get('kronik_hastalik', '')
            ek.ilac_kullanimi = request.form.get('ilac_kullanimi', '')
            ek.acil_ad = request.form.get('acil_ad', '')
            ek.acil_tel = request.form.get('acil_tel', '')
            ek.acil_yakinlik = request.form.get('acil_yakinlik', '')
            ek.ust_beden = request.form.get('ust_beden', '')
            ek.alt_beden = request.form.get('alt_beden', '')
            ek.ayak_numarasi = request.form.get('ayak_numarasi', '')
            ek.baret_bedeni = request.form.get('baret_bedeni', '')
            ek.guncelleme = datetime.now().strftime('%d.%m.%Y')
            if not ek.id:
                db.session.add(ek)
            db.session.commit()
            flash(f'Personel {"eklendi" if not id else "güncellendi"}', 'success')
            return redirect(url_for('ik.personel_detay', id=personel.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Hata: {str(e)}', 'danger')

    from app.stok.models.sube import Sube
    subeler = Sube.query.filter_by(aktif=1).all()
    return render_template('ik/personel_form.html', personel=personel, subeler=subeler)


@ik_bp.route('/personel/<int:id>')
def personel_detay(id):
    personel = Personel.query.get_or_404(id)
    yil = datetime.now().year
    izin_hakki = Izin.yillik_izin_hakki(personel)
    kullanilan = Izin.kullanilan_yillik(personel.id, yil)
    kalan = izin_hakki - kullanilan

    bekleyen_izinler = Izin.query.filter_by(personel_id=id, durum='beklemede').all()
    son_izinler = Izin.query.filter_by(personel_id=id).order_by(Izin.id.desc()).limit(10).all()
    zimmetler = Zimmet.query.filter_by(personel_id=id).order_by(Zimmet.id.desc()).all()
    devamsizliklar = Devamsizlik.query.filter_by(personel_id=id).order_by(Devamsizlik.tarih.desc()).limit(10).all()

    return render_template('ik/personel_detay.html',
        personel=personel,
        izin_hakki=izin_hakki, kullanilan=kullanilan, kalan=kalan,
        bekleyen_izinler=bekleyen_izinler, son_izinler=son_izinler,
        zimmetler=zimmetler, devamsizliklar=devamsizliklar,
        izin_turleri=IZIN_TURLERI, vefat_yakinlari=VEFAT_YAKINLARI,
    )


@ik_bp.route('/personel/<int:id>/sil', methods=['POST'])
@admin_gerekli
def personel_sil(id):
    p = Personel.query.get_or_404(id)
    p.aktif = 0
    p.isten_ayrilma = datetime.now().strftime('%d.%m.%Y')
    db.session.commit()
    flash(f'{p.tam_ad} pasife alındı', 'success')
    return redirect(url_for('ik.personel_liste'))


# ─── İzin ────────────────────────────────────────────
@ik_bp.route('/izinler')
def izin_liste():
    durum = request.args.get('durum', '')
    tur = request.args.get('tur', '')
    query = Izin.query
    if durum:
        query = query.filter_by(durum=durum)
    if tur:
        query = query.filter_by(izin_turu=tur)
    izinler = query.order_by(Izin.id.desc()).limit(200).all()
    return render_template('ik/izin_liste.html',
        izinler=izinler, izin_turleri=IZIN_TURLERI,
        secili_durum=durum, secili_tur=tur,
    )


@ik_bp.route('/personel/<int:personel_id>/izin/ekle', methods=['POST'])
@yazma_gerekli
def izin_ekle(personel_id):
    personel = Personel.query.get_or_404(personel_id)
    tur = request.form.get('izin_turu', '')
    bas = request.form.get('baslangic', '')
    bit = request.form.get('bitis', '')
    gun = request.form.get('gun_sayisi', 0)
    aciklama = request.form.get('aciklama', '')
    talep_turu = request.form.get('talep_turu', 'talep')

    if not tur or not bas or not bit or not gun:
        flash('Tüm alanlar zorunlu', 'danger')
        return redirect(url_for('ik.personel_detay', id=personel_id))

    # Vefat izninde 3 günü kontrol et
    if tur == 'vefat':
        gun = min(float(gun), 3)

    iz = Izin(
        personel_id=personel_id,
        izin_turu=tur,
        baslangic=bas,
        bitis=bit,
        gun_sayisi=float(gun),
        aciklama=aciklama,
        talep_turu=talep_turu,
        vefat_yakin=request.form.get('vefat_yakin', ''),
        rapor_no=request.form.get('rapor_no', ''),
        rapor_hastane=request.form.get('rapor_hastane', ''),
        durum='onaylandi' if talep_turu == 'direkt' else 'beklemede',
    )
    if talep_turu == 'direkt':
        iz.onay_tarihi = datetime.now().strftime('%d.%m.%Y')

    db.session.add(iz)
    db.session.commit()
    flash('İzin kaydedildi', 'success')
    return redirect(url_for('ik.personel_detay', id=personel_id))


@ik_bp.route('/izin/<int:izin_id>/onayla', methods=['POST'])
@admin_gerekli
def izin_onayla(izin_id):
    iz = Izin.query.get_or_404(izin_id)
    iz.durum = 'onaylandi'
    iz.onay_tarihi = datetime.now().strftime('%d.%m.%Y')
    from flask import session
    iz.onaylayan_id = session.get('kullanici_id')
    db.session.commit()
    flash('İzin onaylandı', 'success')
    return redirect(request.referrer or url_for('ik.izin_liste'))


@ik_bp.route('/izin/<int:izin_id>/reddet', methods=['POST'])
@admin_gerekli
def izin_reddet(izin_id):
    iz = Izin.query.get_or_404(izin_id)
    iz.durum = 'reddedildi'
    iz.red_nedeni = request.form.get('red_nedeni', '')
    db.session.commit()
    flash('İzin reddedildi', 'warning')
    return redirect(request.referrer or url_for('ik.izin_liste'))


@ik_bp.route('/izin/<int:izin_id>/sil', methods=['POST'])
@admin_gerekli
def izin_sil(izin_id):
    iz = Izin.query.get_or_404(izin_id)
    personel_id = iz.personel_id
    db.session.delete(iz)
    db.session.commit()
    flash('İzin silindi', 'success')
    return redirect(url_for('ik.personel_detay', id=personel_id))


# ─── Devamsızlık ─────────────────────────────────────
@ik_bp.route('/personel/<int:personel_id>/devamsizlik/ekle', methods=['POST'])
@yazma_gerekli
def devamsizlik_ekle(personel_id):
    d = Devamsizlik(
        personel_id=personel_id,
        tarih=request.form.get('tarih', ''),
        tur=request.form.get('tur', 'gelmedi'),
        sure_dakika=int(request.form.get('sure_dakika') or 0),
        aciklama=request.form.get('aciklama', ''),
    )
    db.session.add(d)
    db.session.commit()
    flash('Devamsızlık kaydedildi', 'success')
    return redirect(url_for('ik.personel_detay', id=personel_id))


@ik_bp.route('/devamsizlik/<int:id>/sil', methods=['POST'])
@admin_gerekli
def devamsizlik_sil(id):
    d = Devamsizlik.query.get_or_404(id)
    personel_id = d.personel_id
    db.session.delete(d)
    db.session.commit()
    flash('Kayıt silindi', 'success')
    return redirect(url_for('ik.personel_detay', id=personel_id))


# ─── Tatil Takvimi ───────────────────────────────────
@ik_bp.route('/tatiller')
def tatil_liste():
    tatiller = Tatil.query.filter_by(aktif=1).order_by(Tatil.tarih).all()
    return render_template('ik/tatil_liste.html', tatiller=tatiller)


@ik_bp.route('/tatil/yeni', methods=['GET', 'POST'])
@ik_bp.route('/tatil/<int:id>/duzenle', methods=['GET', 'POST'])
@admin_gerekli
def tatil_form(id=None):
    tatil = Tatil.query.get_or_404(id) if id else Tatil()
    if request.method == 'POST':
        tatil.ad = request.form.get('ad', '')
        tatil.tarih = request.form.get('tarih', '')
        tatil.bitis_tarihi = request.form.get('bitis_tarihi', '') or None
        tatil.tur = request.form.get('tur', 'resmi')
        tatil.yillik_tekrar = 1 if request.form.get('yillik_tekrar') else 0
        tatil.aciklama = request.form.get('aciklama', '')
        if not id:
            db.session.add(tatil)
        db.session.commit()
        flash('Tatil kaydedildi', 'success')
        return redirect(url_for('ik.tatil_liste'))
    return render_template('ik/tatil_form.html', tatil=tatil)


@ik_bp.route('/tatil/<int:id>/sil', methods=['POST'])
@admin_gerekli
def tatil_sil(id):
    t = Tatil.query.get_or_404(id)
    t.aktif = 0
    db.session.commit()
    flash('Tatil kaldırıldı', 'success')
    return redirect(url_for('ik.tatil_liste'))


@ik_bp.route('/tatil/resmi-yukle', methods=['POST'])
@admin_gerekli
def resmi_tatil_yukle():
    """2025 Türkiye resmi tatillerini otomatik yükle"""
    yil = int(request.form.get('yil', datetime.now().year))
    tatiller_data = [
        (f'01.01.{yil}', 'Yılbaşı', 'resmi', 1),
        (f'23.04.{yil}', 'Ulusal Egemenlik ve Çocuk Bayramı', 'resmi', 1),
        (f'01.05.{yil}', 'Emek ve Dayanışma Günü', 'resmi', 1),
        (f'19.05.{yil}', 'Atatürk\'ü Anma, Gençlik ve Spor Bayramı', 'resmi', 1),
        (f'15.07.{yil}', 'Demokrasi ve Millî Birlik Günü', 'resmi', 1),
        (f'30.08.{yil}', 'Zafer Bayramı', 'resmi', 1),
        (f'29.10.{yil}', 'Cumhuriyet Bayramı', 'resmi', 1),
    ]
    eklenen = 0
    for tarih, ad, tur, tekrar in tatiller_data:
        mevcut = Tatil.query.filter_by(tarih=tarih, ad=ad).first()
        if not mevcut:
            db.session.add(Tatil(ad=ad, tarih=tarih, tur=tur, yillik_tekrar=tekrar))
            eklenen += 1
    db.session.commit()
    flash(f'{yil} yılı için {eklenen} resmi tatil eklendi', 'success')
    return redirect(url_for('ik.tatil_liste'))


# ─── KKD / Zimmet ────────────────────────────────────
@ik_bp.route('/kkd')
def kkd_liste():
    tanimlar = KkdTanim.query.filter_by(aktif=1).order_by(KkdTanim.ad).all()
    return render_template('ik/kkd_liste.html', tanimlar=tanimlar)


@ik_bp.route('/kkd/yeni', methods=['GET', 'POST'])
@ik_bp.route('/kkd/<int:id>/duzenle', methods=['GET', 'POST'])
@admin_gerekli
def kkd_form(id=None):
    kkd = KkdTanim.query.get_or_404(id) if id else KkdTanim()
    if request.method == 'POST':
        kkd.kod = request.form.get('kod', '').upper().strip()
        kkd.ad = request.form.get('ad', '').strip()
        kkd.tur = request.form.get('tur', 'kkd')
        kkd.aciklama = request.form.get('aciklama', '')
        kkd.yenileme_ay = int(request.form.get('yenileme_ay') or 12)
        kkd.stok_urun_id = request.form.get('stok_urun_id') or None
        if not id:
            db.session.add(kkd)
        db.session.commit()
        flash('KKD tanımı kaydedildi', 'success')
        return redirect(url_for('ik.kkd_liste'))
    from app.stok.models import Urun
    urunler = Urun.query.filter_by(aktif=1).order_by(Urun.urun_adi).all()
    return render_template('ik/kkd_form.html', kkd=kkd, urunler=urunler)


@ik_bp.route('/zimmet')
def zimmet_liste():
    durum = request.args.get('durum', '')
    uyari = request.args.get('uyari', '')
    query = Zimmet.query
    if durum:
        query = query.filter_by(durum=durum)
    zimmetler = query.order_by(Zimmet.id.desc()).all()
    if uyari:
        zimmetler = [z for z in zimmetler if z.yenileme_gerekiyor]
    return render_template('ik/zimmet_liste.html', zimmetler=zimmetler,
        secili_durum=durum, uyari=uyari)


@ik_bp.route('/personel/<int:personel_id>/zimmet/ver', methods=['POST'])
@yazma_gerekli
def zimmet_ver(personel_id):
    personel = Personel.query.get_or_404(personel_id)
    kkd_id = request.form.get('kkd_tanim_id')
    if not kkd_id:
        flash('KKD seçilmedi', 'danger')
        return redirect(url_for('ik.personel_detay', id=personel_id))

    kkd = KkdTanim.query.get(kkd_id)
    verilis = request.form.get('verilis_tarihi') or datetime.now().strftime('%d.%m.%Y')

    # Yenileme tarihi hesapla
    try:
        v_dt = datetime.strptime(verilis, '%d.%m.%Y')
        yn_dt = v_dt + timedelta(days=30 * (kkd.yenileme_ay or 12))
        yenileme = yn_dt.strftime('%d.%m.%Y')
    except Exception:
        yenileme = None

    z = Zimmet(
        personel_id=personel_id,
        kkd_tanim_id=int(kkd_id),
        miktar=float(request.form.get('miktar') or 1),
        beden=request.form.get('beden', ''),
        verilis_tarihi=verilis,
        yenileme_tarihi=yenileme,
        aciklama=request.form.get('aciklama', ''),
        onceki_zimmet_id=request.form.get('onceki_zimmet_id') or None,
    )
    db.session.add(z)

    # Stok entegrasyonu
    if kkd and kkd.stok_urun_id:
        try:
            from app.stok.models import StokHareket
            sh = StokHareket(
                urun_id=kkd.stok_urun_id,
                hareket_tipi='cikis',
                miktar=z.miktar,
                aciklama=f'KKD Zimmet - {personel.tam_ad}',
                tarih=verilis,
            )
            db.session.add(sh)
            z.stoktan_dusuldu = 1
        except Exception:
            pass

    db.session.commit()
    flash(f'{kkd.ad} zimmeti verildi', 'success')
    return redirect(url_for('ik.personel_detay', id=personel_id))


@ik_bp.route('/zimmet/<int:id>/durum', methods=['POST'])
@yazma_gerekli
def zimmet_durum(id):
    z = Zimmet.query.get_or_404(id)
    yeni_durum = request.form.get('durum', '')
    aciklama = request.form.get('aciklama', '')
    z.durum = yeni_durum
    z.aciklama = (z.aciklama or '') + (f'\n{aciklama}' if aciklama else '')
    if yeni_durum == 'iade_edildi':
        z.iade_tarihi = datetime.now().strftime('%d.%m.%Y')
    db.session.commit()
    flash('Zimmet durumu güncellendi', 'success')
    return redirect(request.referrer or url_for('ik.zimmet_liste'))


@ik_bp.route('/zimmet/<int:id>/yenile', methods=['POST'])
@yazma_gerekli
def zimmet_yenile(id):
    """Kırık/bozuk/özelliğini kaybetmiş zimmet için yenisini ver"""
    eski = Zimmet.query.get_or_404(id)
    eski.durum = request.form.get('eski_durum', 'kirik')

    kkd = eski.kkd
    verilis = datetime.now().strftime('%d.%m.%Y')
    try:
        yn_dt = datetime.now() + timedelta(days=30 * (kkd.yenileme_ay or 12))
        yenileme = yn_dt.strftime('%d.%m.%Y')
    except Exception:
        yenileme = None

    yeni = Zimmet(
        personel_id=eski.personel_id,
        kkd_tanim_id=eski.kkd_tanim_id,
        miktar=eski.miktar,
        beden=eski.beden,
        verilis_tarihi=verilis,
        yenileme_tarihi=yenileme,
        aciklama=f'Yenileme ({eski.durum})',
        onceki_zimmet_id=eski.id,
    )
    db.session.add(yeni)

    # Stok entegrasyonu
    if kkd and kkd.stok_urun_id:
        try:
            from app.stok.models import StokHareket
            p = Personel.query.get(eski.personel_id)
            sh = StokHareket(
                urun_id=kkd.stok_urun_id,
                hareket_tipi='cikis',
                miktar=yeni.miktar,
                aciklama=f'KKD Yenileme - {p.tam_ad if p else ""}',
                tarih=verilis,
            )
            db.session.add(sh)
            yeni.stoktan_dusuldu = 1
        except Exception:
            pass

    db.session.commit()
    flash(f'{kkd.ad} yenilendi', 'success')
    return redirect(request.referrer or url_for('ik.personel_detay', id=eski.personel_id))


# ─── Maaş ────────────────────────────────────────────
@ik_bp.route('/personel/<int:personel_id>/maas/ekle', methods=['POST'])
@yazma_gerekli
def maas_ekle(personel_id):
    Personel.query.get_or_404(personel_id)
    brut = float(request.form.get('brut_maas', 0))
    prim = float(request.form.get('prim', 0))
    kesinti = float(request.form.get('kesinti', 0))
    net = brut + prim - kesinti
    m = Maas(
        personel_id=personel_id,
        donem=request.form.get('donem', ''),
        brut_maas=brut, prim=prim, kesinti=kesinti, net_maas=net,
        odeme_tarihi=request.form.get('odeme_tarihi', ''),
        odendi_mi=1 if request.form.get('odendi_mi') else 0,
        aciklama=request.form.get('aciklama', ''),
    )
    db.session.add(m)
    db.session.commit()
    flash('Maaş kaydedildi', 'success')
    return redirect(url_for('ik.personel_detay', id=personel_id))


# ─── Takvim API ──────────────────────────────────────
@ik_bp.route('/api/takvim')
def api_takvim():
    """FullCalendar için JSON veri"""
    yil = request.args.get('yil', datetime.now().year, type=int)
    ay = request.args.get('ay', 0, type=int)
    events = []

    # İzinler
    izinler = Izin.query.filter_by(durum='onaylandi').all()
    renkler = {
        'yillik': '#3b82f6', 'hastalik': '#ef4444', 'mazeret': '#f97316',
        'ucretsiz': '#6b7280', 'vefat': '#7c3aed', 'babalik': '#0891b2',
        'annelik': '#db2777', 'resmi_tatil': '#15803d', 'firma_tatili': '#92400e',
    }
    for iz in izinler:
        p = iz.personel
        events.append({
            'id': f'izin-{iz.id}',
            'title': f'{p.tam_ad if p else "?"} ({iz.izin_turu})',
            'start': _tr2iso(iz.baslangic),
            'end': _tr2iso_bitis(iz.bitis),
            'color': renkler.get(iz.izin_turu, '#64748b'),
            'url': url_for('ik.personel_detay', id=iz.personel_id),
        })

    # Tatiller
    tatiller = Tatil.query.filter_by(aktif=1).all()
    for t in tatiller:
        events.append({
            'id': f'tatil-{t.id}',
            'title': t.ad,
            'start': _tr2iso(t.tarih),
            'end': _tr2iso_bitis(t.bitis_tarihi or t.tarih),
            'color': '#15803d',
            'display': 'background',
        })

    return jsonify(events)


def _tr2iso(tarih_str):
    try:
        return datetime.strptime(tarih_str, '%d.%m.%Y').strftime('%Y-%m-%d')
    except Exception:
        return tarih_str


def _tr2iso_bitis(tarih_str):
    """FullCalendar bitiş = +1 gün"""
    try:
        dt = datetime.strptime(tarih_str, '%d.%m.%Y') + timedelta(days=1)
        return dt.strftime('%Y-%m-%d')
    except Exception:
        return tarih_str


@ik_bp.route('/api/kkd-tanimlar')
def api_kkd_tanimlar():
    tanimlar = KkdTanim.query.filter_by(aktif=1).order_by(KkdTanim.ad).all()
    return jsonify([{'id': k.id, 'ad': k.ad, 'tur': k.tur, 'yenileme_ay': k.yenileme_ay} for k in tanimlar])
