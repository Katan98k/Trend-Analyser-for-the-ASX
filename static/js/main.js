/**
 * ---------------------------------------------------------
 * Trend Analyzer for the ASX
 * Shared Interface Controller
 *
 * Provides sidebar controls, alert handling, progress display,
 * history filtering, and safe ticker input formatting.
 *
 * Author: Karan Attavar
 * ---------------------------------------------------------
 */
document.addEventListener('DOMContentLoaded', () => {
    const body = document.body;
    const sidebarToggles = document.querySelectorAll('[data-sidebar-toggle]');

    function setSidebar(open) {
        body.classList.toggle('sidebar-open', open);
        sidebarToggles.forEach(toggle => toggle.setAttribute('aria-expanded', String(open)));
    }

    sidebarToggles.forEach(toggle => {
        toggle.addEventListener('click', () => setSidebar(!body.classList.contains('sidebar-open')));
    });

    document.addEventListener('keydown', event => {
        if (event.key === 'Escape') setSidebar(false);
    });

    document.querySelectorAll('.alert').forEach(alert => {
        window.setTimeout(() => {
            if (!document.body.contains(alert) || !window.bootstrap) return;
            alert.style.opacity = '0';
            alert.style.transition = 'opacity 0.35s ease';
            window.setTimeout(() => bootstrap.Alert.getOrCreateInstance(alert).close(), 350);
        }, 6000);
    });

    document.querySelectorAll('[data-progress-width]').forEach(element => {
        const value = Number.parseFloat(element.dataset.progressWidth);
        element.style.width = `${Math.min(100, Math.max(0, Number.isFinite(value) ? value : 0))}%`;
    });

    const searchInput = document.getElementById('tableSearchInput');
    const tableBody = document.getElementById('historyTableBody');
    if (searchInput && tableBody) {
        searchInput.addEventListener('input', () => {
            const filter = searchInput.value.toLowerCase();
            Array.from(tableBody.rows).forEach(row => {
                row.hidden = !row.textContent.toLowerCase().includes(filter);
            });
        });
    }

    const tickerInput = document.querySelector('input[name="ticker"]');
    if (tickerInput) {
        tickerInput.addEventListener('input', event => {
            event.target.value = event.target.value.toUpperCase().replace(/[^A-Z0-9]/g, '').slice(0, 5);
        });
    }
});
