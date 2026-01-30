# -*- coding: utf-8 -*

from odoo import models, fields, api

class CalendarEvent(models.Model):
    _inherit = 'calendar.event'

    categori_exam = fields.Selection([('scanner', 'SCANNER'),
                                      ('radio', 'RADIOGRAPHIE'),
                                      ('echo', 'ECHOGRAPHIE'),
                                      ('endo', 'ENDOSCOPIE'),
                                      ('consultation', 'CONSULTATION'),
                                     ('labs', 'ANALYSE')],
                                     string='Type Examen'
                                    )
    centre = fields.Selection([('imm', 'IMM'),
                               ('ambatobe', 'AROVY AMBATOBE'),
                              ('atrium', 'AROVY ATRIUM')],
                              string='Centre'
                             )
   # helpdesk_support_id = fields.Many2one('helpdesk.support', string='Helpdesk Support', readonly=True)
    clinic = fields.Text(string='Renseignement clinique')
    patient_id = fields.Many2one(
        'hms.patient',
        string="Patient",
        copy=False,
    )