import os
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app import db
from app.muhasebe.models.muhasebe import (
    MuhasebeKalem, HESAP_TURLERI, GELIR_KATEGORILERI, GIDER_KATEGORILERI
)
from app.kullanici.auth import yazma_gerekli

_tpl = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'templates')
muhasebe_bp = Blueprint('muhasebe', __name__, template_folder=_tpl)


# ── Dashboard ────────────────────────────────────────────────────────────────

@muhasebe_bp.route('/')
def muhasebe_dashboard():
    simdi = datetime.now()
    ay    = simdi.month
    yil   = simdi.year

    bu_ay   = MuhasebeKalem.donem_ozeti(ay=ay, yil=yil)
    bu_yil  = MuhasebeKalem.donem_ozeti(yil=yil)
    toplam  = MuhasebeKalem.donem_ozeti()

    # Son 12 ay grafik verisi
    aylik_veri = []
    for i in range(11, -1, -1):
        try:
            hedef_yil = yil
            hedef_ay_no = ay - i
            while hedef_ay_no <= 0:
                hedef_ay_no += 12
                hedef_yil -= 1
            ay_adlari = ['','Oca','Şub','Mar','Nis','May','Haz','Tem','Ağu','Eyl','Eki','Kas','Ara']
            ozet = MuhasebeKalem.donem_ozeti(ay=hedef_ay_no, yil=hedef_yil)
            aylik_veri.append({
                'ay_adi': f"{ay_adlari[hedef_ay_no]} {hedef_yil}",
                'gelir':  ozet['gelir'],
                'gider':  ozet['gider'],
                'kar':    ozet['kar'],
            })
        except Exception:
            pass

    # Son 20 kalem
    son_kalemler = MuhasebeKalem.query.order_by(
        MuhasebeKalem.id.desc()).limit(20).all()

    return render_template('muhasebe/muhasebe_dashboard.html',
        bu_ay=bu_ay, bu_yil=bu_yil, toplam=toplam,
        aylik_veri=aylik_veri, son_kalemler=son_kalemler,
        simdi_ay=ay, simdi_yil=yil)


# ── Kalem Listesi ────────────────────────────────────────────────────────────

@muhasebe_bp.route('/liste')
def muhasebe_liste():
    tur  = request.args.get('tur', '')
    proje_id = request.args.get('proje_id', '')
    ay   = request.args.get('ay', '')
    yil  = request.args.get('yil', str(datetime.now().year))

    q = MuhasebeKalem.query
    if tur:
        q = q.filter_by(tur=tur)
    if proje_id:
        q = q.filter_by(proje_id=proje_id)
    if yil:
        q = q.filter(MuhasebeKalem.tarih.like(f'%.{yil}'))
    if ay:
        ay_str = f'{int(ay):02d}'
        q = q.filter(MuhasebeKalem.tarih.like(f'%.{ay_str}.%'))

    kalemler = q.order_by(MuhasebeKalem.tarih.desc(), MuhasebeKalem.id.desc()).all()
    ozet = {
        'gelir': sum(k.tutar for k in kalemler if k.tur == 'gelir'),
        'gider': sum(k.tutar for k in kalemler if k.tur == 'gider'),
    }
    ozet['kar'] = ozet['gelir'] - ozet['gider']

    from app.proje.models.proje import Proje
    return render_template('muhasebe/muhasebe_liste.html',
        kalemler=kalemler, ozet=ozet,
        secili_tur=tur, secili_proje=proje_id,
        secili_ay=ay, secili_yil=yil,
        projeler=Proje.query.filter_by(aktif=1).all())


# ── Elle Giriş ───────────────────────────────────────────────────────────────

@muhasebe_bp.route('/yeni', methods=['GET', 'POST'])
@yazma_gerekli
def muhasebe_yeni():
    if request.method == 'POST':
        tur   = request.form.get('tur', 'gelir')
        tutar_str = request.form.get('tutar', '0').replace(',', '.')
        try:
            tutar = float(tutar_str)
        except ValueError:
            tutar = 0

        if tutar <= 0:
            flash('Tutar sıfırdan büyük olmalıdır', 'danger')
        else:
            k = MuhasebeKalem(
                tur          = tur,
                kategori     = request.form.get('kategori', ''),
                aciklama     = request.form.get('aciklama', '').strip(),
                tutar        = tutar,
                para_birimi  = request.form.get('para_birimi', 'TL'),
                tarih        = request.form.get('tarih', datetime.now().strftime('%d.%m.%Y')),
                kaynak       = 'elle',
                proje_id     = request.form.get('proje_id') or None,
                olusturan_id = session.get('kullanici_id'),
            )
            db.session.add(k)
            db.session.commit()
            flash(f'{"Gelir" if tur == "gelir" else "Gider"} kaydedildi', 'success')
            return redirect(url_for('muhasebe.muhasebe_liste'))

    from app.proje.models.proje import Proje
    return render_template('muhasebe/muhasebe_form.html',
        projeler=Proje.query.filter_by(aktif=1).all(),
        gelir_kategoriler=GELIR_KATEGORILERI,
        gider_kategoriler=GIDER_KATEGORILERI)


# ── Sil ─────────────────────────────────────────────────────────────────────

@muhasebe_bp.route('/<int:id>/sil', methods=['POST'])
@yazma_gerekli
def muhasebe_sil(id):
    k = MuhasebeKalem.query.get_or_404(id)
    if k.kaynak != 'elle':
        flash('Otomatik oluşturulan kayıtlar silinemez', 'warning')
        return redirect(url_for('muhasebe.muhasebe_liste'))
    db.session.delete(k)
    db.session.commit()
    flash('Kayıt silindi', 'success')
    return redirect(url_for('muhasebe.muhasebe_liste'))


# ── Fatura Entegrasyonu ──────────────────────────────────────────────────────

def fatura_muhasebe_kaydet(fatura):
    """Fatura kesilince otomatik muhasebe kaydı oluştur"""
    try:
        tur = 'gelir' if fatura.fatura_tipi == 'satis' else 'gider'
        kategori = 'Satış Geliri' if tur == 'gelir' else 'Hammadde / Malzeme'
        musteri = fatura.musteri_adi or (fatura.tedarikci.unvan if fatura.tedarikci else '—')

        k = MuhasebeKalem(
            tur          = tur,
            kategori     = kategori,
            aciklama     = f'Fatura: {fatura.fatura_no} — {musteri}',
            tutar        = fatura.genel_toplam,
            para_birimi  = fatura.para_birimi,
            tarih        = fatura.fatura_tarihi,
            kaynak       = 'fatura',
            kaynak_id    = fatura.id,
            fatura_no    = fatura.fatura_no,
        )
        db.session.add(k)
        db.session.commit()
    except Exception:
        pass
