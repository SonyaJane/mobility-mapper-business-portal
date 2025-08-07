// Register Business JavaScript
// Billing frequency logic
export default function updatePrices() {
    const selected = document.querySelector('input[name="billing_frequency"]:checked');
    const yearly = selected && selected.value.toLowerCase() === 'yearly';

    document.querySelectorAll('.price-display').forEach(el => {
        const priceMonth = parseFloat(el.dataset.priceMonth).toFixed(2);
        const priceYear = parseFloat(el.dataset.priceYear).toFixed(2);
        const main = el.querySelector('.price-main');
        const alt = el.querySelector('.price-alt');

        if (yearly && priceYear > 0) {
            main.textContent = `£${priceYear} / year`;
            if (alt) alt.textContent = `or £${priceMonth} / month`;
        } else {
            main.textContent = `£${priceMonth} / month`;
            if (alt && priceYear > 0) alt.textContent = `or £${priceYear} / year`;
        }
    });
}
