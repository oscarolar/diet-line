# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    facebook_lead_id = fields.Char(readonly=True, copy=False)

    _sql_constraints = [
        ('facebook_lead_unique', 'unique(facebook_lead_id)',
         'A partner already exists with that Facebook Lead ID!')
    ]


class CrmTeam(models.Model):
    _inherit = 'crm.team'

    assign_method = fields.Selection([
        ('manual', 'Manually'),
        ('randomly', 'Randomly'),
        ('balanced', 'Balanced'),
        ('rounded', 'Rounded')], string='Assignation Method',
        default='manual', required=False,
        help='Automatic assignation method for new leads:\n'
             '\tManually: manual\n'
             '\tRandomly: randomly but everyone gets the same amount\n'
             '\tBalanced: to the person with the least amount of open leads\n'
             '\tRounded: to the person with the longest unassignment')

    @api.constrains('assign_method', 'member_ids')
    def _check_member_assignation(self):
        if not self.member_ids and self.assign_method != 'manual':
            raise ValidationError(_("You must have team members assigned to"
                                    " change the assignation method."))

    @api.onchange('member_ids')
    def _onchange_member_ids(self):
        if not self.member_ids:
            self.assign_method = 'manual'

    @api.multi
    def get_new_user(self):
        self.ensure_one()
        new_user = self.env['res.users']
        lead_obj = self.env['crm.lead']
        member_ids = sorted(self.member_ids.ids)
        if not member_ids:
            return new_user
        if self.assign_method == 'randomly':
            # randomly means new leads get uniformly distributed
            previous_assigned_user = lead_obj.search([
                ('team_id', '=', self.id)],
                order='create_date desc', limit=1).user_id
            # handle the case where the previous_assigned_user has left the
            # team (or there is none).
            if previous_assigned_user and \
                    previous_assigned_user.id in member_ids:
                previous_index = member_ids.index(
                    previous_assigned_user.id)
                new_user = new_user.browse(
                    member_ids[(previous_index + 1) % len(member_ids)])
            else:
                new_user = new_user.browse(member_ids[0])
        elif self.assign_method == 'balanced':
            read_group_res = lead_obj.read_group(
                ['|', ('active', '=', True), ('active', '=', False),
                    ('user_id', 'in', member_ids)], ['user_id'], ['user_id'])
            # add all the members in case a member has no leads
            # (and thus doesn't appear in the previous read_group)
            count_dict = dict((m_id, 0) for m_id in member_ids)
            count_dict.update(
                (data['user_id'][0], data['user_id_count'])
                for data in read_group_res)
            new_user = new_user.browse(min(count_dict, key=count_dict.get))
        elif self.assign_method == 'rounded':
            # This condition assigns leads to the oldest unassigned user
            count_dict = {}
            for uid in member_ids:
                count_dict[uid] = lead_obj.search(
                    ['|', ('active', '=', True), ('active', '=', False),
                     ('team_id', '=', self.id),
                     ('user_id', '=', uid), ],
                    order='id desc',
                    limit=1).id or 0
            new_user = new_user.browse(min(count_dict, key=count_dict.get))
        return new_user


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

        # Partner assignment/creation
        partner_obj = self.env['res.partner']
        partner_id = partner_obj.search(
            [('facebook_lead_id', '=', lead.get('id'))], limit=1)

        if not partner_id:
            partner_ids = lead_id.handle_partner_assignation()
            partner_id = partner_ids.get(lead_id.id)
            partner_id = partner_obj.browse(partner_id)
            partner_id.facebook_lead_id = lead_id.facebook_lead_id

        lead_id.partner_id = partner_id

        # Default priority for leads coming from Facebook is high
        lead_id.priority = '2'

        # Team/user assignment
        if form.team_id:
            lead_id.team_id = form.team_id.id
            lead_id.user_id = lead_id.team_id.get_new_user().id
        else:
            lead_id.team_id = False
            lead_id.user_id = False

        return lead_id

    def get_opportunity_name(self, vals, lead, form):
        if lead.get('full_name'):
            name = lead['full_name']
        else:
            name = super(CrmLead, self).get_opportunity_name(vals, lead, form)
        return name
