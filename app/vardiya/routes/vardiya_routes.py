import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from app import db
from app.vardiya.models.vardiya import VardiyaTanim, VardiyaAtama, Puantaj, GunlukDevam
from app.kullanici.auth import yazma_gerekli, admin_gerekli

_tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
vardiya_bp = Blueprint('vardiya', __name__, template_folder=_tpl)

@vardiya_bp.route('/')
def vardiya_dashboard():
    tanimlar = VardiyaTanim.query.filter_by(aktif=1).all()
    bugun = datetime.now().strftime('%d.%m.%Y')
    bugun_atamalar = VardiyaAtama.query.filter_by(tarih=bugun).all()
    bekleyen_puantaj = Puantaj.query.filter_by(onaylandi=0).count()
    return render_template('vardiya/vardiya_dashboard.html',
        tanimlar=tanimlar, bugun_atamalar=bugun_atamalar,
        bekleyen_puantaj=bekleyen_puantaj, bugun=bugun)

@vardiya_bp.route('/tanimlar')
def tanim_liste():
    tanimlar = VardiyaTanim.query.filter_by(aktif=1).all()
    return render_template('vardiya/tanim_liste.html', tanimlar=tanimlar)

@vardiya_bp.route('/tanim/yeni', methods=['POST'])
@vardiya_bp.route('/tanim/<int:id>/duzenle', methods=['POST'])
@admin_gerekli
def tanim_kaydet(id=None):
    t = VardiyaTanim.query.get_or_404(id) if id else VardiyaTanim()
    t.ad = request.form.get('ad','')
    t.baslangic = request.form.get('baslangic','08:00')
    t.bitis = request.form.get('bitis','17:00')
    t.renk = request.form.get('renk','#3b82f6')
    if not id: db.session.add(t)
    db.session.commit()
    flash('Vardiya tanımı kaydedildi', 'success')
    return redirect(url_for('vardiya.tanim_liste'))

@vardiya_bp.route('/atama')
def atama_liste():
    ay = request.args.get('ay', datetime.now().strftime('%Y-%m'))
    yil, ay_no = map(int, ay.split('-'))
    bas = f'01.{ay_no:02d}.{yil}'
    from calendar import monthrange
    son_gun = monthrange(yil, ay_no)[1]
    bit = f'{son_gun}.{ay_no:02d}.{yil}'
    atamalar = VardiyaAtama.query.filter(
        VardiyaAtama.tarih >= bas, VardiyaAtama.tarih <= bit
    ).all()
    tanimlar = VardiyaTanim.query.filter_by(aktif=1).all()
    from app.ik.models.personel import Personel
    personeller = Personel.query.filter_by(aktif=1).order_by(Personel.ad).all()
    return render_template('vardiya/atama_liste.html',
        atamalar=atamalar, tanimlar=tanimlar,
        personeller=personeller, secili_ay=ay)

@vardiya_bp.route('/atama/kaydet', methods=['POST'])
@yazma_gerekli
def atama_kaydet():
    a = VardiyaAtama(
        personel_id=int(request.form.get('personel_id')),
        vardiya_id=int(request.form.get('vardiya_id')),
        tarih=request.form.get('tarih',''),
        notlar=request.form.get('notlar',''),
    )
    db.session.add(a)
    db.session.commit()
    flash('Vardiya atandı', 'success')
    return redirect(url_for('vardiya.atama_liste'))

@vardiya_bp.route('/puantaj')
def puantaj_liste():
    ay = request.args.get('ay', datetime.now().strftime('%Y-%m'))
    yil, ay_no = map(int, ay.split('-'))
    puantajlar = Puantaj.query.filter_by(yil=yil, ay=ay_no).all()
    return render_template('vardiya/puantaj_liste.html',
        puantajlar=puantajlar, secili_ay=ay)

@vardiya_bp.route('/puantaj/olustur', methods=['POST'])
@yazma_gerekli
def puantaj_olustur():
    """Seçilen ay için tüm aktif personelin puantajını otomatik oluştur"""
    from app.ik.models.personel import Personel, Izin, Devamsizlik
    from app.ik.models.personel import Tatil
    ay = request.form.get('ay', datetime.now().strftime('%Y-%m'))
    yil, ay_no = map(int, ay.split('-'))
    from calendar import monthrange
    toplam_gun = monthrange(yil, ay_no)[1]

    # Resmi tatil günleri
    ay_bas = f'01.{ay_no:02d}.{yil}'
    ay_bit = f'{toplam_gun}.{ay_no:02d}.{yil}'
    tatil_sayisi = Tatil.query.filter(
        Tatil.aktif == 1,
        Tatil.tarih >= ay_bas,
        Tatil.tarih <= ay_bit,
    ).count()

    personeller = Personel.query.filter_by(aktif=1).all()
    olusturulan = 0
    for p in personeller:
        mevcut = Puantaj.query.filter_by(personel_id=p.id, yil=yil, ay=ay_no).first()
        if mevcut: continue
        # İzin günleri
        izin_gun = Izin.kullanilan_yillik(p.id, yil) if ay_no == datetime.now().month else 0
        # Devamsızlık
        dev_gun = Devamsizlik.query.filter(
            Devamsizlik.personel_id == p.id,
            Devamsizlik.tarih >= ay_bas,
            Devamsizlik.tarih <= ay_bit,
            Devamsizlik.tur == 'gelmedi',
        ).count()
        is_gunu = toplam_gun - tatil_sayisi
        calisilan = max(0, is_gunu - izin_gun - dev_gun)
        pu = Puantaj(
            personel_id=p.id, yil=yil, ay=ay_no,
            calisilan_gun=calisilan, izin_gun=izin_gun,
            devamsizlik_gun=dev_gun, resmi_tatil_gun=tatil_sayisi,
        )
        db.session.add(pu)
        olusturulan += 1
    db.session.commit()
    flash(f'{olusturulan} personel için puantaj oluşturuldu', 'success')
    return redirect(url_for('vardiya.puantaj_liste', ay=ay))


# ── Toplu Günlük Devam Girişi ─────────────────────────────────────────────────

@vardiya_bp.route('/devam')
def devam_dashboard():
    """Tarih seçimi ve günlük devam özeti"""
    from app.vardiya.models.vardiya import GunlukDevam
    tarih = request.args.get('tarih', datetime.now().strftime('%d.%m.%Y'))
    devamlar = GunlukDevam.query.filter_by(tarih=tarih).all()
    devam_map = {d.personel_id: d for d in devamlar}

    # Özet istatistik
    ozet = {
        'geldi':       sum(1 for d in devamlar if d.durum == 'geldi'),
        'gelmedi':     sum(1 for d in devamlar if d.durum == 'gelmedi'),
        'gec_geldi':   sum(1 for d in devamlar if d.durum == 'gec_geldi'),
        'erken_cikis': sum(1 for d in devamlar if d.durum == 'erken_cikis'),
        'izinli':      sum(1 for d in devamlar if d.durum == 'izinli'),
        'toplam':      len(devamlar),
    }

    from app.ik.models.personel import Personel
    personeller = Personel.query.filter_by(aktif=1).order_by(Personel.ad).all()

    return render_template('vardiya/devam_dashboard.html',
        tarih=tarih, personeller=personeller,
        devam_map=devam_map, ozet=ozet)


@vardiya_bp.route('/devam/toplu-kaydet', methods=['POST'])
@yazma_gerekli
def devam_toplu_kaydet():
    """Tüm personel için günlük devam durumunu tek seferde kaydet"""
    from app.vardiya.models.vardiya import GunlukDevam
    from app.ik.models.personel import Personel
    tarih = request.form.get('tarih', datetime.now().strftime('%d.%m.%Y'))
    kullanici_id = session.get('kullanici_id')

    personeller = Personel.query.filter_by(aktif=1).all()
    kaydedilen = 0

    for p in personeller:
        durum_key = f'durum_{p.id}'
        durum = request.form.get(durum_key)
        if not durum:
            continue

        giris  = request.form.get(f'giris_{p.id}', '')
        cikis  = request.form.get(f'cikis_{p.id}', '')
        gecikme = int(request.form.get(f'gecikme_{p.id}') or 0)
        aciklama = request.form.get(f'aciklama_{p.id}', '')

        mevcut = GunlukDevam.query.filter_by(personel_id=p.id, tarih=tarih).first()
        if mevcut:
            mevcut.durum               = durum
            mevcut.giris_saati         = giris
            mevcut.cikis_saati         = cikis
            mevcut.gecikme_dakika      = gecikme
            mevcut.aciklama            = aciklama
            mevcut.olusturan_id        = kullanici_id
        else:
            kayit = GunlukDevam(
                personel_id        = p.id,
                tarih              = tarih,
                durum              = durum,
                giris_saati        = giris,
                cikis_saati        = cikis,
                gecikme_dakika     = gecikme,
                aciklama           = aciklama,
                olusturan_id       = kullanici_id,
                olusturma_tarihi   = datetime.now().strftime('%d.%m.%Y %H:%M'),
            )
            db.session.add(kayit)
        kaydedilen += 1

    db.session.commit()
    flash(f'{tarih} tarihi için {kaydedilen} personel kaydedildi', 'success')
    return redirect(url_for('vardiya.devam_dashboard', tarih=tarih))


@vardiya_bp.route('/devam/gecmis')
def devam_gecmis():
    """Son 30 günün devam özeti — personel bazlı"""
    from app.vardiya.models.vardiya import GunlukDevam
    from app.ik.models.personel import Personel
    from sqlalchemy import func

    personeller = Personel.query.filter_by(aktif=1).order_by(Personel.ad).all()

    # Son 30 gün her personelin devam istatistiği
    istatistikler = {}
    for p in personeller:
        devamlar = GunlukDevam.query.filter_by(personel_id=p.id).order_by(
            GunlukDevam.tarih.desc()).limit(30).all()
        istatistikler[p.id] = {
            'geldi':     sum(1 for d in devamlar if d.durum == 'geldi'),
            'gelmedi':   sum(1 for d in devamlar if d.durum == 'gelmedi'),
            'gec':       sum(1 for d in devamlar if d.durum == 'gec_geldi'),
            'toplam':    len(devamlar),
        }

    return render_template('vardiya/devam_gecmis.html',
        personeller=personeller, istatistikler=istatistikler)


# ── Günlük Toplu Devam Takibi ─────────────────────────────────────────────────

@vardiya_bp.route('/devam')
def devam_listesi():
    """Gün bazlı tüm personel devam durumu"""
    from app.ik.models.personel import Personel
    from app.vardiya.models.vardiya import GunlukDevam

    tarih = request.args.get('tarih', datetime.now().strftime('%d.%m.%Y'))

    personeller = Personel.query.filter_by(aktif=1).order_by(
        Personel.departman, Personel.ad).all()

    # Bu gün için mevcut kayıtları al
    kayitlar = {
        k.personel_id: k
        for k in GunlukDevam.query.filter_by(tarih=tarih).all()
    }

    return render_template('vardiya/devam_listesi.html',
        personeller=personeller, kayitlar=kayitlar, tarih=tarih)


@vardiya_bp.route('/devam/kaydet', methods=['POST'])
@yazma_gerekli
def devam_kaydet():
    """Tüm personelin günlük devam bilgisini toplu kaydet"""
    from app.vardiya.models.vardiya import GunlukDevam

    tarih = request.form.get('tarih', datetime.now().strftime('%d.%m.%Y'))
    personel_idler = request.form.getlist('personel_id[]')
    olusturan_id = session.get('kullanici_id')
    kaydedilen = 0

    for pid in personel_idler:
        durum      = request.form.get(f'durum_{pid}', 'geldi')
        giris      = request.form.get(f'giris_{pid}', '')
        cikis      = request.form.get(f'cikis_{pid}', '')
        aciklama   = request.form.get(f'aciklama_{pid}', '')

        # Gecikme hesapla (standart 08:00 giriş)
        gecikme = 0
        if giris and durum == 'geldi':
            try:
                standart_h, standart_m = 8, 0
                gelen_h, gelen_m = map(int, giris.split(':'))
                fark = (gelen_h * 60 + gelen_m) - (standart_h * 60 + standart_m)
                gecikme = max(0, fark)
            except Exception:
                pass

        # Erken çıkış (standart 17:00 çıkış)
        erken_cikis = 0
        if cikis and durum == 'geldi':
            try:
                standart_h, standart_m = 17, 0
                cikan_h, cikan_m = map(int, cikis.split(':'))
                fark = (standart_h * 60 + standart_m) - (cikan_h * 60 + cikan_m)
                erken_cikis = max(0, fark)
            except Exception:
                pass

        # Mevcut kaydı güncelle ya da yeni oluştur
        kayit = GunlukDevam.query.filter_by(
            personel_id=int(pid), tarih=tarih).first()

        if kayit:
            kayit.durum             = durum
            kayit.giris_saati       = giris
            kayit.cikis_saati       = cikis
            kayit.gecikme_dakika    = gecikme
            kayit.erken_cikis_dakika = erken_cikis
            kayit.aciklama          = aciklama
        else:
            kayit = GunlukDevam(
                personel_id         = int(pid),
                tarih               = tarih,
                durum               = durum,
                giris_saati         = giris,
                cikis_saati         = cikis,
                gecikme_dakika      = gecikme,
                erken_cikis_dakika  = erken_cikis,
                aciklama            = aciklama,
                olusturan_id        = olusturan_id,
                olusturma_tarihi    = datetime.now().strftime('%d.%m.%Y %H:%M'),
            )
            db.session.add(kayit)
        kaydedilen += 1

    db.session.commit()
    flash(f'{tarih} tarihi için {kaydedilen} personel kaydedildi', 'success')
    return redirect(url_for('vardiya.devam_listesi', tarih=tarih))


@vardiya_bp.route('/devam/rapor')
def devam_rapor():
    """Aylık devam özet raporu"""
    from app.ik.models.personel import Personel
    from app.vardiya.models.vardiya import GunlukDevam
    import calendar

    yil  = int(request.args.get('yil',  datetime.now().year))
    ay   = int(request.args.get('ay',   datetime.now().month))
    dep  = request.args.get('departman', '')

    ay_adi = ['', 'Ocak','Şubat','Mart','Nisan','Mayıs','Haziran',
              'Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık'][ay]

    q = Personel.query.filter_by(aktif=1)
    if dep:
        q = q.filter_by(departman=dep)
    personeller = q.order_by(Personel.departman, Personel.ad).all()

    gun_sayisi = calendar.monthrange(yil, ay)[1]

    # Ay için tarih listesi (GG.MM.YYYY)
    tarihler = [f'{g:02d}.{ay:02d}.{yil}' for g in range(1, gun_sayisi + 1)]

    # Tüm kayıtları al
    tum_kayitlar = GunlukDevam.query.filter(
        GunlukDevam.tarih.like(f'%.{ay:02d}.{yil}')
    ).all()

    kayit_map = {}
    for k in tum_kayitlar:
        kayit_map[(k.personel_id, k.tarih)] = k

    # Her personel için özet
    ozet = []
    for p in personeller:
        geldi = devamsiz = gec = erken = izinli = 0
        for t in tarihler:
            k = kayit_map.get((p.id, t))
            if k:
                if k.durum == 'geldi':
                    geldi += 1
                    if k.gecikme_dakika > 0:    gec += 1
                    if k.erken_cikis_dakika > 0: erken += 1
                elif k.durum == 'gelmedi':    devamsiz += 1
                elif k.durum == 'izinli':     izinli += 1
        ozet.append({
            'personel': p,
            'geldi': geldi, 'devamsiz': devamsiz,
            'gec': gec, 'erken': erken, 'izinli': izinli,
            'kayitsiz': gun_sayisi - geldi - devamsiz - izinli,
        })

    departmanlar = sorted(set(p.departman for p in
        Personel.query.filter_by(aktif=1).all() if p.departman))

    return render_template('vardiya/devam_rapor.html',
        ozet=ozet, yil=yil, ay=ay, ay_adi=ay_adi,
        gun_sayisi=gun_sayisi, tarihler=tarihler,
        secili_dep=dep, departmanlar=departmanlar,
        kayit_map=kayit_map)
