# -*- coding: utf-8 -*-
from odoo.tests import common


class TestBase(common.TransactionCase):
    at_install = False
    post_install = True

    def setUp(self):
        super(TestBase, self).setUp()
        self.config_param = self.env['ir.config_parameter']
        self.main_company = self.env.user.company_id
        self.second_company = self.env['res.company'].create(
            {'name': 'Second company'})

    def test_cache(self):
        key = 'test_key'
        value1 = 'value1'
        value2 = 'value2'

        # set value for first company
        self.config_param.set_param(key, value1)
        # call get_param to cache the value
        self.assertEqual(
            self.config_param.get_param(key), value1, 'Value is not saved!')

        # set value for second company
        self.env.user.company_id = self.second_company
        self.config_param.set_param(key, value2)
        param = self.config_param.search([('key', '=', key)])

        # check without cache first
        self.assertEqual(
            param.value, value2, 'Value for second company is not saved!')

        # check cache
        self.assertEqual(
            self.config_param.get_param(key),
            value2,
            'Cache gives value for wrong company!')

        self.env.user.company_id = self.main_company
        self.assertEqual(self.config_param.get_param(key), value1)
