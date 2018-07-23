# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    facebook_lead_id = fields.Char(readonly=True, copy=False)

    _sql_constraints = [
        ('facebook_lead_unique', 'unique(facebook_lead_id)',
         'A partner already exists with that Facebook Lead ID!')
    ]


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    ketosis_specialist = fields.Char()
    specialist_type = fields.Char()
    weight_to_lower = fields.Char()
    interested = fields.Char()
    visited_specialist = fields.Char()
    zip = fields.Char()
    gender = fields.Char()

    def lead_creation(self, lead, form):
        lead_id = super(CrmLead, self).lead_creation(lead, form)
        if not lead_id:
            return lead_id

        partner_obj = self.env['res.partner']
        partner_id = partner_obj.search(
            [('facebook_lead_id', '=', lead.get('id'))], limit=1)

        if not partner_id:
            partner_ids = lead_id.handle_partner_assignation()
            partner_id = partner_ids.get(lead_id.id)
            partner_id = partner_obj.browse(partner_id)
            partner_id.facebook_lead_id = lead_id.facebook_lead_id

        lead_id.partner_id = partner_id

        try:
            self.env.cr.commit()
        except Exception:
            self.env.cr.rollback()
        return lead_id

    def get_opportunity_name(self, vals, lead, form):
        if lead.get('full_name'):
            name = lead['full_name']
        else:
            name = super(CrmLead, self).get_opportunity_name(vals, lead, form)
        return name
