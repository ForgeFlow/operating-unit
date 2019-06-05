# -*- coding: utf-8 -*-
# © 2016-17 Eficent Business and IT Consulting Services S.L.
# © 2016 Serpent Consulting Services Pvt. Ltd.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl.html).
from odoo.tools.translate import _
from odoo import api, fields, models
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"

    operating_unit_id = fields.Many2one('operating.unit', 'Operating Unit')

    @api.model
    def create(self, vals):
        if vals.get('move_id', False):
            move = self.env['account.move'].browse(vals['move_id'])
            if move.operating_unit_id:
                vals['operating_unit_id'] = move.operating_unit_id.id
        _super = super(AccountMoveLine, self)
        return _super.create(vals)

    @api.model
    def _query_get(self, domain=None):
        if domain is None:
            domain = []
        if self._context.get('operating_unit_ids', False):
            domain.append(('operating_unit_id', 'in',
                           self._context.get('operating_unit_ids')))
        return super(AccountMoveLine, self)._query_get(domain)

    @api.multi
    @api.constrains('operating_unit_id', 'company_id')
    def _check_company_operating_unit(self):
        for rec in self:
            if (rec.company_id and rec.operating_unit_id and rec.company_id !=
                    rec.operating_unit_id.company_id):
                raise UserError(_('Configuration error!\nThe Company in the'
                                  ' Move Line and in the Operating Unit must '
                                  'be the same.'))

    @api.multi
    @api.constrains('operating_unit_id', 'move_id')
    def _check_move_operating_unit(self):
        for rec in self:
            if (rec.move_id and rec.move_id.operating_unit_id and
                rec.operating_unit_id and rec.move_id.operating_unit_id !=
                    rec.operating_unit_id):
                raise UserError(_('Configuration error!\nThe Operating Unit in'
                                  ' the Move Line and in the Move must be the'
                                  ' same.'))

    @api.multi
    def _prepare_writeoff_first_line_values(self, values):
        res = super(AccountMoveLine, self)._prepare_writeoff_first_line_values(values)
        if res['journal_id']:
            journal = self.env['account.journal'].browse(res['journal_id'])
            res['operating_unit_id'] = journal.operating_unit_id.id
        return res

    @api.multi
    def _prepare_writeoff_second_line_values(self, values):
        res = super(AccountMoveLine, self)._prepare_writeoff_second_line_values(values)
        if res['journal_id']:
            journal = self.env['account.journal'].browse(res['journal_id'])
            res['operating_unit_id'] = journal.operating_unit_id.id
        return res

    @api.multi
    def _check_pay_balance(self, lines, payment):
        # Look for the balance of each OU
        ou_balance = {}
        pay_acc = payment.journal_id.default_debit_account_id or \
                  payment.journal_id.default_credit_account_id
        for line in lines.filtered(
                lambda x: x.account_id.reconcile
                          and x.account_id != pay_acc):
            if line.operating_unit_id.id not in ou_balance:
                ou_balance[line.operating_unit_id.id] = 0.0
            ou_balance[line.operating_unit_id.id] += (line.debit - line.credit)
        ou_balance_copy = ou_balance.copy()
        for ou in ou_balance:
            for ou2 in ou_balance:
                if ou != ou2:
                    ou_balance[ou] = ou_balance_copy[ou]*-1 + ou_balance_copy[ou2]
        return ou_balance

    @api.model
    def create_ou_balance(self, credit_move_id, debit_move_id):
        ml_obj = self.env['account.move.line']
        if not credit_move_id.company_id.ou_is_self_balanced\
                and debit_move_id.company_id.ou_is_self_balanced:
            return False

        # If all move lines point to the same operating unit, there's no
        # need to create a balancing move line
        ou_list_ids = [credit_move_id.operating_unit_id.id,
                       debit_move_id.operating_unit_id.id]
        if ou_list_ids.count(ou_list_ids[0]) == len(ou_list_ids):
            return False

        # Create balancing entries for un-balanced OU's.
        amls = []
        payment = credit_move_id.payment_id or debit_move_id.payment_id
        ou_balances = self._check_pay_balance(credit_move_id.move_id.line_ids + debit_move_id.move_id.line_ids, payment)
        move_id = False
        for ou_id in ou_list_ids:
            # Create a balancing move line in the operating unit
            # clearing account
            if not move_id:
                if credit_move_id.payment_id:
                    move_id = self.env['account.move'].create(credit_move_id.payment_id._get_move_vals())
                else:
                    move_id = self.env['account.move'].create(debit_move_id.payment_id._get_move_vals())
            line_data = self.env['account.move']._prepare_inter_ou_balancing_move_line(
                move_id, ou_id, ou_balances)
            if line_data:
                amls.append(ml_obj.with_context(wip=True).
                            create(line_data))
        if amls:
            move_id.with_context(wip=False).\
                write({'line_ids': [(4, aml.id) for aml in amls]})
            move_id.with_context({'reconciling': True}).post()
        return move_id.id


class AccountMove(models.Model):
    _inherit = "account.move"

    operating_unit_id = fields.Many2one('operating.unit',
                                        'Default operating unit',
                                        help="This operating unit will "
                                             "be defaulted in the move lines.")

    @api.multi
    def _prepare_inter_ou_balancing_move_line(self, move, ou_id,
                                              ou_balances):
        if not move.company_id.inter_ou_clearing_account_id:
            raise UserError(_('Error!\nYou need to define an inter-operating\
                unit clearing account in the company settings'))

        res = {
            'name': 'OU-Balancing',
            'move_id': move.id,
            'journal_id': move.journal_id.id,
            'date': move.date,
            'operating_unit_id': ou_id,
            'account_id': move.company_id.inter_ou_clearing_account_id.id
        }

        if ou_balances[ou_id] < 0.0:
            res['debit'] = abs(ou_balances[ou_id])

        else:
            res['credit'] = ou_balances[ou_id]
        return res

    @api.multi
    def _check_ou_balance(self, move):
        # Look for the balance of each OU
        ou_balance = {}
        for line in move.line_ids:
            if line.operating_unit_id.id not in ou_balance:
                ou_balance[line.operating_unit_id.id] = 0.0
            ou_balance[line.operating_unit_id.id] += (line.debit - line.credit)
        return ou_balance

    @api.multi
    def post(self):
        ml_obj = self.env['account.move.line']
        for move in self:
            if self.env.context.get('reconciling', False):
                continue
            if not move.company_id.ou_is_self_balanced:
                continue

            # If all move lines point to the same operating unit, there's no
            # need to create a balancing move line
            ou_list_ids = [line.operating_unit_id and
                           line.operating_unit_id.id for line in
                           move.line_ids if line.operating_unit_id]
            if len(ou_list_ids) <= 1:
                continue

            # Create balancing entries for un-balanced OU's.
            ou_balances = self._check_ou_balance(move)
            amls = []
            for ou_id in ou_balances.keys():
                # If the OU is already balanced, then do not continue
                if move.company_id.currency_id.is_zero(ou_balances[ou_id]):
                    continue
                # Create a balancing move line in the operating unit
                # clearing account
                line_data = self._prepare_inter_ou_balancing_move_line(
                    move, ou_id, ou_balances)
                if line_data:
                    amls.append(ml_obj.with_context(wip=True).
                                create(line_data))
            if amls:
                move.with_context(wip=False).\
                    write({'line_ids': [(4, aml.id) for aml in amls]})

        return super(AccountMove, self).post()

    def assert_balanced(self):
        if self.env.context.get('wip'):
            return True
        return super(AccountMove, self).assert_balanced()

    @api.multi
    @api.constrains('line_ids')
    def _check_ou(self):
        for move in self:
            if not move.company_id.ou_is_self_balanced:
                continue
            for line in move.line_ids:
                if not line.operating_unit_id:
                    raise UserError(_('Configuration error!\nThe operating\
                    unit must be completed for each line if the operating\
                    unit has been defined as self-balanced at company level.'))


class AccountPartialReconcile(models.Model):
    _inherit = 'account.partial.reconcile'

    bal_move_id = fields.Many2one(
        'account.move', index=True)

    @api.multi
    def reverse_bal_entries(self):
        res = False
        for rec in self:
            res = rec.bal_move_id.reverse_moves()
        return res

    @api.multi
    def assign_balance_to_partial_reconcile(self):
        if self.env.context.get('reversal', False):
            return
        ml_obj = self.env['account.move.line']
        for rec in self:
            if rec.bal_move_id:
                rec.with_context({'reversal': True, 'reconciling': True}).reverse_bal_entries()
            if rec.debit_move_id.operating_unit_id != rec.credit_move_id.operating_unit_id:
                rec.bal_move_id = ml_obj.create_ou_balance(rec.credit_move_id, rec.debit_move_id)

    @api.model
    def create(self, vals):
        res = super(AccountPartialReconcile, self).create(vals)
        res.assign_balance_to_partial_reconcile()
        return res

    @api.multi
    def write(self, vals):
        if not vals.get('bal_move_id', False) and not vals.get('full_reconcile_id', False):
            self.assign_balance_to_partial_reconcile()
        return super(AccountPartialReconcile, self).write(vals)

    @api.multi
    def unlink(self):
        if self.bal_move_id:
            self.with_context({'reversal': True, 'reconciling': True}).reverse_bal_entries()
        result = super(AccountPartialReconcile, self).unlink()
        return result
