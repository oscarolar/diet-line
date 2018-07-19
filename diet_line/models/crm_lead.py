# -*- coding: utf-8 -*-
from odoo import fields, models


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
        try:
            lead_id.handle_partner_assignation()
            self.env.cr.commit()
        except Exception:
            self.env.cr.rollback()
        return lead_id
