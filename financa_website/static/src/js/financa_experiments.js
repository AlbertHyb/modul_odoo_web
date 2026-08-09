/** @odoo-module **/

// Activation requires an approved experiment brief and a later module version.
const EXPERIMENTS_ENABLED = false;

if (EXPERIMENTS_ENABLED) {
    document.querySelectorAll("[data-financa-experiment][data-financa-variant]");
}

