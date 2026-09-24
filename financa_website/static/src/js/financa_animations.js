/** @odoo-module **/

// ponytail: content stays visible without JS; CSS only hides .financa-reveal when this class is present
document.documentElement.classList.add("js-financa");

const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const observed = new WeakSet();
const initializedCarousels = new WeakSet();

// ponytail: one observer for everything; JS only tags elements and sets --financa-delay, CSS owns the motion
const STAGGER_ITEMS = ".financa-problems-grid > li, .financa-services-grid > article, .financa-cases-grid > article, .financa-capabilities > li, .financa-timeline > li, .financa-integration-flow > li, .financa-odoo-modules > article, .financa-diagnosis-checks > div";
const LEAD_ITEMS = ".financa-section-heading, .financa-diagnosis-grid > div:first-child, .financa-final-cta-inner > div, .financa-final-cta-inner > .financa-button";
const CLOSING_ITEMS = ".financa-problems-closing, .financa-integration-closing, .financa-services-closing, .financa-process-closing";
const STAGGER_STEP_MS = 80;
const STAGGER_MAX_MS = 300;

function prepareReveal(section) {
    if (section.dataset.financaPrepared === "1") {
        return;
    }
    section.dataset.financaPrepared = "1";

    section.querySelectorAll(LEAD_ITEMS).forEach((element) => element.classList.add("financa-anim-lead"));

    const items = [...section.querySelectorAll(STAGGER_ITEMS)];
    items.forEach((element, index) => {
        element.classList.add("financa-anim-item");
        element.style.setProperty("--financa-delay", `${Math.min(index * STAGGER_STEP_MS, STAGGER_MAX_MS)}ms`);
    });

    section.querySelectorAll(CLOSING_ITEMS).forEach((element) => {
        element.classList.add("financa-anim-lead");
        element.style.setProperty("--financa-delay", `${Math.min(items.length * STAGGER_STEP_MS, STAGGER_MAX_MS)}ms`);
    });
}

function animateCount(element) {
    if (element.dataset.financaCounted === "1") {
        return;
    }
    element.dataset.financaCounted = "1";

    const target = Number(element.dataset.count);
    if (!Number.isFinite(target) || reducedMotion.matches) {
        return;
    }

    const prefix = element.dataset.countPrefix || "";
    const suffix = element.dataset.countSuffix || "";
    const startedAt = performance.now();
    const duration = 700;

    function frame(now) {
        const progress = Math.min((now - startedAt) / duration, 1);
        element.textContent = `${prefix}${Math.round(target * progress)}${suffix}`;
        if (progress < 1) {
            requestAnimationFrame(frame);
        }
    }

    requestAnimationFrame(frame);
}

const observer = "IntersectionObserver" in window && !reducedMotion.matches
    ? new IntersectionObserver((entries) => {
        for (const entry of entries) {
            if (!entry.isIntersecting) {
                continue;
            }
            entry.target.classList.add("is-visible");
            entry.target.querySelectorAll("[data-count]").forEach(animateCount);
            observer.unobserve(entry.target);
            // ponytail: drop anim classes once the stagger ends so hover/focus transitions aren't delayed
            const section = entry.target;
            setTimeout(() => {
                section.querySelectorAll(".financa-anim-lead, .financa-anim-item").forEach((element) => {
                    element.classList.remove("financa-anim-lead", "financa-anim-item");
                    element.style.removeProperty("--financa-delay");
                });
            }, 500 + STAGGER_MAX_MS + 50);
        }
    }, { threshold: 0.16 })
    : null;

function register(root = document) {
    const elements = root.matches?.(".financa-reveal")
        ? [root]
        : root.querySelectorAll?.(".financa-reveal") || [];

    for (const element of elements) {
        if (observed.has(element)) {
            continue;
        }
        observed.add(element);
        if (observer) {
            prepareReveal(element);
            observer.observe(element);
        } else {
            element.classList.add("is-visible");
            element.querySelectorAll("[data-count]").forEach(animateCount);
        }
    }

    const carousels = root.matches?.(".financa-hero-carousel")
        ? [root]
        : root.querySelectorAll?.(".financa-hero-carousel") || [];
    carousels.forEach(initCarousel);
}

function initCarousel(carousel) {
    if (initializedCarousels.has(carousel)) return;

    const panels = [...carousel.querySelectorAll(".financa-hero-panel")];
    const dots = [...carousel.querySelectorAll("[data-financa-carousel-dot]")];
    const status = carousel.querySelector("[data-financa-carousel-status]");
    if (panels.length !== 3 || dots.length !== panels.length) return;
    initializedCarousels.add(carousel);

    let active = 0;
    function show(index, announce = true) {
        active = (index + panels.length) % panels.length;
        panels.forEach((panel, panelIndex) => {
            const state = panelIndex === active ? "active" : panelIndex === (active + 1) % panels.length ? "next" : "previous";
            panel.dataset.financaState = state;
            panel.setAttribute("aria-hidden", String(state !== "active"));
        });
        dots.forEach((dot, dotIndex) => {
            const selected = dotIndex === active;
            dot.setAttribute("aria-current", String(selected));
            dot.tabIndex = selected ? 0 : -1;
        });
        if (announce && status) status.textContent = `${panels[active].querySelector("h2")?.textContent || "Panel"}, panel ${active + 1} de ${panels.length}`;
    }

    carousel.querySelector("[data-financa-carousel-prev]")?.addEventListener("click", () => { show(active - 1); restart(); });
    carousel.querySelector("[data-financa-carousel-next]")?.addEventListener("click", () => { show(active + 1); restart(); });
    dots.forEach((dot, index) => dot.addEventListener("click", () => { show(index); restart(); }));
    carousel.addEventListener("keydown", (event) => {
        if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
        event.preventDefault();
        show(event.key === "Home" ? 0 : event.key === "End" ? panels.length - 1 : active + (event.key === "ArrowRight" ? 1 : -1));
        restart();
    });

    // ponytail: autoplay pauses on hover/focus/hidden tab/reduced-motion; no aria-live spam on auto-advance
    const AUTOPLAY_MS = 5000;
    let timer = null;
    function stop() {
        if (timer) {
            clearInterval(timer);
            timer = null;
        }
    }
    function start() {
        if (timer || reducedMotion.matches || document.hidden) return;
        timer = setInterval(() => show(active + 1, false), AUTOPLAY_MS);
    }
    function restart() {
        stop();
        start();
    }
    carousel.addEventListener("pointerenter", stop);
    carousel.addEventListener("pointerleave", start);
    carousel.addEventListener("focusin", stop);
    carousel.addEventListener("focusout", start);
    document.addEventListener("visibilitychange", () => (document.hidden ? stop() : start()));

    show(0, false);
    carousel.classList.add("is-enhanced");
    start();
}

function init() {
    register();
    new MutationObserver((mutations) => {
        for (const mutation of mutations) {
            for (const node of mutation.addedNodes) {
                if (node.nodeType === Node.ELEMENT_NODE) {
                    register(node);
                }
            }
        }
    }).observe(document.body, { childList: true, subtree: true });

    if (window.location.hash) {
        document.querySelector(window.location.hash)?.scrollIntoView({ block: "start" });
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
} else {
    init();
}
