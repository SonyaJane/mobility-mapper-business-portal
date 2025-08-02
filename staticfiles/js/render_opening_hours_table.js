function renderOpeningHoursTable(opening_hours) {
    if (!opening_hours) return '';
    let oh;
    try {
        oh = typeof opening_hours === 'string' ? JSON.parse(opening_hours) : opening_hours;
    } catch (e) {
        return '';
    }
    let html = `
        <div class="my-2"><strong>Opening Hours:</strong></div>
        <div class="table-responsive">
            <table class="table table-bordered table-sm w-auto mb-0" id="opening-hours-table-dashboard">
                <tbody>
    `;
    Object.entries(oh).forEach(([day, info]) => {
        html += `<tr>
            <td class="px-2"><strong>${day}</strong></td>
            <td class="px-2">`;
        if (info.closed) {
            html += `<span class="text-muted">Closed</span>`;
        } else if (info.periods && info.periods.length) {
            html += info.periods.map((p, idx) =>
                `<span>${p.open} - ${p.close}</span>${idx < info.periods.length - 1 ? '<br>' : ''}`
            ).join('');
        } else {
            html += `<span class="text-muted">No hours set</span>`;
        }
        html += `</td></tr>`;
    });
    html += `
                </tbody>
            </table>
        </div>
    `;
    return html;
}