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
    def _check_ou_balance(self, debit_move_id, credit_move_id):
        # Look for the balance of each OU
        ou_balance = {}
        for line in debit_move_id + credit_move_id:
            if line.operating_unit_id.id not in ou_balance:
                ou_balance[line.operating_unit_id.id] = 0.0
            ou_balance[line.operating_unit_id.id] += (line.debit - line.credit)
        return ou_balance

    def prepare_account_move(self, journal=None):
        """ Return dict to create the inter OU move
        """
        journal = journal or self.journal_id
        if not journal.sequence_id:
            raise UserError(_('Configuration Error !'), _('The journal %s does not have a sequence, please specify one.') % journal.name)
        if not journal.sequence_id.active:
            raise UserError(_('Configuration Error !'), _('The sequence of journal %s is deactivated.') % journal.name)
        name = self.move_name or journal.with_context(ir_sequence_date=self.payment_date).sequence_id.next_by_id()
        return {
            'name': name,
            'date': self.payment_date,
            'ref': self.communication or '',
            'company_id': self.company_id.id,
            'journal_id': journal.id,
        }

    @api.model
    def create_ou_balance(self, credit_move_id, debit_move_id):
        ml_obj = self.env['account.move.line']
        if not credit_move_id.company_id.ou_is_self_balanced\
                and debit_move_id.company_id.ou_is_self_balanced:
            return False

        # If all move lines point to the same operating unit, there's no
        # need to create a balancing move line
        ou_list_ids = [credit_move_id.operating_unit_id and
                       debit_move_id.operating_unit_id.id]
        if len(ou_list_ids) <= 1:
            return False

        # Create balancing entries for un-balanced OU's.
        ou_balances = self._check_ou_balance(debit_move_id, credit_move_id)
        amls = []
        move_id = False
        for ou_id in ou_balances.keys():
            # Create a balancing move line in the operating unit
            # clearing account
            # If the OU is already balanced, then do not continue
            if credit_move_id.company_id.currency_id.is_zero(ou_balances[ou_id]) and debit_move_id.company_id.currency_id.is_zero(ou_balances[ou_id]):
                return False
            if not move_id:
                vals = self.prepare_account_move()
                move_id = self.env['account.move'].create(vals)
            line_data = self._prepare_inter_ou_balancing_move_line(
                credit_move_id.move_id, ou_id, ou_balances)
            if line_data:
                amls.append(ml_obj.with_context(wip=True).
                            create(line_data))
            if amls:
                move_id.with_context(wip=False).\
                    write({'line_ids': [(4, aml.id) for aml in amls]})
        return amls

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
    def write(self, vals):
        res = super(AccountPartialReconcile, self).write(vals)
        ml_obj = self.env['account.move.line']
        for rec in self:
            if rec.debit_move_id.operating_unit_id != rec.credit_move_id.operating_unit_id:
                bal_move = ml_obj.create_ou_balance(rec.credit_move_id, rec.debit_move_id)
                if bal_move:
                    vals['bal_move_id'] = bal_move.id
        return res
