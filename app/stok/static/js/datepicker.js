/**
 * ERP Tarih Seçici — CDN bağımlılığı yok
 * class="datepicker" olan tüm input'lara otomatik uygulanır
 * Format: GG.AA.YYYY
 */
(function () {
    'use strict';

    const AYLAR = ['Ocak','Şubat','Mart','Nisan','Mayıs','Haziran',
                   'Temmuz','Ağustos','Eylül','Ekim','Kasım','Aralık'];
    const GUNLER = ['Pt','Sa','Ça','Pe','Cu','Ct','Pz'];

    function padZ(n) { return String(n).padStart(2, '0'); }

    function parseDate(str) {
        if (!str) return null;
        const p = str.split('.');
        if (p.length === 3) {
            const d = parseInt(p[0]), m = parseInt(p[1]) - 1, y = parseInt(p[2]);
            if (!isNaN(d) && !isNaN(m) && !isNaN(y)) return new Date(y, m, d);
        }
        return null;
    }

    function formatDate(date) {
        return padZ(date.getDate()) + '.' + padZ(date.getMonth() + 1) + '.' + date.getFullYear();
    }

    function createCalendar(input) {
        if (input._dpAttached) return;
        input._dpAttached = true;

        let current = parseDate(input.value) || new Date();
        let viewYear = current.getFullYear();
        let viewMonth = current.getMonth();
        let popup = null;

        function buildCalendar() {
            const div = document.createElement('div');
            div.className = 'dp-popup';
            div.style.cssText = `
                position:absolute; z-index:99999; background:#fff;
                border:1px solid #e2e8f0; border-radius:10px;
                box-shadow:0 8px 32px rgba(0,0,0,0.18);
                padding:12px; min-width:260px; font-size:13px;
                font-family:inherit;
            `;

            // Header
            const header = document.createElement('div');
            header.style.cssText = 'display:flex;align-items:center;justify-content:space-between;margin-bottom:8px;';

            const btnPrev = document.createElement('button');
            btnPrev.type = 'button';
            btnPrev.innerHTML = '&#8249;';
            btnPrev.style.cssText = 'background:#1e293b;color:#fff;border:none;border-radius:6px;width:28px;height:28px;cursor:pointer;font-size:18px;line-height:1;';

            const btnNext = document.createElement('button');
            btnNext.type = 'button';
            btnNext.innerHTML = '&#8250;';
            btnNext.style.cssText = btnPrev.style.cssText;

            const title = document.createElement('span');
            title.style.cssText = 'font-weight:700;color:#1e293b;cursor:pointer;';
            title.textContent = AYLAR[viewMonth] + ' ' + viewYear;

            btnPrev.onclick = function(e) {
                e.stopPropagation();
                viewMonth--;
                if (viewMonth < 0) { viewMonth = 11; viewYear--; }
                rerender();
            };
            btnNext.onclick = function(e) {
                e.stopPropagation();
                viewMonth++;
                if (viewMonth > 11) { viewMonth = 0; viewYear++; }
                rerender();
            };

            header.appendChild(btnPrev);
            header.appendChild(title);
            header.appendChild(btnNext);
            div.appendChild(header);

            // Hızlı yıl seçimi
            const yilRow = document.createElement('div');
            yilRow.style.cssText = 'display:flex;gap:4px;margin-bottom:8px;flex-wrap:wrap;';
            const yilBaslangic = new Date().getFullYear() - 2;
            for (let y = yilBaslangic; y <= yilBaslangic + 5; y++) {
                const btn = document.createElement('button');
                btn.type = 'button';
                btn.textContent = y;
                btn.style.cssText = `padding:2px 6px;border:1px solid #e2e8f0;border-radius:4px;
                    cursor:pointer;font-size:11px;background:${y === viewYear ? '#1e293b' : '#f8fafc'};
                    color:${y === viewYear ? '#fff' : '#374151'};`;
                btn.onclick = function(e) {
                    e.stopPropagation();
                    viewYear = y;
                    rerender();
                };
                yilRow.appendChild(btn);
            }
            div.appendChild(yilRow);

            // Gün başlıkları
            const grid = document.createElement('div');
            grid.style.cssText = 'display:grid;grid-template-columns:repeat(7,1fr);gap:2px;';

            // Pazartesi başlangıç
            GUNLER.forEach(function(g) {
                const cell = document.createElement('div');
                cell.textContent = g;
                cell.style.cssText = 'text-align:center;font-weight:600;color:#64748b;padding:4px 0;font-size:11px;';
                grid.appendChild(cell);
            });

            // Ayın ilk günü (Pt=1'den başla)
            const firstDay = new Date(viewYear, viewMonth, 1);
            let startDow = firstDay.getDay(); // 0=Pazar
            startDow = (startDow === 0) ? 6 : startDow - 1; // Pazartesi=0

            for (let i = 0; i < startDow; i++) {
                grid.appendChild(document.createElement('div'));
            }

            const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
            const today = new Date();
            const selected = parseDate(input.value);

            for (let d = 1; d <= daysInMonth; d++) {
                const cell = document.createElement('button');
                cell.type = 'button';
                cell.textContent = d;

                const isToday = (d === today.getDate() && viewMonth === today.getMonth() && viewYear === today.getFullYear());
                const isSel = selected && (d === selected.getDate() && viewMonth === selected.getMonth() && viewYear === selected.getFullYear());

                cell.style.cssText = `
                    text-align:center;padding:5px 2px;border:none;border-radius:6px;
                    cursor:pointer;font-size:13px;width:100%;
                    background:${isSel ? '#f59e0b' : isToday ? '#fef3c7' : 'transparent'};
                    color:${isSel ? '#fff' : '#1e293b'};
                    font-weight:${isSel || isToday ? '700' : '400'};
                `;

                cell.onmouseover = function() {
                    if (!isSel) this.style.background = '#fef3c7';
                };
                cell.onmouseout = function() {
                    if (!isSel) this.style.background = isToday ? '#fef3c7' : 'transparent';
                };

                (function(day) {
                    cell.onclick = function(e) {
                        e.stopPropagation();
                        const date = new Date(viewYear, viewMonth, day);
                        input.value = formatDate(date);
                        input.dispatchEvent(new Event('change', {bubbles: true}));
                        closePopup();
                    };
                })(d);

                grid.appendChild(cell);
            }
            div.appendChild(grid);

            // Bugün butonu
            const footer = document.createElement('div');
            footer.style.cssText = 'margin-top:8px;text-align:center;';
            const btnToday = document.createElement('button');
            btnToday.type = 'button';
            btnToday.textContent = 'Bugün';
            btnToday.style.cssText = 'padding:4px 16px;background:#1e293b;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:12px;';
            btnToday.onclick = function(e) {
                e.stopPropagation();
                const t = new Date();
                input.value = formatDate(t);
                input.dispatchEvent(new Event('change', {bubbles: true}));
                closePopup();
            };
            footer.appendChild(btnToday);
            div.appendChild(footer);

            return div;
        }

        function rerender() {
            if (popup) {
                const newPopup = buildCalendar();
                popup.parentNode.replaceChild(newPopup, popup);
                popup = newPopup;
            }
        }

        function showPopup() {
            closeAllPopups();
            current = parseDate(input.value) || new Date();
            viewYear = current.getFullYear();
            viewMonth = current.getMonth();

            popup = buildCalendar();

            // Konumlandır
            const rect = input.getBoundingClientRect();
            const scrollTop = window.scrollY || document.documentElement.scrollTop;
            const scrollLeft = window.scrollX || document.documentElement.scrollLeft;

            popup.style.top = (rect.bottom + scrollTop + 4) + 'px';
            popup.style.left = (rect.left + scrollLeft) + 'px';

            document.body.appendChild(popup);

            // Ekran sınırı kontrolü
            setTimeout(function() {
                const popRect = popup.getBoundingClientRect();
                if (popRect.right > window.innerWidth) {
                    popup.style.left = (rect.right + scrollLeft - popRect.width) + 'px';
                }
                if (popRect.bottom > window.innerHeight) {
                    popup.style.top = (rect.top + scrollTop - popRect.height - 4) + 'px';
                }
            }, 0);
        }

        function closePopup() {
            if (popup) {
                popup.remove();
                popup = null;
            }
        }

        // Input'a tıklayınca aç
        input.addEventListener('click', function(e) {
            e.stopPropagation();
            if (popup) { closePopup(); } else { showPopup(); }
        });

        input.addEventListener('focus', function() {
            if (!popup) showPopup();
        });

        // Placeholder
        if (!input.placeholder) input.placeholder = 'GG.AA.YYYY';
    }

    function closeAllPopups() {
        document.querySelectorAll('.dp-popup').forEach(function(p) { p.remove(); });
    }

    // Dışarı tıklayınca kapat
    document.addEventListener('click', closeAllPopups);

    // DOMContentLoaded'da tüm .datepicker'lara uygula
    function applyToAll() {
        document.querySelectorAll('input.datepicker').forEach(createCalendar);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', applyToAll);
    } else {
        applyToAll();
    }

    // Dinamik eklenenler için (MutationObserver)
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(m) {
            m.addedNodes.forEach(function(node) {
                if (node.nodeType === 1) {
                    if (node.matches && node.matches('input.datepicker')) createCalendar(node);
                    node.querySelectorAll && node.querySelectorAll('input.datepicker').forEach(createCalendar);
                }
            });
        });
    });
    observer.observe(document.body, {childList: true, subtree: true});

    // Global erişim
    window.ERPDatepicker = { apply: applyToAll, create: createCalendar };
})();
