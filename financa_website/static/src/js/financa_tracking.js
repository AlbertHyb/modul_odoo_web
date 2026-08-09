/** @odoo-module **/

const sectionEvents = new Set();
const experimentEvents = new Set();
const startedForms = new WeakSet();
let sectionObserver;
let optionalConsentGranted = null;

function isEditor() {
    const query = new URLSearchParams(window.location.search);
    return query.has("enable_editor")
        || document.body.classList.contains("editor_enable")
        || document.documentElement.classList.contains("o_website_editable")
        || Boolean(document.querySelector(".o_we_website_top_actions, .o_website_preview"));
}

function readConsent() {
    const rawCookie = document.cookie
        .split("; ")
        .find((entry) => entry.startsWith("website_cookies_bar="))
        ?.split("=")
        .slice(1)
        .join("=");

    if (!rawCookie) {
        return false;
    }

    try {
        return JSON.parse(decodeURIComponent(rawCookie)).optional === true;
    } catch {
        return false;
    }
}

function hasConsent() {
    return optionalConsentGranted === true;
}

function storageGet(key) {
    try {
        return window.sessionStorage.getItem(key);
    } catch {
        return null;
    }
}

function storageSet(key, value) {
    try {
        window.sessionStorage.setItem(key, value);
    } catch {
        // Tracking must never interrupt navigation.
    }
}

function storageRemove(key) {
    try {
        window.sessionStorage.removeItem(key);
    } catch {
        // Tracking must never interrupt navigation.
    }
}

function emit(eventName, parameters = {}) {
    if (isEditor() || !hasConsent() || typeof window.gtag !== "function") {
        return false;
    }

    window.gtag("event", eventName, {
        ...parameters,
        page_path: window.location.pathname,
    });
    return true;
}

function trackSection(section) {
    const sectionName = section.dataset.financaSection;
    if (!sectionName || sectionEvents.has(sectionName)) {
        return;
    }
    if (emit("financa_section_view", { section_name: sectionName })) {
        sectionEvents.add(sectionName);
        sectionObserver?.unobserve(section);
    }
}

function observeSections() {
    if (!("IntersectionObserver" in window)) {
        document.querySelectorAll("[data-financa-section]").forEach(trackSection);
        return;
    }

    sectionObserver ||= new IntersectionObserver((entries) => {
        for (const entry of entries) {
            if (entry.isIntersecting) {
                trackSection(entry.target);
            }
        }
    }, { threshold: 0.35 });

    document.querySelectorAll("[data-financa-section]").forEach((section) => {
        if (!sectionEvents.has(section.dataset.financaSection)) {
            sectionObserver.observe(section);
        }
    });
}

function trackCurrentlyVisibleSections() {
    for (const section of document.querySelectorAll("[data-financa-section]")) {
        const rect = section.getBoundingClientRect();
        const visibleHeight = Math.min(rect.bottom, window.innerHeight) - Math.max(rect.top, 0);
        if (visibleHeight > Math.min(rect.height * 0.35, window.innerHeight * 0.35)) {
            trackSection(section);
        }
    }
}

function ctaDestination(link) {
    const href = link.getAttribute("href") || "";
    try {
        const url = new URL(href, window.location.origin);
        return url.origin === window.location.origin ? `${url.pathname}${url.hash}` : url.href;
    } catch {
        return href;
    }
}

function rememberFormSubmission(form) {
    if (!hasConsent()) {
        return;
    }
    const token = `${Date.now()}`;
    storageSet("financa_pending_submission", token);
    storageSet("financa_pending_form", form.dataset.financaFormName || "contacto_diagnostico");
}

function trackContactView() {
    if (window.location.pathname !== "/contactus") {
        return;
    }
    const sourceCta = storageGet("financa_source_cta");
    if (sourceCta && emit("financa_contact_view", { source_cta: sourceCta })) {
        storageRemove("financa_source_cta");
    }
}

function trackConfirmedLead() {
    if (window.location.pathname !== "/gracias-diagnostico") {
        return;
    }

    const params = new URLSearchParams(window.location.search);
    const token = storageGet("financa_pending_submission");
    const formName = storageGet("financa_pending_form") || "contacto_diagnostico";
    const submittedRecently = token && Date.now() - Number(token) < 15 * 60 * 1000;
    let cameFromContact = false;

    try {
        const referrer = new URL(document.referrer);
        cameFromContact = referrer.origin === window.location.origin && referrer.pathname === "/contactus";
    } catch {
        cameFromContact = false;
    }

    if (!submittedRecently || !cameFromContact || params.get("financa_submission") !== "1") {
        return;
    }

    const dedupeKey = `financa_lead_sent_${token}`;
    if (storageGet(dedupeKey)) {
        return;
    }

    if (emit("generate_lead", { lead_source: "website_diagnostico", form_name: formName })) {
        storageSet(dedupeKey, "1");
        storageRemove("financa_pending_submission");
        storageRemove("financa_pending_form");
    }
}

function onClick(event) {
    const loginLink = event.target.closest("a[href='/web/login']");
    if (loginLink) {
        emit("financa_login_click", { cta_location: "header" });
        return;
    }

    const submitButton = event.target.closest(".s_website_form_send");
    if (submitButton) {
        const form = submitButton.closest("form[data-financa-form-name]");
        if (form) {
            rememberFormSubmission(form);
        }
    }

    const cta = event.target.closest("[data-financa-cta]");
    if (!cta) {
        return;
    }

    const destination = ctaDestination(cta);
    const ctaName = cta.dataset.financaCtaName || "cta";
    if (hasConsent() && destination.startsWith("/contactus")) {
        storageSet("financa_source_cta", ctaName);
    }
    emit("financa_cta_click", {
        cta_name: ctaName,
        cta_location: cta.dataset.financaCtaLocation || "unknown",
        destination,
    });
}

function onFormInteraction(event) {
    const form = event.target.closest?.("form[data-financa-form-name]");
    if (!form || startedForms.has(form)) {
        return;
    }
    if (emit("financa_form_start", { form_name: form.dataset.financaFormName })) {
        startedForms.add(form);
    }
}

function onSubmit(event) {
    const form = event.target.closest?.("form[data-financa-form-name]");
    if (form) {
        rememberFormSubmission(form);
    }
}

function trackExperimentExposure(experimentId, variantId) {
    const key = `${experimentId}:${variantId}`;
    if (!experimentId || !variantId || experimentEvents.has(key)) {
        return false;
    }
    if (emit("financa_experiment_exposure", {
        experiment_id: experimentId,
        variant_id: variantId,
    })) {
        experimentEvents.add(key);
        return true;
    }
    return false;
}

function onConsentGranted() {
    optionalConsentGranted = true;
    trackContactView();
    trackConfirmedLead();
    trackCurrentlyVisibleSections();
}

function onConsentDenied() {
    optionalConsentGranted = false;
    storageRemove("financa_source_cta");
    storageRemove("financa_pending_submission");
    storageRemove("financa_pending_form");
}

function init() {
    if (isEditor()) {
        return;
    }

    optionalConsentGranted = readConsent();

    document.addEventListener("click", onClick);
    document.addEventListener("focusin", onFormInteraction);
    document.addEventListener("input", onFormInteraction);
    document.addEventListener("change", onFormInteraction);
    document.addEventListener("submit", onSubmit);
    document.addEventListener("optionalCookiesAccepted", onConsentGranted);
    document.addEventListener("optionalCookiesDenied", onConsentDenied);

    observeSections();
    trackContactView();
    trackConfirmedLead();

    window.financaAnalytics = Object.freeze({ trackExperimentExposure });
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init, { once: true });
} else {
    init();
}

