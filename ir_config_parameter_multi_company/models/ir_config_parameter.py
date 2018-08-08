# -*- coding: utf-8 -*-
import logging

from odoo import models, fields, api, _, tools
from odoo.addons.base.ir.ir_config_parameter import IrConfigParameter as IrConfigParameterOriginal  # noqa

_logger = logging.getLogger(__name__)
PROP_NAME = _('Default value for "%s"')


class IrConfigParameter(models.Model):
    _inherit = 'ir.config_parameter'

    value = fields.Text(required=False, company_dependent=True)

    @api.multi
    def _get_property(self, for_default=False):
        self.ensure_one()

        domain = self.env['ir.property']._get_domain('value', self._name)
        domain += [('res_id', '=', '%s,%s' % (self._name, self.id))]
        if for_default:
            # find: ('company_id', 'in', [company_id, False])
            # update to: ('company_id', 'in', [False])
            domain = [
                ('company_id', 'in', [False])
                if x[0] == 'company_id'
                else
                x
                for x in domain
            ]

        prop = self.env['ir.property'].search(domain)
        return prop

    @api.model
    def create(self, vals):
        res = super(IrConfigParameter, self).create(vals)
        # make value company independent
        prop = res._get_property()
        prop.company_id = None
        prop.name = PROP_NAME % res.key
        return res

    @api.multi
    def write(self, vals):
        res = super(IrConfigParameter, self).write(vals)
        if 'key' in vals:
            # Change property name after renaming the parameter to avoid confusions  # noqa
            self.ensure_one()  # it's not possible to update key on multiple records  # noqa
            name = PROP_NAME % vals.get('key')
            prop = self._get_property(for_default=True)
            prop.name = name
        return res

    @api.model
    def get_param(self, key, default=False):
        company_id = self.env.context.get('company_id')
        if not company_id:
            website_id = self.env.context.get('website_id')
            if website_id:
                website = self.env['website'].browse(website_id)
                company_id = website.company_id and website.company_id.id

        if not company_id:
            company_id = self.env.user.company_id.id

        return super(
            IrConfigParameter,
            self.with_context(
                force_company=company_id)).get_param(key, default)

    @api.model
    @tools.ormcache_context('self._uid', 'key', keys=("force_company",))
    def _get_param(self, key):
        _logger.debug('_get_param(%s) context: %s', key, self.env.context)
        # call undecorated super method. See odoo/tools/cache.py::ormcache
        # and http://decorator.readthedocs.io/en/stable/
        # tests.documentation.html#getting-the-source-code
        return IrConfigParameterOriginal._get_param.__wrapped__(self, key)

    @api.multi
    def _create_default_value(self, value):
        """Set company-independent default value"""
        self.ensure_one()
        self.env['ir.property'].create({
            'fields_id': self.env.ref(
                'base.field_ir_config_parameter_value').id,
            'res_id': 'ir.config_parameter,%s' % self.id,
            'name': PROP_NAME % self.key,
            'value': value,
            'type': 'text',
        })

    def _auto_init(self):
        # Check that we have an value column
        cr = self.env.cr
        sql = """SELECT COUNT(*)
                 FROM information_schema.columns
                 WHERE table_name=%s AND column_name=%s;"""
        cr.execute(sql, ('ir_config_parameter', 'value'))
        has_value = cr.dictfetchone().get('count')
        cr.execute(sql, ('ir_config_parameter', 'value_old'))
        has_value_old = cr.dictfetchone().get('count')
        if has_value and not has_value_old:
            _logger.info(
                '''Starting conversion for ir.config_parameter:
                   saving data for further processing.''')
            # Rename image column so we don't lose images upon module install
            cr.execute(
                """ALTER TABLE ir_config_parameter
                   RENAME COLUMN value TO value_old""")
            cr.execute(
                """ALTER TABLE ir_config_parameter
                   ADD COLUMN value TEXT NOT NULL DEFAULT ''""")

            def call_init():
                self._init_from_value_old()
            self.pool.post_init(call_init)
        else:
            _logger.debug(
                '''No value field found in ir_config_parameter;
                   no data to save.''')
        return super(IrConfigParameter, self)._auto_init()

    def _init_from_value_old(self):
        cr = self.env.cr

        _logger.info(
            '''Starting rewrite of ir.config_parameter,
               saving values to ir.property.''')
        for rec in self.env['ir.config_parameter'].sudo().search([]):
            cr.execute(
                "SELECT key,value_old FROM ir_config_parameter WHERE id = %s",
                (rec.id, ))
            res = cr.dictfetchone()
            value_old = res.get('value_old')
            rec._create_default_value(value_old)
