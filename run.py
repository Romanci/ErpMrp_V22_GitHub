# -*- coding: utf-8 -*-
"""
ERP Sunucu Başlatıcı
--------------------
Doğrudan çalıştırın: python run.py
"""
import os
import sys
import socket

# Proje kök klasörünü sys.path'e ekle
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# Flask uygulamasını oluştur
# 'app' isim çakışmasını önlemek için __import__ kullan
_app_module = __import__('app', fromlist=['create_app'])
flask_app = _app_module.create_app()

if __name__ == '__main__':
    cert = os.path.join(BASE_DIR, 'ssl', 'cert.pem')
    key  = os.path.join(BASE_DIR, 'ssl', 'key.pem')

    if os.path.exists(cert) and os.path.exists(key):
        ssl_ctx = (cert, key)
        proto   = 'https'
    else:
        ssl_ctx = None
        proto   = 'http'

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = '127.0.0.1'

    print(f"\n  \u2554{'='*46}\u2557")
    print(f"  \u2551  ERP Y\u00f6netim Sistemi Ba\u015flat\u0131ld\u0131{' '*14}\u2551")
    print(f"  \u2560{'='*46}\u2563")
    print(f"  \u2551  Bu bilgisayar    : {proto}://localhost:5000{' '*6}\u2551")
    print(f"  \u2551  A\u011fdaki cihazlar  : {proto}://{ip}:5000{' '*(17-len(ip))}\u2551")
    if ssl_ctx:
        print(f"  \u2551  \U0001f512 HTTPS aktif \u2014 kamera eri\u015fimi a\u00e7\u0131k{' '*9}\u2551")
        print(f"  \u2551  \u26a0  G\u00fcvensiz uyard\u0131 \u00e7\u0131karsa:{' '*19}\u2551")
        print(f"  \u2551     Geli\u015fmi\u015f \u2192 Yine de devam et{' '*13}\u2551")
    print(f"  \u255a{'='*46}\u255d\n")

    flask_app.run(
        host      = '0.0.0.0',
        port      = 5000,
        debug     = False,
        ssl_context = ssl_ctx,
    )
