# Satin alma modulu modellerinin toplu importu

from app.satin_alma.models.tedarikci import Tedarikci
from app.satin_alma.models.siparis import SatinAlmaSiparisi, SatinAlmaSiparisiSatir

__all__ = [
    'Tedarikci',
    'SatinAlmaSiparisi',
    'SatinAlmaSiparisiSatir'
]
