export default function syncSelects(selectIds) {
    // Sync all accessibility filter selects
    selectIds.forEach(id => {
        const el = document.getElementById(id);
        if (el) {
        el.addEventListener('change', function() {
            selectIds.forEach(otherId => {
            if (otherId !== id) {
                const otherEl = document.getElementById(otherId);
                if (otherEl) otherEl.value = el.value;
            }
            });
            // Optionally trigger your filtering logic here
            if (typeof window.filterBusinesses === 'function') {
            window.filterBusinesses();
            }
        });
        }
    });
    }