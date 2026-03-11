import os

def dizin_yapisi(yol='.'):
    for kok, dizinler, dosyalar in os.walk(yol):
        # .git, __pycache__ veya .venv gibi gereksizleri gizleyelim
        dizinler[:] = [d for d in dizinler if not d.startswith(('.', '__'))]
        
        seviye = kok.replace(yol, '').count(os.sep)
        girinti = ' ' * 4 * seviye
        print(f'{girinti}{os.path.basename(kok)}/')
        
        alt_girinti = ' ' * 4 * (seviye + 1)
        for f in dosyalar:
            if not f.startswith('.'): # Gizli dosyaları gösterme
                print(f'{alt_girinti}{f}')

dizin_yapisi()
