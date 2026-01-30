# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import datetime

class InsertResultAnterieurLine(models.TransientModel):
    _name = "result.anterieur.wizard.line"
    _description = "Ligne de résultat antérieur"

    wizard_result_id = fields.Many2one("result.anterieur.wizard")
    date = fields.Date(string='Date')
    name = fields.Char('Parameter')
    result = fields.Char('Resultat')
    lab_uom_id = fields.Many2one('acs.lab.test.uom', string='UOM')
    remark = fields.Char('Remark')
    normal_range = fields.Char('Normal Range')
    #ACS: in doo15 warning and danger can be removed. After checkinging need
    result_type = fields.Selection([
        ('low', "Low"),
        ('normal', "Normal"),
        ('high', "High"),
        ('positive', "Positive"),
        ('negative', "Negative"),
        ('warning', "Warning"),
        ('danger', "Danger"),
        ], default='normal', string="Result Type", help="Technical field for UI purpose.")
    result_value_type = fields.Selection([
        ('quantitative','Quantitative'),
        ('qualitative','Qualitative'),
    ], string='Result Value Type', default='quantitative')

class InsertResultAnterieur(models.TransientModel):
    _name = 'result.anterieur.wizard'
    _description = 'Résultat antérieur'

    patient_id = fields.Many2one('hms.patient', string='Patient')
    line_ids = fields.One2many('result.anterieur.wizard.line', 'wizard_result_id', string='Invoice Lines')

    @api.model
    def default_get(self, fields):
        res = super(InsertResultAnterieur, self).default_get(fields)
        active_model = self._context.get('active_model')
        if active_model == 'patient.laboratory.test':
            active_record = self.env['patient.laboratory.test'].browse(self._context.get('active_id'))
            if active_record.state == 'done':
                raise ValidationError(_("L'état de l'enregistrement ne doit pas être fait"))
            lines = []
            histo_analyte = self.env['lab.test.critearea']
            list_analyte = []
            for line in active_record.critearea_ids:
                lines.append(line.name)
            for histo in lines:
                vals = histo_analyte.search([('name', '=', histo),
                                             ('patient_lab_id', '!=', active_record.id),
                                             ('patient_id', '=', active_record.patient_id.id),
                                             ('date_result','<=',active_record.date_analysis)], limit=1, order='id DESC')
                list_analyte.append((0, 0, {
                    'name': vals.name,
                    'result': vals.result,
                    'lab_uom_id': vals.lab_uom_id,
                    'remark': vals.remark,
                    'normal_range': vals.normal_range,
                    'result_type': vals.result_type,
                    'result_value_type': vals.result_value_type,
                    'date': vals.date_result,
                }))
            res.update({'line_ids': list_analyte, 'patient_id': active_record.patient_id.id})
        return res

    def insert_record(self):
        active_model = self._context.get('active_model')
        active_record = self.env['patient.laboratory.test'].browse(self._context.get('active_id'))
        vals = []
        for line in self.line_ids:
            for rec in active_record.critearea_ids:
                if line.name == rec.name:
                    vals.append((1, rec.id, {
                        'prev_result': line.result,
                        'date_anterieur': line.date,
                    }))
                else:
                    pass
        active_record.write({'critearea_ids': vals})

