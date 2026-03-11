#!/bin/bash
# ERP MRP v0.8 - Linux/Mac Kurulum Scripti

set -e  # Hata olursa dur

echo "================================================"
echo "  ERP MRP v0.8 - Kurulum"
echo "================================================"
echo ""

# Script'in bulundugu dizine git
cd "$(dirname "$0")"

# ── 1. Python kontrolu ──────────────────────────────
echo "[1/5] Python kontrol ediliyor..."
if command -v python3 &> /dev/null; then
    PYTHON=python3
elif command -v python &> /dev/null && python --version 2>&1 | grep -q "Python 3"; then
    PYTHON=python
else
    echo "HATA: Python 3 bulunamadi!"
    echo "  Ubuntu/Debian : sudo apt install python3 python3-pip python3-venv"
    echo "  Mac           : brew install python3"
    exit 1
fi
echo "  Bulundu: $($PYTHON --version)"

# ── 2. Sanal ortam ──────────────────────────────────
echo ""
echo "[2/5] Sanal ortam (venv) hazirlaniyor..."
if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
    echo "  venv olusturuldu"
else
    echo "  venv zaten mevcut"
fi

# venv'i aktif et
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
elif [ -f "venv/Scripts/activate" ]; then
    source venv/Scripts/activate
else
    echo "HATA: venv aktivasyon dosyasi bulunamadi!"
    exit 1
fi
echo "  venv aktif: $(which python)"

# ── 3. Kutuphaneler ─────────────────────────────────
echo ""
echo "[3/5] Kutuphaneler yukleniyor (1-3 dakika)..."
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet
echo "  Tum kutuphaneler yuklendi"

# ── 4. Veritabani ───────────────────────────────────
echo ""
echo "[4/5] Veritabani kontrol ediliyor..."
python -c "
from app import create_app, db
app = create_app()
print('  Veritabani hazir')
"

# Yerel IP adresini tespit etme
IP_ADDR=$(hostname -I | awk '{print $1}')

# ── 5. Sunucu ───────────────────────────────────────
echo ""
echo "[5/5] Sunucu baslatiliyor..."
echo ""
echo "================================================"
echo "  Uygulama hazir!"
echo "  Yerel Adres : http://$IP_ADDR:5001"
echo "  Giris       : admin / admin123"
echo "  Kapatma     : Ctrl+C"
echo "================================================"
echo ""

# Flask'ı tüm arayüzlerde dinleyecek şekilde başlat (0.0.0.0)
flask run --host=0.0.0.0 --port=5001
python run.py
