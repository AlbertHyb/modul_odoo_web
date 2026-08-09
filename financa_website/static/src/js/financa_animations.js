/** @odoo-module **/

const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
const observed = new WeakSet();

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

    if (window.location.hash) {
        document.querySelector(window.location.hash)?.scrollIntoView({ block: "start" });
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
} else {
    init();
}

