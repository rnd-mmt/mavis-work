# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
 
class SplitInvoiceLine(models.TransientModel):
    _name = 'split.invoice.line'
    _description = 'Split Record Line'

    wizard_id = fields.Many2one("split.invoice.wizard")
    line_id = fields.Many2one("account.move.line")
    product_id = fields.Many2one("product.product", "Product")
    name = fields.Text("Description")
    quantity = fields.Float("Quantity")
    price = fields.Float("Unit Price")
    qty_to_split = fields.Float(string='Split Qty')
    price_to_split = fields.Float(string='Split Price')
    percentage_to_split = fields.Float(string='Split Percentage')
    display_type = fields.Selection([
        ('line_section', 'Section'),
        ('line_note', 'Note'),
    ], default=False, help="Technical field for UX purpose.")


class SplitInvoiceWizard(models.TransientModel):
    _name = 'split.invoice.wizard'
    _description = 'Split Invoice Record'

    prise_charge = fields.Selection([
        ('fonctionnaire', 'Fonctionnaire'),
        ('prise_en_charge_100', 'Prise en charge 100%'),
        ('sans_plafond', 'Sans plafond'),
        ('plafond_motant_total', 'Avec plafond sur motant total'),
        ('plafond_par_article', 'Avec plafond par article'),
    ], 'Prise en charge', default='fonctionnaire')
    split_selection = fields.Selection([
            ('invoice','Full Invoice'),
            ('lines','Invoice Lines'),
        ], 'Split Type')
    percentage = fields.Float("Ticket modérateur", default=100)
    line_split_selection = fields.Selection([
            ('qty','Quantity'),
            ('price','Unit Price'),
            ('percentage','Percentage'),
            ('sur_plafond_total', 'Plafond sur montant total'),
            ('plafond_article', 'Plafond par article'),
        ], 'Paramêtre')
    line_ids = fields.One2many('split.invoice.line', 'wizard_id', string='Invoice Lines')
    partner_id = fields.Many2one('res.partner', 'Société', required=True)
    total_plafond = fields.Float("Plafond")
    # ==== historique assurance ====
    ceiling_type = fields.Selection([
        ('fonctionnaire','Type fonctionnaire'),
        ('no_ceiling', 'Sans Plafond'),
        ('with_ceiling', 'Avec Plafond sur montant total'),
        ('with_ceiling_article', 'Avec Plafond par particle'),
    ], 'Type plafond/Profil', default='no_ceiling')
    percentage_by_assurance = fields.Float(string='Taux Assurance (%)', default=0.0)
    percentage_by_patient = fields.Float(string='Taux Patient (%)', default=0.0)
    ceiling = fields.Float(string="Plafond", default=0.0)
    result_taux_assurance = fields.Float(string="Resultat pourcentage assurance", default=0.0)
    result_taux_patient = fields.Float(string="Resultat pourcentage patient", default=0.0)
    initial_amount = fields.Float(string='Montant Initial', default=0.00)
    exceeding = fields.Float(string="Dépassement", default=0.0)

    @api.model
    def default_get(self, fields):
        res = super(SplitInvoiceWizard, self).default_get(fields)
        active_model = self._context.get('active_model')
        if active_model == 'account.move':
            active_record = self.env['account.move'].browse(self._context.get('active_id'))
            if active_record.state!='draft':
                raise ValidationError(_('Invoice must be in draft state.'))
            lines = []
            for line in active_record.invoice_line_ids:
                lines.append((0,0,{
                    'name': line.name,
                    'product_id': line.product_id and line.product_id.id or False,
                    'line_id': line.id,
                    'quantity': line.quantity,
                    'price': line.price_unit,
                    'qty_to_split': 1,
                    'price_to_split': line.price_unit * 0.5,
                    'percentage_to_split': 50,
                    'display_type': line.display_type,
                    'wizard_id': self.id
                }))
            res.update({'line_ids': lines, 'partner_id': active_record.partner_id.assurance.id, 'initial_amount': active_record.amount_total })
        return res

    @api.onchange('prise_charge')
    def onchange_prise_charge(self):
        if self.prise_charge == 'fonctionnaire':
            # self.split_selection = 'lines'
            # self.line_split_selection = 'qty'
            self.split_selection = 'invoice'
            self.percentage_by_assurance = 100
            self.percentage_by_patient = 0
        elif self.prise_charge == 'prise_en_charge_100':
            # self.split_selection = 'lines'
            # self.line_split_selection = 'qty'
            self.split_selection = 'invoice'
            self.percentage_by_assurance = 100
            self.percentage_by_patient = 0
        elif self.prise_charge == 'sans_plafond':
            self.split_selection = 'invoice'
            self.line_split_selection = ''
        elif self.prise_charge == 'plafond_motant_total':
            self.split_selection = 'lines'
            self.line_split_selection = 'sur_plafond_total'
        elif self.prise_charge == 'plafond_par_article':
            self.split_selection = 'lines'
            self.line_split_selection = 'plafond_article'

    def compute_ceiling(self, invoice_cible):
        if self.prise_charge == 'fonctionnaire':
            invoice_cible.ceiling_type = 'fonctionnaire'
            invoice_cible.initial_amount = self.initial_amount
        if self.prise_charge == 'prise_en_charge_100':
            invoice_cible.ceiling_type = 'no_ceiling'
            invoice_cible.initial_amount = self.initial_amount
            invoice_cible.percentage_by_assurance = 100
            invoice_cible.percentage_by_patient = 0
            invoice_cible.result_taux_assurance = invoice_cible.amount_insurance
            invoice_cible.result_taux_patient = invoice_cible.amount_patient
        if self.prise_charge == 'sans_plafond':
            invoice_cible.ceiling_type = 'no_ceiling'
            invoice_cible.initial_amount = self.initial_amount
            invoice_cible.percentage_by_assurance = self.percentage
            invoice_cible.percentage_by_patient = 100 - self.percentage
            invoice_cible.result_taux_assurance = invoice_cible.amount_insurance
            invoice_cible.result_taux_patient = invoice_cible.amount_patient
        if self.prise_charge == 'plafond_motant_total':
            invoice_cible.ceiling_type = 'with_ceiling'
            invoice_cible.ceiling = self.total_plafond
            invoice_cible.result_taux_assurance = self.total_plafond
            invoice_cible.percentage_by_assurance = self.percentage
            invoice_cible.percentage_by_patient = 100 - self.percentage
            invoice_cible.initial_amount = self.initial_amount
            invoice_cible.result_taux_assurance = (self.initial_amount * self.percentage) / 100
            invoice_cible.result_taux_patient = (self.initial_amount * invoice_cible.percentage_by_patient) / 100
            invoice_cible.exceeding = invoice_cible.amount_patient - invoice_cible.result_taux_patient
        if self.prise_charge == 'plafond_par_article':
            invoice_cible.ceiling_type = 'with_ceiling_article'
            invoice_cible.initial_amount = self.initial_amount
            invoice_cible.ceiling = self.total_plafond
            invoice_cible.percentage_by_assurance = self.percentage
            invoice_cible.percentage_by_patient = 100 - self.percentage
            invoice_cible.result_taux_assurance = (self.initial_amount * self.percentage) / 100
            invoice_cible.result_taux_patient = (self.initial_amount * invoice_cible.percentage_by_patient) / 100
            invoice_cible.exceeding = invoice_cible.amount_patient - invoice_cible.result_taux_patient

    def split_lines(self, active_record, split_field, update_field):
        rest_total_lines = 0
        total_lines = 0
        lines_to_split = active_record.invoice_line_ids.filtered(lambda r: r[split_field])
        new_inv_id = False
        if len(lines_to_split) >= 1:
            new_inv_id = active_record.with_context(from_split_invoice=True).copy()
            new_inv_id.partner_id = self.partner_id.id
            for line in new_inv_id.invoice_line_ids:
                #Insertion valeur initial
                line.with_context(check_move_validity=False).price_subtotal_before_split = line.price_subtotal
                line.with_context(check_move_validity=False).price_unit_before_split = line.price_unit
                if not line[split_field]:
                    line.with_context(check_move_validity=False).unlink()
                else:
                    line.with_context(check_move_validity=False).write({
                        update_field: line[split_field],
                        split_field: 0
                    })

            for line in active_record.invoice_line_ids:
                # Insertion valeur initial
                line.with_context(check_move_validity=False).price_subtotal_before_split = line.price_subtotal
                line.with_context(check_move_validity=False).price_unit_before_split = line.price_unit
                if line[split_field]:
                    if line[update_field] == line[split_field]:
                        line.with_context(check_move_validity=False).unlink()
                    else:
                        line.with_context(check_move_validity=False).write({
                            update_field: line[update_field] - line[split_field],
                            split_field: 0
                        })

        else:
            raise ValidationError(_('Please Enter Proper Amount/Quantity/Percentage To Split.'))
        return new_inv_id    

    def split_record(self):
        active_model = self._context.get('active_model')
        new_inv_id = False
        if active_model == 'account.move':
            active_record = self.env['account.move'].browse(self._context.get('active_id'))
            # Create Splited Record
            if self.split_selection == 'ceiling':
                pass

            if self.split_selection == 'invoice':
                total = 0
                restTotal = 0
                tolerance = 0.0001

                if not self.percentage:
                    raise ValidationError(_('Please Enter Percentage To Split.'))
                new_inv_id = active_record.with_context(from_split_invoice=True).copy()
                new_inv_id.partner_id = self.partner_id.id
                for line in new_inv_id.invoice_line_ids:
                    if line.price_subtotal_before_split < tolerance:
                        line.with_context(check_move_validity=False).price_subtotal_before_split = line.price_subtotal
                        line.with_context(check_move_validity=False).price_unit_before_split = line.price_unit
                    new_price = line.price_unit * (self.percentage / 100)
                    line.with_context(check_move_validity=False).price_unit = new_price

                for active_line in active_record.invoice_line_ids:
                    if active_line.price_subtotal_before_split < tolerance:
                        active_line.with_context(
                            check_move_validity=False).price_subtotal_before_split = active_line.price_subtotal
                        active_line.with_context(
                            check_move_validity=False).price_unit_before_split = active_line.price_unit
                    new_price = active_line.price_unit - (active_line.price_unit * (self.percentage / 100))
                    active_line.with_context(check_move_validity=False).price_unit = new_price
                    restTotal += active_line.price_subtotal_before_split - active_line.price_subtotal
                    total += active_line.price_subtotal

            if self.line_split_selection == 'sur_plafond_total':
                taux_assurance = 0.0
                total_initial = active_record.amount_total
                taux_assurance = (total_initial * self.percentage) / 100
                restTotal = 0
                tolerance = 0.0001
                new_inv_id = active_record.with_context(from_split_invoice=True).copy()
                new_inv_id.partner_id = self.partner_id.id
                if taux_assurance < self.total_plafond:
                    total = 0
                    restTotal = 0
                    tolerance = 0.0001
                    if not self.percentage:
                        raise ValidationError(_('Please Enter Percentage To Split.'))
                    for line in new_inv_id.invoice_line_ids:
                        if line.price_subtotal_before_split < tolerance:
                            line.with_context(
                                check_move_validity=False).price_subtotal_before_split = line.price_subtotal
                            line.with_context(check_move_validity=False).price_unit_before_split = line.price_unit
                        new_price = line.price_unit * (self.percentage / 100)
                        line.with_context(check_move_validity=False).price_unit = new_price

                    for active_line in active_record.invoice_line_ids:
                        if active_line.price_subtotal_before_split < tolerance:
                            active_line.with_context(
                                check_move_validity=False).price_subtotal_before_split = active_line.price_subtotal
                            active_line.with_context(
                                check_move_validity=False).price_unit_before_split = active_line.price_unit
                        new_price = active_line.price_unit - (active_line.price_unit * (self.percentage / 100))
                        active_line.with_context(check_move_validity=False).price_unit = new_price
                        restTotal += active_line.price_subtotal_before_split - active_line.price_subtotal
                        total += active_line.price_subtotal
                elif taux_assurance > self.total_plafond:
                    for line in new_inv_id.invoice_line_ids:
                        if line.price_subtotal_before_split < tolerance:
                            line.with_context(
                                check_move_validity=False).price_subtotal_before_split = line.price_subtotal
                            line.with_context(check_move_validity=False).price_unit_before_split = line.price_unit
                        new_price = (line.price_subtotal * self.total_plafond) / (total_initial * line.quantity)
                        line.with_context(check_move_validity=False).price_unit = new_price

                    for active_line in active_record.invoice_line_ids:
                        if active_line.price_subtotal_before_split < tolerance:
                            active_line.with_context(
                                check_move_validity=False).price_subtotal_before_split = active_line.price_subtotal
                            active_line.with_context(
                                check_move_validity=False).price_unit_before_split = active_line.price_unit
                        new_price = active_line.price_unit - ((active_line.price_subtotal * self.total_plafond) / (
                                    total_initial * active_line.quantity))
                        active_line.with_context(check_move_validity=False).price_unit = new_price

            if self.line_split_selection == 'plafond_article':
                total_initial = active_record.amount_total
                restTotal = 0
                tolerance = 0.0001
                new_inv_id = active_record.with_context(from_split_invoice=True).copy()
                new_inv_id.partner_id = self.partner_id.id
                for line in new_inv_id.invoice_line_ids:
                    if line.price_subtotal_before_split < tolerance:
                        line.with_context(check_move_validity=False).price_subtotal_before_split = line.price_subtotal
                        line.with_context(check_move_validity=False).price_unit_before_split = line.price_unit
                        result_percentage = line.price_unit * (self.percentage / 100)
                        if result_percentage >= self.total_plafond:
                            new_price = self.total_plafond
                        else:
                            new_price = result_percentage
                        line.with_context(check_move_validity=False).price_unit = new_price

                for active_line in active_record.invoice_line_ids:
                    if active_line.price_subtotal_before_split < tolerance:
                        active_line.with_context(check_move_validity=False).price_subtotal_before_split = active_line.price_subtotal
                        active_line.with_context(check_move_validity=False).price_unit_before_split = active_line.price_unit
                        result_percentage = active_line.price_unit * (self.percentage / 100)
                        if result_percentage >= self.total_plafond:
                            new_price = active_line.price_unit - self.total_plafond
                        else:
                            new_price = active_line.price_unit - result_percentage
                        active_line.with_context(check_move_validity=False).price_unit = new_price

            if self.split_selection == 'lines':
                total = 0
                restTotal = 0
                tolerance = 0.0001
                for line in self.line_ids:
                    price_to_split = 0
                    if self.line_split_selection == 'price':
                        price_to_split = line.price_to_split
                    elif self.line_split_selection == 'percentage':
                        price_to_split = line.line_id.price_unit * (line.percentage_to_split / 100)

                    line.line_id.with_context(check_move_validity=False).write({
                        'qty_to_split': line.qty_to_split,
                        'price_to_split': price_to_split,
                    })

                if self.line_split_selection == 'qty':
                    new_inv_id = self.split_lines(active_record, 'qty_to_split', 'quantity')


                if self.line_split_selection in ['price', 'percentage']:
                    new_inv_id = self.split_lines(active_record, 'price_to_split', 'price_unit')

            new_inv_id.with_context(check_move_validity=False)._onchange_partner_id()
            # ==== insertion reference de l'ancienne facture=====
            new_inv_id.with_context(check_move_validity=False).fact_associe = active_record.id
            active_record.with_context(check_move_validity=False).fact_associe = new_inv_id.id
            new_inv_id.with_context(check_move_validity=False).type_paid = new_inv_id.partner_id.type_paid
            active_record.with_context(check_move_validity=False).type_paid = active_record.partner_id.type_paid

            # === PART ASSURANCE ====
            new_inv_id.with_context(check_move_validity=False).amount_insurance = new_inv_id.amount_total
            active_record.with_context(check_move_validity=False).amount_insurance = new_inv_id.amount_total

            # === PART PATIENT ====
            new_inv_id.with_context(check_move_validity=False).amount_patient = active_record.amount_total
            active_record.with_context(check_move_validity=False).amount_patient = active_record.amount_total

            new_inv_id.with_context(check_move_validity=False)._recompute_dynamic_lines(recompute_all_taxes=True,
                                                                                        recompute_tax_base_amount=True)
            active_record.with_context(check_move_validity=False)._recompute_dynamic_lines(recompute_all_taxes=True,
                                                                                           recompute_tax_base_amount=True)

            self.compute_ceiling(active_record)
            self.compute_ceiling(new_inv_id)

            #===METTRE A L'ETAT COMPTABILITE ===
            new_inv_id.action_post()
            active_record.action_post()

            new_inv_id.message_post_with_view('mail.message_origin_link',
                                              values={'self': new_inv_id, 'origin': active_record},
                                              subtype_id=self.env.ref('mail.mt_note').id
                                              )
            active_record.message_post_with_view('mail.message_origin_link',
                                                 values={'self': active_record, 'origin': new_inv_id, 'edit': True, },
                                                 subtype_id=self.env.ref('mail.mt_note').id
                                                 )

        return new_inv_id


# class SplitInvoiceWizard(models.TransientModel):
#     _name = 'split.invoice.wizard'
#     _description = 'Split Invoice Record'

#     split_selection = fields.Selection([
#             ('invoice','Full Invoice'),
#             ('lines','Invoice Lines'),
#         ], 'Split Type', default='invoice')
#     percentage = fields.Float("Percentage to Split", default=50)
#     line_split_selection = fields.Selection([
#             ('qty','Quantity'),
#             ('price','Unit Price'),
#             ('percentage','Percentage'),
#         ], 'Split Line by', default='qty')
#     line_ids = fields.One2many('split.invoice.line', 'wizard_id', string='Invoice Lines')
#     partner_id = fields.Many2one('res.partner', 'Customer/Supplier', required=True)

#     @api.model
#     def default_get(self, fields):
#         res = super(SplitInvoiceWizard, self).default_get(fields)
#         active_model = self._context.get('active_model')
#         if active_model == 'account.move':
#             active_record = self.env['account.move'].browse(self._context.get('active_id'))
#             if active_record.state!='draft':
#                 raise ValidationError(_('Invoice must be in draft state.'))
#             lines = []
#             for line in active_record.invoice_line_ids:
#                 lines.append((0,0,{
#                     'name': line.name,
#                     'product_id': line.product_id and line.product_id.id or False,
#                     'line_id': line.id,
#                     'quantity': line.quantity,
#                     'price': line.price_unit,
#                     'qty_to_split': 1,
#                     'price_to_split': line.price_unit * 0.5,
#                     'percentage_to_split': 50,
#                     'display_type': line.display_type,
#                     'wizard_id': self.id
#                 }))
#             res.update({'line_ids': lines, 'partner_id': active_record.partner_id.id })
#         return res        

#     def split_lines(self, active_record, split_field, update_field):
#         lines_to_split = active_record.invoice_line_ids.filtered(lambda r: r[split_field])
#         new_inv_id = False
#         if len(lines_to_split) >= 1:
#             new_inv_id = active_record.with_context(from_split_invoice=True).copy()
#             new_inv_id.partner_id = self.partner_id.id
#             for line in new_inv_id.invoice_line_ids:
#                 if not line[split_field]:
#                     line.with_context(check_move_validity=False).unlink()
#                 else:
#                     line.with_context(check_move_validity=False).write({
#                         update_field: line[split_field],
#                         split_field: 0
#                     })

#             for line in active_record.invoice_line_ids:
#                 if line[split_field]:
#                     if line[update_field] == line[split_field]:
#                         line.with_context(check_move_validity=False).unlink()
#                     else:
#                         line.with_context(check_move_validity=False).write({
#                             update_field: line[update_field] - line[split_field],
#                             split_field: 0
#                         })

#         else:
#             raise ValidationError(_('Please Enter Proper Amount/Quantity/Percentage To Split.'))
#         return new_inv_id

#     def split_record(self):
#         active_model = self._context.get('active_model')
#         new_inv_id = False
#         if active_model == 'account.move':
#             active_record = self.env['account.move'].browse(self._context.get('active_id'))
#             #Create Splited Record
#             if self.split_selection == 'invoice':
#                 #Incase of 100% just unlink active record.
#                 if self.percentage==100:
#                     active_record.write({'partner_id': self.partner_id.id})
#                     active_record.with_context(check_move_validity=False)._onchange_partner_id()
#                     return active_record

#                 if not self.percentage:
#                     raise ValidationError(_('Please Enter Percentage To Split.'))
#                 new_inv_id = active_record.with_context(from_split_invoice=True).copy()
#                 new_inv_id.partner_id = self.partner_id.id
#                 for line in new_inv_id.invoice_line_ids:
#                     new_price = line.price_unit * (self.percentage / 100)
#                     line.with_context(check_move_validity=False).price_unit = new_price

#                 for active_line in active_record.invoice_line_ids:
#                     new_price = active_line.price_unit - (active_line.price_unit * (self.percentage / 100))
#                     active_line.with_context(check_move_validity=False).price_unit = new_price

#             if self.split_selection == 'lines':
#                 for line in self.line_ids:
#                     price_to_split = 0
#                     if self.line_split_selection == 'price':
#                         price_to_split = line.price_to_split
#                     elif self.line_split_selection == 'percentage':
#                         price_to_split = line.line_id.price_unit * (line.percentage_to_split / 100)

#                     line.line_id.with_context(check_move_validity=False).write({
#                         'qty_to_split': line.qty_to_split,
#                         'price_to_split': price_to_split,
#                     })

#                 if self.line_split_selection == 'qty':
#                     new_inv_id = self.split_lines(active_record, 'qty_to_split', 'quantity')

#                 if self.line_split_selection in ['price', 'percentage']:
#                     new_inv_id = self.split_lines(active_record, 'price_to_split', 'price_unit')

#             new_inv_id.with_context(check_move_validity=False)._onchange_partner_id()

#             # ==== insertion reference de l'ancienne facture=====
#             new_inv_id.with_context(check_move_validity=False).fact_associe = active_record.id
#             active_record.with_context(check_move_validity=False).fact_associe = new_inv_id.id

#             new_inv_id.with_context(check_move_validity=False)._recompute_dynamic_lines(recompute_all_taxes=True, recompute_tax_base_amount=True)
#             active_record.with_context(check_move_validity=False)._recompute_dynamic_lines(recompute_all_taxes=True, recompute_tax_base_amount=True)
        
#             new_inv_id.message_post_with_view('mail.message_origin_link',
#                 values={'self': new_inv_id, 'origin': active_record},
#                 subtype_id=self.env.ref('mail.mt_note').id
#             )
#             active_record.message_post_with_view('mail.message_origin_link',
#                 values={'self': active_record, 'origin': new_inv_id, 'edit': True,},
#                 subtype_id=self.env.ref('mail.mt_note').id
#             )

#         return new_inv_id
