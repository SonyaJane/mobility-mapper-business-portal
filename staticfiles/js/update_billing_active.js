// Billing frequency listeners
export default function updateBillingActive() {
    const radios = document.querySelectorAll('input[name="billing_frequency"]');
    radios.forEach(radio => {
    const label = document.querySelector(`label[for='${radio.id}']`);
    if (label) {
        if (radio.checked) {
        label.classList.add('active');
        } else {
        label.classList.remove('active');
        }
    }
    });
}