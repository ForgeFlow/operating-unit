# -*- coding: utf-8 -*-
# © 2016-17 Eficent Business and IT Consulting Services S.L.
# © 2016 Serpent Consulting Services Pvt. Ltd.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo import api, fields, models, _


class AccountPayment(models.Model):
    _inherit = "account.payment"

    @api.depends('journal_id')
    def _compute_operating_unit_id(self):
        for payment in self:
            if payment.journal_id:
                payment.operating_unit_id = \
                    payment.journal_id.operating_unit_id

    operating_unit_id = fields.Many2one(
        'operating.unit', string='Operating Unit',
        compute='_compute_operating_unit_id', readonly=True, store=True)

    def _get_counterpart_move_line_vals(self, invoice=False):
        if not invoice:
            return super(AccountPayment, self)._get_counterpart_move_line_vals(
                invoice)
        if len(invoice) == 1:
            res = super(AccountPayment,
                        self)._get_counterpart_move_line_vals(invoice=invoice)
            res['operating_unit_id'] = invoice.operating_unit_id.id or False
            return res
        else:
            for inv in invoice:
                res = super(AccountPayment,
                            self)._get_counterpart_move_line_vals(
                    invoice=inv)
                res['operating_unit_id'] = inv.operating_unit_id.id or False
                return res

    def _get_liquidity_move_line_vals(self, amount):
        res = super(AccountPayment, self)._get_liquidity_move_line_vals(amount)
        res['operating_unit_id'] = self.journal_id.operating_unit_id.id \
            or False
        return res

    def _get_dst_liquidity_aml_dict_vals(self):
        dst_liquidity_aml_dict = {
            'name': _('Transfer from %s') % self.journal_id.name,
            'account_id':
                self.destination_journal_id.default_credit_account_id.id,
            'currency_id': self.destination_journal_id.currency_id.id,
            'payment_id': self.id,
            'journal_id': self.destination_journal_id.id,
        }

        if self.currency_id != self.company_id.currency_id:
            dst_liquidity_aml_dict.update({
                'currency_id': self.currency_id.id,
                'amount_currency': self.amount,
            })

        dst_liquidity_aml_dict.update({
            'operating_unit_id':
                self.destination_journal_id.operating_unit_id.id or False})
        return dst_liquidity_aml_dict

    def _get_shared_move_line_vals(self, debit, credit, amount_currency, move_id, invoice_id=False):
        """ Returns values common to both move lines (except for debit, credit and amount_currency which are reversed)
        """
        res = super(AccountPayment, self)._get_shared_move_line_vals(
            debit, credit, amount_currency, move_id, invoice_id
        )
        res['operating_unit_id'] = self.journal_id.operating_unit_id.id or False
        return res
