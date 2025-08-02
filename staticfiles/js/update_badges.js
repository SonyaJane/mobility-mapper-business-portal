// Function to render selected accessibility badges with remove buttons
export default function updateBadges() {
    const select = document.getElementById('accessibility-select');
    const container = document.getElementById('accessibility-badges');
    if (!select || !container) return;
    container.innerHTML = '';
    Array.from(select.selectedOptions).forEach(opt => {
        const badge = document.createElement('span');
        badge.className = 'badge bg-secondary me-1 d-inline-flex align-items-center';
        badge.textContent = opt.value;
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'btn-close btn-close-white btn-sm ms-1';
        btn.setAttribute('aria-label', 'Remove');
        btn.addEventListener('click', e => {
            e.stopPropagation();
            opt.selected = false;
            updateBadges();
            filterBusinesses();
        });
        badge.appendChild(btn);
        container.appendChild(badge);
    });
}