/** @odoo-module **/

// ponytail: content stays visible without JS; CSS only hides .financa-reveal when this class is present
document.documentElement.classList.add("js-financa");

const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const observed = new WeakSet();

// ponytail: one observer for everything; JS only tags elements and sets --financa-delay, CSS owns the motion
const STAGGER_ITEMS = ".financa-index-list > li, .financa-bento > article, .financa-rail > li, .financa-stats > li, .financa-cases > li";
const LEAD_ITEMS = ".financa-section-heading, .financa-index-intro, .financa-rail-head, .financa-closing-inner > div, .financa-closing-inner > .financa-button";
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

    // getElementById: a hash is not always a valid CSS selector (#:~:text=, #123).
    if (window.location.hash.length > 1) {
        let targetId = window.location.hash.slice(1);
        try {
            targetId = decodeURIComponent(targetId);
        } catch {
            // Keep the raw hash when it is not valid percent-encoding.
        }
        document.getElementById(targetId)?.scrollIntoView({ block: "start" });
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
} else {
    init();
}
