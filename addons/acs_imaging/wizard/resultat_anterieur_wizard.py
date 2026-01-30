# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime

class ImgResultAnterieurLine(models.TransientModel):
    _name = "img.result.anterieur.wizard.line"
    _description = "Ligne de résultat antérieur imagerie"

    wizard_result_id = fields.Many2one("img.result.anterieur.wizard")
    selected = fields.Boolean("Choix")
    date = fields.Date(string='Date')
    clinic_info = fields.Char('Renseignement clinique')
    interpretation = fields.Html('Interpretation')
    

class ImgResultAnterieur(models.TransientModel):
    _name = 'img.result.anterieur.wizard'
    _description = 'Résultat antérieur imagerie' 

    patient_id = fields.Many2one('hms.patient', string='Patient')
    line_ids = fields.One2many('img.result.anterieur.wizard.line', 'wizard_result_id', string='Ligne de resultat')

    @api.model
    def default_get(self, fields):
        res = super(ImgResultAnterieur, self).default_get(fields)
        active_model = self._context.get('active_model')
        if active_model == 'patient.imaging.test':
            active_record = self.env['patient.imaging.test'].browse(self._context.get('active_id'))
            if active_record.state == 'done':
                raise ValidationError(_("L'état de l'enregistrement ne doit pas être fait"))
            lines = []
            histo_result = self.env['patient.imaging.test'].search([('test_id', '=', active_record.test_id.id),
                                             ('state', '=', 'done'),
                                             ('patient_id', '=', active_record.patient_id.id),
                                             ('date_analysis','<=',active_record.date_analysis)])
            
            for histo in histo_result:
                lines.append((0, 0, {
                    'date': histo.date_analysis,
                    'clinic_info': histo.clinic_info,
                    'interpretation': histo.interpretation,
                }))
            res.update({'line_ids': lines, 'patient_id': active_record.patient_id.id})
        return res

    def insert_record(self):
        active_model = self._context.get('active_model')
        active_record = self.env['patient.imaging.test'].browse(self._context.get('active_id'))
        for line in self.line_ids:
            if line.selected is True:
                active_record.result_date_antérieur = line.date
                active_record.old_rc = line.clinic_info
                active_record.old_interpretation = line.interpretation
            else:
                pass
           
