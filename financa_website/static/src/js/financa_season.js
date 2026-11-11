/** @odoo-module **/

// TEMPORADA (cierre de año): actualiza el contador de la tarjeta del hero.
// El servidor ya pinta el número, así que la página se lee bien sin JavaScript;
// esto solo lo corrige con la fecha local del visitante (zona horaria y caché).
// Se retira en enero junto con su línea en __manifest__.py.

function daysUntilYearEnd(now = new Date()) {
    const today = Date.UTC(now.getFullYear(), now.getMonth(), now.getDate());
    const yearEnd = Date.UTC(now.getFullYear(), 11, 31);
    return Math.max(0, Math.round((yearEnd - today) / 86400000));
}

function updateCounters() {
    const days = String(daysUntilYearEnd());
    document.querySelectorAll("[data-financa-days]").forEach((node) => {
        node.textContent = days;
    });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", updateCounters, { once: true });
} else {
    updateCounters();
}
