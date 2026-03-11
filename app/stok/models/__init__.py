# Stok modulu modellerinin toplu importu
# Bu dosya sayesinde diger dosyalarda tek tek import etmeye gerek kalmaz

from app.stok.models.urun import Urun
from app.stok.models.kategori import Kategori
from app.stok.models.depo import Depo
from app.stok.models.stok_lokasyon import StokLokasyon
from app.stok.models.stok_hareket import StokHareket
from app.stok.models.parti import Parti
from app.stok.models.sayim import Sayim
from app.stok.models.sayim_duzeltme import SayimDuzeltme

# Disariya acilan modul listesi
__all__ = [
    'Urun',
    'Kategori', 
    'Depo',
    'StokLokasyon',
    'StokHareket',
    'Parti',
    'Sayim',
    'SayimDuzeltme'
]
