"""
Kurulum profili uygula.
Kullanım: python profil_uygula.py muhasebe
          python profil_uygula.py yonetici
          python profil_uygula.py admin_tam
"""
import sys
import os
import json

profil_dir = os.path.join(os.path.dirname(__file__), 'kurulum_profilleri')
modul_dosya = os.path.join(os.path.dirname(__file__), 'moduller.json')

if len(sys.argv) < 2:
    print("Kullanım: python profil_uygula.py <profil_adi>")
    print("Mevcut profiller:")
    for f in os.listdir(profil_dir):
        if f.endswith('.json'):
            with open(os.path.join(profil_dir, f)) as fp:
                p = json.load(fp)
                print(f"  {f.replace('.json','')} - {p.get('profil_adi','')}")
    sys.exit(1)

profil_adi = sys.argv[1]
if not profil_adi.endswith('.json'):
    profil_adi += '.json'
profil_yolu = os.path.join(profil_dir, profil_adi)

if not os.path.exists(profil_yolu):
    print(f"Hata: {profil_adi} bulunamadı")
    sys.exit(1)

with open(profil_yolu) as f:
    profil = json.load(f)

with open(modul_dosya, 'w', encoding='utf-8') as f:
    json.dump(profil['moduller'], f, ensure_ascii=False, indent=2)

print(f"✓ '{profil['profil_adi']}' profili uygulandı")
print(f"  Sunucuyu yeniden başlatın: ./baslat.sh")
