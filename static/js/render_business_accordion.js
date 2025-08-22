import renderOpeningHoursTable from './render_opening_hours_table.js';

export default function renderBusinessAccordion(biz) {
    let accessibility = '';
    if (biz.accessibility_features && biz.accessibility_features.length) {
        accessibility = biz.accessibility_features.map(f => `<span class='badge accessibility-badge'>${f}</span>`).join(' ');
    }
    let website = biz.website ? `<a href=\"${biz.website}\" target=\"_blank\" class=\"text-orange\"><i class=\"bi bi-globe fs-5 me-2 text-orange\"></i>${biz.website}</a>` : '';
    let facebook = biz.facebook_url ? `<a href=\"${biz.facebook_url}\" target=\"_blank\" class=\"me-2\"><i class=\"bi bi-facebook text-orange\"></i></a>` : '';
    let instagram = biz.instagram_url ? `<a href=\"${biz.instagram_url}\" target=\"_blank\" class=\"me-2\"><i class=\"bi bi-instagram fs-5 me-2 text-orange\"></i></a>` : '';
    let x_twitter = biz.x_twitter_url ? `<a href=\"${biz.x_twitter_url}\" target=\"_blank\" class=\"me-2\"><i class=\"bi bi-twitter-x text-orange\"></i></a>` : '';
    let public_email = biz.public_email ? `<a href=\"mailto:${biz.public_email}\" class=\"text-orange\"><i class=\"bi bi-envelope fs-5 me-2 text-coffee\"></i>${biz.public_email}</a>` : '';
    let phone = biz.public_phone ? `<i class='bi bi-telephone fs-5 me-2 text-green'></i>${biz.public_phone}` : '';
    let description = biz.description ? `<i class='bi bi-card-text fs-5 me-2 text-orange'></i>${biz.description}` : '';
    let services = biz.services_offered ? `<i class='bi bi-briefcase fs-5 me-2 text-mango'></i>${biz.services_offered}` : '';
    let offers = biz.special_offers ? `<i class='bi bi-tag fs-5 me-2 text-coffee'></i>${biz.special_offers}` : '';
    let opening_hours = biz.opening_hours ? renderOpeningHoursTable(biz.opening_hours) : '';
    return `
        <div class=\"accordion-body mt-2 mb-1\">
            ${accessibility ? `<div class=\"mb-2\">${accessibility}</div>` : ''}
            ${website ? `<div class=\"mb-1 text-orange\">${website}</div>` : ''}
            ${(facebook || instagram || x_twitter) ? `<div class=\"mb-1 d-flex flex-row align-items-center\"><i class='bi bi-share fs-5 me-2 text-mango'></i>${facebook}${instagram}${x_twitter}</div>` : ''}
            ${public_email ? `<div class=\"mb-1 text-coffee\">${public_email}</div>` : ''}
            ${phone ? `<div class=\"mb-1 text-green\">${phone}</div>` : ''}
            ${description ? `<div class=\"mb-1\">${description}</div>` : ''}
            ${services ? `<div class=\"mb-1\">${services}</div>` : ''}
            ${offers ? `<div class=\"mb-1\">${offers}</div>` : ''}
            ${opening_hours}
        </div>
    `;
}