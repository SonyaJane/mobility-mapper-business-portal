export default function renderOpeningHoursTable(opening_hours) {
    if (!opening_hours) return '';
    // Helper to convert 24h HH:MM to 12h format (e.g., '15:00' -> '3pm')
    function format12h(time) {
        const [h, m] = time.split(':');
        let hour = parseInt(h, 10);
        const suffix = hour < 12 ? 'am' : 'pm';
        hour = hour % 12 || 12;
        return m === '00' ? `${hour}${suffix}` : `${hour}:${m}${suffix}`;
    }
    let oh;
    try {
        oh = typeof opening_hours === 'string' ? JSON.parse(opening_hours) : opening_hours;
    } catch (e) {
        return '';
    }
    let html = `
        <div class="my-2"><i class='bi bi-clock fs-5 me-2 text-green'></i>Opening Hours:</div>
        <div class="table-responsive">
            <table class="table table-bordered table-sm w-auto mb-0 opening-hours-table-dashboard">
                <tbody>
    `;
    Object.entries(oh).forEach(([day, info]) => {
        html += `<tr>
            <td class="px-3 align-middle line-height-16">${day}</td>
            <td class="px-3 align-middle line-height-16">`;
        const periods = Array.isArray(info) ? info : [];
        if (periods.length) {
            html += periods.map((p, idx) =>
                `<span>${format12h(p.start)} - ${format12h(p.end)}</span>` +
                (idx < periods.length - 1 ? '<br>' : '')
            ).join('');
        } else {
            // No periods means closed
            html += `<span class="text-muted line-height-16">Closed</span>`;
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