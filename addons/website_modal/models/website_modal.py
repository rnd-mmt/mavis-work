# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
try:
    from ..tools.sanitize import html_sanitize
except (ImportError, IOError) as err:
    pass


class WebsiteModal(models.Model):

    _name = 'website.modal'
    _description = 'Popups'

    name = fields.Char(
        required=True,
    )

    size = fields.Selection(
        selection=[
            ('modal-xs', 'Small'),
            ('modal-lg', 'Big'),
        ],
        default='modal-lg',
        required=True,
        ondelete={"modal-xs": "set null"}
    )

    appear_visit = fields.Boolean(
        string='Visit Page',
    )

    appear_visit_first = fields.Boolean(
        string='Visit Page (only once)',
        default=True,
    )

    appear_visit_url = fields.Char(
        string='URL',
    )

    appear_exit = fields.Boolean(
        string='Page Exit Intent',
    )

    appear_exit_first = fields.Boolean(
        string='Page Exit Intent (only once)',
        default=True,
    )

    appear_exit_url = fields.Char(
        string='URL',
    )

    appear_time = fields.Boolean(
        string='Time on Page',
    )

    appear_time_first = fields.Boolean(
        string='Time on Page (only once)',
        default=True,
    )

    appear_time_url = fields.Char(
        string='URL',
    )

    appear_time_val = fields.Integer(
        string='Time (seconds)',
        default=10,
    )

    appear_scroll = fields.Boolean(
        string='Scroll to Bottom of Page',
    )

    appear_scroll_first = fields.Boolean(
        string='Scroll to Bottom of Page (only once)',
        default=True,
    )

    appear_scroll_url = fields.Char(
        string='URL',
    )

    plain_html = fields.Boolean(
        string='Use plain HTML field (usually used for pasting HTML)',
    )

    html_text = fields.Text(
        string="HTML",
        compute='_compute_html_text',
        inverse='_inverse_html_text',
    )

    html = fields.Html(
        string="HTML",
        sanitize=False,
    )

    def _compute_html_text(self):
        for rec in self:
            rec.html_text = rec.html

    def _inverse_html_text(self):
        for rec in self:
            if not rec.plain_html:
                continue
            rec.html = html_sanitize(rec.html_text)
