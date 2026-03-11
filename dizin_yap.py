# Proje dizinlerini otomatik olusturan kod
import os

# Ana proje dizini
BASE_DIR = "erp_mrp_v04"

# Olusturulacak tum dizinlerin listesi
DIZINLER = [
    # Ana uygulama
    f"{BASE_DIR}/app",
    f"{BASE_DIR}/app/stok",
    f"{BASE_DIR}/app/stok/models",
    f"{BASE_DIR}/app/stok/routes",
    f"{BASE_DIR}/app/stok/templates/stok",
    f"{BASE_DIR}/app/stok/static/css",
    f"{BASE_DIR}/app/stok/static/js",
    f"{BASE_DIR}/app/templates",
    f"{BASE_DIR}/app/static/css",
    f"{BASE_DIR}/app/static/js",
    
    # Migrasyon ve test
    f"{BASE_DIR}/migrations/versions",
    f"{BASE_DIR}/tests/stok",
]

def dizinleri_olustur():
    # Her dizin icin
    for dizin in DIZINLER:
        # Dizin yoksa olustur
        if not os.path.exists(dizin):
            os.makedirs(dizin)
            print(f"Olusturuldu: {dizin}")
        else:
            print(f"Zaten var: {dizin}")

    # __init__.py dosyalarini olustur (Python paketi yapmak icin)
    init_dosyalari = [
        f"{BASE_DIR}/app/__init__.py",
        f"{BASE_DIR}/app/stok/__init__.py",
        f"{BASE_DIR}/app/stok/models/__init__.py",
        f"{BASE_DIR}/app/stok/routes/__init__.py",
    ]
    
    for dosya in init_dosyalari:
        if not os.path.exists(dosya):
            open(dosya, 'w').close()
            print(f"Olusturuldu: {dosya}")

    print("\nTum dizinler hazir!")

# Calistir
if __name__ == "__main__":
    dizinleri_olustur()
