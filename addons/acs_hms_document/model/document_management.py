# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import AccessError, ValidationError, MissingError, UserError
from odoo.osv.expression import AND, OR, FALSE_DOMAIN
from collections import defaultdict


class DocumentDirectory(models.Model):
    _name = "document.directory"
    _description = "Document Directory"

    def _get_attachment_count(self):
        res = {}
        AttachmentObj = self.env['ir.attachment']
        for rec in self:
            attchement_count = 0
            domain = [('directory_id','=',rec.id)]
            if rec.res_model and rec.res_model.name:
                model_domain = [('res_model', '=', rec.res_model.model)]
                domain = OR([domain,model_domain])
            rec.attchement_count = AttachmentObj.search_count(domain)

    name = fields.Char(required=True)
    parent_id = fields.Many2one('document.directory',string='Parent Directory', index=True, ondelete='cascade')
    children_ids = fields.One2many('document.directory', 'parent_id', string='Children', copy=True)
    user_ids = fields.Many2many('res.users', 'document_user_rel', 'user_id', 'doc_id', string="Users")
    description = fields.Text(string='Description')
    tag_ids = fields.Many2many('document.tag', 'directory_tag_rel', 'directory_id', 'tag_id', 
        string='Tags', help="Classify and analyze your Document")
    department_id = fields.Many2one('hr.department', string='Department', ondelete='restrict')
    attchement_count = fields.Integer(compute='_get_attachment_count', string="Number of documents attached")
    res_model = fields.Many2one('ir.model', 'Model', ondelete='cascade')

    @api.constrains('res_model')
    def _check_model(self):
        if self.res_model:
            directories = self.search([('id', '!=', self.id),('res_model', '=',self.res_model.id)])
            if directories:
                raise ValidationError(_('You can have only one directory for a model.'))
     
    def action_view_attachments(self):
        self = self.sudo()
        domain = [('directory_id','=',self.id)]
        if self.res_model and self.res_model.name:
            model_domain = [('res_model', '=', self.res_model.model)]
            domain = OR([domain,model_domain])
        attachments = self.env['ir.attachment'].search(domain)
        action = self.env["ir.actions.actions"]._for_xml_id("base.action_attachment")
        action['domain'] = [('id', 'in', attachments.ids)]
        action['context'] = {
                'default_res_model': self.res_model.model,
                'default_directory_id': self.id,
                'default_is_document': True}
        return action


    def name_get(self):
        def get_names(directory):
            """ Return the list [cat.name, cat.parent_id.name, ...] """
            res = []
            while directory:
                res.append(directory.name)
                directory = directory.parent_id
            return res
        return [(directory.id, " / ".join(reversed(get_names(directory)))) for directory in self]

    @api.constrains('parent_id')
    def _check_directory_recursion(self):
        if not self._check_recursion():
            raise ValidationError(_('Error ! You cannot create recursive Directory.'))
        return True


class Attachment(models.Model):
    _inherit = "ir.attachment"

    is_document = fields.Boolean("Is Document")
    directory_id = fields.Many2one('document.directory', string='Directory', ondelete='restrict')
    description = fields.Text(string='Description')
    tag_ids = fields.Many2many('document.tag', 'hms_document_tag_rel', 'document_id', 'tag_id', 
        string='Tags', help="Classify and analyze your Document")

    #ACS: Allow to read Documents. Only by passs to read is_document is added as if condition.
    @api.model
    def check(self, mode, values=None):
        """ Restricts the access to an ir.attachment, according to referred mode """
        if self.env.is_superuser():
            return True
        # Always require an internal user (aka, employee) to access to a attachment
        if not (self.env.is_admin() or self.env.user.has_group('base.group_user')):
            raise AccessError(_("Sorry, you are not allowed to access this document."))
        # collect the records to check (by model)
        model_ids = defaultdict(set)            # {model_name: set(ids)}
        if self:
            # DLE P173: `test_01_portal_attachment`
            self.env['ir.attachment'].flush(['res_model', 'res_id', 'create_uid', 'public', 'res_field', 'is_document'])
            self._cr.execute('SELECT res_model, res_id, create_uid, public, res_field, is_document FROM ir_attachment WHERE id IN %s', [tuple(self.ids)])
            for res_model, res_id, create_uid, public, res_field, is_document in self._cr.fetchall():
                if not self.env.is_system() and res_field:
                    raise AccessError(_("Sorry, you are not allowed to access this document."))
                if public and mode == 'read':
                    continue
                #ACS: THIS NEW CODE WAS ADDED
                if is_document:
                    continue
                if not (res_model and res_id):
                    continue
                model_ids[res_model].add(res_id)
        if values and values.get('res_model') and values.get('res_id'):
            model_ids[values['res_model']].add(values['res_id'])

        # check access rights on the records
        for res_model, res_ids in model_ids.items():
            # ignore attachments that are not attached to a resource anymore
            # when checking access rights (resource was deleted but attachment
            # was not)
            if res_model not in self.env:
                continue
            if res_model == 'res.users' and len(res_ids) == 1 and self.env.uid == list(res_ids)[0]:
                # by default a user cannot write on itself, despite the list of writeable fields
                # e.g. in the case of a user inserting an image into his image signature
                # we need to bypass this check which would needlessly throw us away
                continue
            records = self.env[res_model].browse(res_ids).exists()
            # For related models, check if we can write to the model, as unlinking
            # and creating attachments can be seen as an update to the model
            access_mode = 'write' if mode in ('create', 'unlink') else mode
            records.check_access_rights(access_mode)
            records.check_access_rule(access_mode)



class Tag(models.Model):
    _name = "document.tag"
    _description = "Document Tags"

    name = fields.Char('Name', required=True, translate=True)
    color = fields.Integer('Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Tag name already exists !"),
    ]

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: