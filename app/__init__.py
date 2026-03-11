# Ana uygulama fabrikası
from flask import Flask, session, redirect, url_for, request, g
from flask_sqlalchemy import SQLAlchemy
from config import Config
import os

db = SQLAlchemy()
ACIK_URLLAR = ['/kullanici/giris', '/static/']


def login_gerekli_mi(endpoint, path):
    for acik in ACIK_URLLAR:
        if path.startswith(acik):
            return False
    return True


def create_app():
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'stok', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'stok', 'static'))

    flask_app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    flask_app.config.from_object(Config)
    db.init_app(flask_app)

    # Modül durumlarını flask_app context'e ekle
    from app.modul_yonetici import modul_durumları
    moduller = modul_durumları()

    # ── Temel blueprint'ler (her zaman yüklü) ──────────────────────────────
    from app.stok.routes.urun_routes import stok_bp
    from app.stok.routes.stok_hareket_routes import hareket_bp
    from app.stok.routes.depo_routes import depo_bp
    from app.stok.routes.parti_routes import parti_bp
    from app.stok.routes.sayim_routes import sayim_bp
    from app.stok.routes.rapor_routes import rapor_bp
    from app.stok.routes.gelismis_rapor_routes import gelismis_rapor_bp
    from app.stok.routes.kategori_routes import kategori_bp
    from app.stok.routes.export_routes import export_bp
    from app.stok.routes.import_routes import import_bp
    from app.stok.routes.yedek_routes import yedek_bp
    from app.stok.routes.ayar_routes import ayar_bp
    from app.stok.routes.sube_routes import sube_bp
    from app.stok.routes.email_routes import email_bp
    from app.stok.routes.barkod_routes import barkod_bp
    from app.stok.routes.bildirim_routes import bildirim_bp
    from app.stok.routes.arama_routes import arama_bp
    from app.kullanici.routes.kullanici_routes import kullanici_bp
    from app.routes import main_bp
    from app.stok.routes.modul_ayar_routes import modul_ayar_bp

    flask_app.register_blueprint(main_bp)
    flask_app.register_blueprint(stok_bp, url_prefix='/stok')
    flask_app.register_blueprint(hareket_bp, url_prefix='/stok')
    flask_app.register_blueprint(depo_bp, url_prefix='/stok')
    flask_app.register_blueprint(parti_bp, url_prefix='/stok')
    flask_app.register_blueprint(sayim_bp, url_prefix='/stok')
    flask_app.register_blueprint(rapor_bp, url_prefix='/stok')
    flask_app.register_blueprint(gelismis_rapor_bp, url_prefix='/stok')
    flask_app.register_blueprint(kategori_bp, url_prefix='/stok')
    flask_app.register_blueprint(export_bp, url_prefix='/stok')
    flask_app.register_blueprint(import_bp, url_prefix='/stok')
    flask_app.register_blueprint(yedek_bp, url_prefix='/stok')
    flask_app.register_blueprint(ayar_bp, url_prefix='/stok')
    flask_app.register_blueprint(sube_bp, url_prefix='/stok')
    flask_app.register_blueprint(email_bp, url_prefix='/stok')
    flask_app.register_blueprint(barkod_bp, url_prefix='/stok')
    flask_app.register_blueprint(bildirim_bp, url_prefix='/stok')
    flask_app.register_blueprint(arama_bp, url_prefix='/stok')
    flask_app.register_blueprint(kullanici_bp, url_prefix='/kullanici')
    flask_app.register_blueprint(modul_ayar_bp, url_prefix='/admin')

    # ── Koşullu blueprint'ler ───────────────────────────────────────────────
    if moduller.get('satin_alma'):
        from app.satin_alma.routes.tedarikci_routes import tedarikci_bp
        from app.satin_alma.routes.siparis_routes import siparis_bp as sa_siparis_bp
        flask_app.register_blueprint(tedarikci_bp, url_prefix='/satin-alma')
        flask_app.register_blueprint(sa_siparis_bp, url_prefix='/satin-alma')

    if moduller.get('uretim'):
        from app.uretim.routes.uretim_emri_routes import uretim_bp
        from app.uretim.routes.tezgah_routes import tezgah_bp
        from app.uretim.routes.bom_routes import bom_bp
        from app.uretim.routes.mrp_routes import mrp_bp
        from app.uretim.routes.maliyet_routes import maliyet_bp
        from app.uretim.routes.kapasite_routes import kapasite_bp
        flask_app.register_blueprint(uretim_bp, url_prefix='/uretim')
        flask_app.register_blueprint(tezgah_bp, url_prefix='/uretim')
        flask_app.register_blueprint(bom_bp, url_prefix='/uretim')
        flask_app.register_blueprint(mrp_bp, url_prefix='/uretim')
        flask_app.register_blueprint(maliyet_bp, url_prefix='/uretim')
        flask_app.register_blueprint(kapasite_bp, url_prefix='/uretim')

    if moduller.get('fatura'):
        from app.fatura.routes.fatura_routes import fatura_bp
        flask_app.register_blueprint(fatura_bp, url_prefix='/fatura')

    if moduller.get('ik'):
        from app.ik.routes.personel_routes import ik_bp
        from app.ik.routes.zkteco_routes import zk_bp
        flask_app.register_blueprint(ik_bp, url_prefix='/ik')
        flask_app.register_blueprint(zk_bp, url_prefix='/ik')

    if moduller.get('bakim'):
        from app.bakim.routes.bakim_routes import bakim_bp
        flask_app.register_blueprint(bakim_bp, url_prefix='/bakim')

    if moduller.get('crm'):
        from app.crm.routes.crm_routes import crm_bp
        flask_app.register_blueprint(crm_bp, url_prefix='/crm')

    if moduller.get('kalite'):
        from app.kalite.routes.kalite_routes import kalite_bp
        flask_app.register_blueprint(kalite_bp, url_prefix='/kalite')

    if moduller.get('dokuman'):
        from app.dokuman.routes.dokuman_routes import dokuman_bp
        flask_app.register_blueprint(dokuman_bp, url_prefix='/dokuman')

    if moduller.get('arac'):
        from app.arac.routes.arac_routes import arac_bp
        flask_app.register_blueprint(arac_bp, url_prefix='/arac')

    if moduller.get('vardiya'):
        from app.vardiya.routes.vardiya_routes import vardiya_bp
        flask_app.register_blueprint(vardiya_bp, url_prefix='/vardiya')

    if moduller.get('proje'):
        from app.proje.routes.proje_routes import proje_bp
        flask_app.register_blueprint(proje_bp, url_prefix='/proje')

    if moduller.get('siparis'):
        from app.siparis.routes.siparis_routes import siparis_bp
        flask_app.register_blueprint(siparis_bp, url_prefix='/siparis')

    if moduller.get('muhasebe'):
        from app.muhasebe.routes.muhasebe_routes import muhasebe_bp
        flask_app.register_blueprint(muhasebe_bp, url_prefix='/muhasebe')

    # ── Context Processors ──────────────────────────────────────────────────
    @flask_app.context_processor
    def inject_moduller():
        return {'aktif_moduller': moduller}

    @flask_app.context_processor
    def inject_firma_ayarlari():
        """Firma adı, logo ve sistem ayarlarını tüm şablonlara enjekte et"""
        try:
            from app.stok.models.sistem_ayar import SistemAyar
            return {
                'firma_adi':        SistemAyar.get('firma_adi', 'ERP Sistem'),
                'firma_alt_baslik': SistemAyar.get('firma_alt_baslik', 'Yönetim Sistemi'),
                'firma_logo':       SistemAyar.get('firma_logo', ''),
            }
        except Exception:
            return {'firma_adi': 'ERP Sistem', 'firma_alt_baslik': 'Yönetim Sistemi', 'firma_logo': ''}

    @flask_app.context_processor
    def kullanici_yetkileri():
        yetki = {
            'stok': True, 'satin_alma': True, 'uretim': True, 'fatura': True,
            'ik': False, 'bakim': False, 'crm': False, 'kalite': False,
            'dokuman': False, 'arac': False, 'vardiya': False, 'muhasebe': False,
            'yazma': False, 'silme': False, 'admin': False,
        }
        if session.get('admin') or session.get('kullanici_id'):
            if session.get('admin'):
                yetki = {k: True for k in yetki}
            else:
                from app.kullanici.models.kullanici import Kullanici
                k = Kullanici.query.get(session.get('kullanici_id'))
                if k:
                    rol = k.birincil_rol()
                    if rol:
                        for alan in ['stok', 'satin_alma', 'uretim', 'ik', 'bakim',
                                     'crm', 'kalite', 'dokuman', 'arac', 'vardiya', 'muhasebe']:
                            yetki[alan] = bool(getattr(rol, f'{alan}_erisim', 0))
                        yetki['yazma'] = bool(rol.yazma_izni)
                        yetki['silme'] = bool(rol.silme_izni)
                    if k.admin_mi():
                        yetki = {k2: True for k2 in yetki}
        # Modül kapalıysa yetkiyi de kapat
        for m in ['satin_alma', 'uretim', 'fatura', 'ik', 'bakim',
                  'crm', 'kalite', 'dokuman', 'arac', 'vardiya', 'muhasebe']:
            if not moduller.get(m):
                yetki[m] = False
        return {'yetki': yetki}

    @flask_app.context_processor
    def inject_now():
        from datetime import datetime
        return {'now': datetime.now}

    # ── Before Request ───────────────────────────────────────────────────────
    @flask_app.before_request
    def giris_kontrol():
        if not login_gerekli_mi(request.endpoint, request.path):
            return
        if not session.get('kullanici_id'):
            return redirect(url_for('kullanici.giris'))
        # Modül erişim kontrolü
        if not session.get('admin'):
            path = request.path
            modul_path_map = {
                '/satin-alma': 'satin_alma', '/uretim': 'uretim', '/fatura': 'fatura',
                '/ik': 'ik', '/bakim': 'bakim', '/crm': 'crm', '/kalite': 'kalite',
                '/dokuman': 'dokuman', '/arac': 'arac', '/vardiya': 'vardiya',
            }
            for prefix, modul_adi in modul_path_map.items():
                if path.startswith(prefix):
                    if not moduller.get(modul_adi):
                        return redirect(url_for('main.dashboard'))
                    break

    # ── DB Oluştur ──────────────────────────────────────────────────────────
    with flask_app.app_context():
        # Tüm modeller db.create_all() öncesi import edilmeli
        import app.stok.models.urun
        import app.stok.models.stok_hareket
        import app.stok.models.depo
        import app.stok.models.parti
        import app.stok.models.kategori
        import app.stok.models.sayim
        import app.stok.models.sistem_ayar
        import app.stok.models.sube
        import app.kullanici.models.kullanici
        import app.satin_alma.models.tedarikci
        import app.satin_alma.models.siparis
        import app.uretim.models.uretim_emri
        import app.uretim.models.tezgah
        import app.uretim.models.bom
        import app.ik.models.personel
        import app.bakim.models.bakim
        import app.fatura.models.fatura
        import app.crm.models.crm
        import app.kalite.models.kalite
        import app.dokuman.models.dokuman
        import app.arac.models.arac
        import app.vardiya.models.vardiya
        import app.proje.models.proje
        import app.siparis.models.siparis
        import app.muhasebe.models.muhasebe
        import app.stok.models.bildirim
        db.create_all()
        _varsayilan_verileri_olustur()

    return flask_app


def _varsayilan_verileri_olustur():
    """İlk kurulumda admin ve rolleri oluştur"""
    from app.kullanici.models.kullanici import Kullanici, Rol, KullaniciRol
    from app.kullanici.models.kullanici import sifre_hashle

    # Rolleri oluştur/güncelle
    roller_tanim = [
        ('admin',    'Tam yetki - tüm modüller',
         dict(stok=1, satin_alma=1, uretim=1, ik=1, bakim=1, crm=1, kalite=1, dokuman=1, arac=1, vardiya=1, muhasebe=1, yazma=1, silme=1)),
        ('mudur',    'Yönetici - tüm modüller görüntüle ve düzenle',
         dict(stok=1, satin_alma=1, uretim=1, ik=1, bakim=1, crm=1, kalite=1, dokuman=1, arac=1, vardiya=1, muhasebe=1, yazma=1, silme=0)),
        ('muhasebe', 'Muhasebe - fatura, satın alma, stok',
         dict(stok=1, satin_alma=1, uretim=0, ik=0, bakim=0, crm=1, kalite=0, dokuman=1, arac=0, vardiya=0, muhasebe=1, yazma=1, silme=0)),
        ('operator', 'Stok ve üretim işlemleri',
         dict(stok=1, satin_alma=1, uretim=1, ik=0, bakim=1, crm=0, kalite=1, dokuman=0, arac=0, vardiya=1, muhasebe=0, yazma=1, silme=0)),
        ('okuyucu',  'Sadece görüntüleme',
         dict(stok=1, satin_alma=1, uretim=1, ik=0, bakim=0, crm=0, kalite=0, dokuman=0, arac=0, vardiya=0, muhasebe=0, yazma=0, silme=0)),
    ]

    for rol_adi, aciklama, izinler in roller_tanim:
        rol = Rol.query.filter_by(rol_adi=rol_adi).first()
        if not rol:
            rol = Rol(rol_adi=rol_adi, aciklama=aciklama)
            db.session.add(rol)
        # Yeni alanları güncelle (migration yerine)
        for alan, deger in izinler.items():
            if hasattr(rol, f'{alan}_erisim'):
                setattr(rol, f'{alan}_erisim', deger)
            elif alan in ('yazma', 'silme'):
                setattr(rol, f'{alan}_izni', deger)

    # Admin kullanıcı yoksa oluştur
    if not Kullanici.query.filter_by(kullanici_adi='admin').first():
        admin = Kullanici(
            kullanici_adi='admin',
            sifre_hash=sifre_hashle('admin123'),
            ad='Sistem', soyad='Yöneticisi',
            email='admin@sistem.local',
        )
        db.session.add(admin)
        db.session.flush()
        admin_rol = Rol.query.filter_by(rol_adi='admin').first()
        if admin_rol:
            db.session.add(KullaniciRol(kullanici_id=admin.id, rol_id=admin_rol.id))

    db.session.commit()
