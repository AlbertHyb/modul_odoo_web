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

// TEMPORADA: el búho posado despega, cruza la pantalla aleteando y aterriza en la
// otra esquina. El CSS dibuja el vuelo; aquí solo se alternan el lado y el estado.
const OWL_FLIGHT_MS = 7000;
const OWL_REST_MS = 9000;
const OWL_FIRST_FLIGHT_MS = 2500;

function startOwl() {
    const owl = document.querySelector("[data-financa-owl]");
    if (!owl || window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
        return;
    }
    owl.style.setProperty("--financa-owl-flight", `${OWL_FLIGHT_MS}ms`);

    function fly() {
        // en una pestaña oculta no vuela: espera a que vuelva a verse
        if (document.hidden) {
            setTimeout(fly, OWL_REST_MS);
            return;
        }
        owl.dataset.side = owl.dataset.side === "left" ? "right" : "left";
        owl.classList.add("is-flying");
        setTimeout(() => {
            owl.classList.remove("is-flying");
            setTimeout(fly, OWL_REST_MS);
        }, OWL_FLIGHT_MS);
    }

    setTimeout(fly, OWL_FIRST_FLIGHT_MS);
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", startOwl, { once: true });
} else {
    startOwl();
}
