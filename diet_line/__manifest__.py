# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Diet Line App',
    'version': '11.0.1.0.7',
    "author": "Vauxoo",
    "license": "LGPL-3",
    'category': 'Hidden',
    'summary': 'Diet Line App for customizations',
    'depends': [
        # Main Apps
        'crm',
        'account_invoicing',
        'account_accountant',
        'website',
        'mass_mailing',
        'marketing_automation',
        'stock',
        # Secondary Modules
        'account_cash_basis_base_account',
        'l10n_mx',
        'l10n_mx_edi',
        'l10n_mx_edi_payment',
        'l10n_mx_edi_payment',
        # Modules from Facebook connector branch
        'crm_facebook_leads',
    ],
    'data': [
        'views/crm_lead_view.xml'
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': True,
}
