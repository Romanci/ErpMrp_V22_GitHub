// Ana JavaScript dosyasi

// Flash mesajlarini otomatik kapat
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.remove();
            }, 300);
        }, 5000);
    });
    
    // Sayfa yuklenince aktif menuyu ac ve vurgula
    const currentPath = window.location.pathname;
    const menuLinks = document.querySelectorAll('.submenu a');
    
    menuLinks.forEach(link => {
        const href = link.getAttribute('href');
        // Tam eslesme veya alt sayfa kontrolu
        if (href && (currentPath === href || currentPath.startsWith(href.split('?')[0]))) {
            link.classList.add('active-link');
            // Ust submenu'yu ac
            const submenu = link.closest('.submenu');
            if (submenu) {
                submenu.classList.add('active');
            }
        }
    });
});

// Silme onayi
function silmeOnayi(mesaj) {
    return confirm(mesaj || 'Silmek istediginize emin misiniz?');
}


// Silme onayi
function silmeOnayi(mesaj) {
    return confirm(mesaj || 'Silmek istediginize emin misiniz?');
}

// Tablo satirina cift tiklama
document.addEventListener('DOMContentLoaded', function() {
    const tabloSatirlari = document.querySelectorAll('.data-table tbody tr');
    tabloSatirlari.forEach(function(satir) {
        satir.style.cursor = 'pointer';
        satir.addEventListener('dblclick', function() {
            const duzenleLink = this.querySelector('a[href*="duzenle"]');
            if (duzenleLink) {
                window.location.href = duzenleLink.href;
            }
        });
    });
});