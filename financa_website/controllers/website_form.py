"""Send the diagnostic follow-up email when the Financa contact form creates a lead."""

import logging

from odoo.addons.website_crm.controllers.website_form import WebsiteForm

_logger = logging.getLogger(__name__)

THANK_YOU_PAGE = "financa_website.financa_thank_you_page"
SURVEY = "financa_website.financa_diagnostic_survey"
TEMPLATE = "financa_website.mail_template_financa_diagnostic_follow_up"


class FinancaWebsiteForm(WebsiteForm):

    def insert_record(self, request, model_sudo, values, custom, meta=None):
        lead_id = super().insert_record(request, model_sudo, values, custom, meta=meta)
        if model_sudo.model == "crm.lead" and lead_id and self._financa_is_financa_website(request):
            env = request.env(su=True)
            try:
                # the lead is already stored: a mail problem must not lose it
                with env.cr.savepoint():
                    self._financa_send_follow_up(request, env["crm.lead"].browse(lead_id))
            except Exception:
                _logger.exception("Financa follow-up email failed for lead %s", lead_id)
        return lead_id

    def _financa_is_financa_website(self, request):
        page = request.env(su=True).ref(THANK_YOU_PAGE, raise_if_not_found=False)
        return bool(page) and page.website_id == request.website

    def _financa_send_follow_up(self, request, lead):
        env = lead.env
        survey = env.ref(SURVEY, raise_if_not_found=False)
        template = env.ref(TEMPLATE, raise_if_not_found=False)
        if not lead.email_from or not survey or not survey.active or not template:
            _logger.warning("Financa follow-up skipped for lead %s: missing email, survey or template", lead.id)
            return

        answer = survey._create_answer(
            partner=lead.partner_id,
            email=lead.email_from,
            nickname=lead.contact_name or lead.partner_name,
            check_attempts=False,
        )
        base_url = request.website.get_base_url()
        if not base_url.startswith("http"):
            # desarrollo: el sitio conserva el marcador de dominio sin renderizar
            base_url = request.httprequest.url_root.rstrip("/")
        survey_url = base_url + answer.get_start_url()
        # send_mail también deja el correo en el chatter del lead
        template.with_context(financa_survey_url=survey_url).send_mail(lead.id)
