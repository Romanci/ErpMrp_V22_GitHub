// Ana JavaScript dosyasi - tum uygulama icin ortak fonksiyonlar

// Flash mesajlarini otomatik kapat
document.addEventListener('DOMContentLoaded', function() {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            alert.style.opacity = '0';
            setTimeout(function() {
                alert.remove();
            }, 300);
        }, 3000);
    });
});

// Silme islemi onayi
function silmeOnayi(mesaj) {
    return confirm(mesaj || 'Silmek istediginize emin misiniz?');
}

// Sayfa yuklenirken calisacak fonksiyonlar
document.addEventListener('DOMContentLoaded', function() {
    // Tablo satirlarina cift tiklama ile detay acma
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