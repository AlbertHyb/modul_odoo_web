"""Model methods for the Financa website module."""

from odoo import api, models


class WebsitePage(models.Model):
    _inherit = "website.page"

    @api.model
    def _financa_archive_competing_homepage(self):
        """Archive every page at "/" except the Financa homepage.

        Odoo 19 resolves "/" with `website.page` ordered by `website_id asc`
        (website_page._get_page_info, _order = 'website_id'). A generic page
        (website_id False) or another specific page wins over the Financa
        homepage unless its URL is moved away.
        """
        Page = self.env["website.page"].sudo()
        module_homepage = Page.search(
            [
                ("url", "=", "/"),
                ("view_id.key", "=", "financa_website.financa_homepage"),
            ],
            limit=1,
        )
        if not module_homepage:
            return False

        website_id = module_homepage.website_id.id
        homepages = Page.search(
            [
                ("url", "=", "/"),
                "|",
                ("website_id", "=", False),
                ("website_id", "=", website_id),
            ]
        )
        for page in homepages - module_homepage:
            archive_url = page.url + "-odoo-homepage-archivo"
            while Page.search([("url", "=", archive_url)]):
                archive_url += "2"
            page.write({"url": archive_url, "is_published": False})
            for menu in page.menu_ids:
                menu.write({"url": "/", "page_id": module_homepage.id})
        return True
