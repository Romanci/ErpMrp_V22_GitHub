# Uygulama ayarlarinin tutuldugu dosya
import os

# Proje klasorunun tam yolu
BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Veritabani dosya yolu
DATABASE_PATH = os.path.join(BASE_DIR, 'database.db')

# Flask ayarlari
class Config:
    # Guvenlik anahtari - production'da SECRET_KEY env degiskenini set edin!
    # Ornek: export SECRET_KEY="guclu-rastgele-anahtar-buraya"
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'erp-mrp-dev-key-lutfen-production-icin-degistirin'
    
    # Veritabani baglanti adresi - alternatif db icin DATABASE_URL env kullanin
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or f'sqlite:///{DATABASE_PATH}'
    
    # SQL sorgu loglarini kapat (performans icin)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Turkce tarih formati
    DATE_FORMAT = '%d.%m.%Y'
