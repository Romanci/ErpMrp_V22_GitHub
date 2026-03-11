# -*- coding: utf-8 -*-
import os, sys, socket

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from app import create_app
uygulama = create_app()

if __name__ == '__main__':
    cert = os.path.join(BASE_DIR, 'ssl', 'cert.pem')
    key  = os.path.join(BASE_DIR, 'ssl', 'key.pem')
    ssl_ctx = (cert, key) if (os.path.exists(cert) and os.path.exists(key)) else None
    proto   = 'https' if ssl_ctx else 'http'

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80)); ip = s.getsockname()[0]; s.close()
    except:
        ip = '127.0.0.1'

    print(f"\n  ERP Yönetim Sistemi Başlatıldı")
    print(f"  Bu bilgisayar   : {proto}://localhost:5000")
    print(f"  Ağdaki cihazlar : {proto}://{ip}:5000")
    if ssl_ctx:
        print(f"  HTTPS aktif - kamera erişimi açık")
        print(f"  Güvensiz uyarısı çıkarsa: Gelişmiş > Yine de devam et")
    print()

    uygulama.run(host='0.0.0.0', port=5000, debug=False, ssl_context=ssl_ctx)
