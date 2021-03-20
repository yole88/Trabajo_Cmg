# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    medical_checkup_ids = fields.One2many('hr.medical.checkup', 'employee_id',
                                          string="Medical checkup")
    checkup_count = fields.Integer(compute='_compute_medical_medical_count', string='Checkup')

    def _compute_medical_medical_count(self):
        fetch_data = self.env['hr.medical.checkup'].read_group([('employee_id', 'in', self.ids)], ['employee_id'],
                                                        ['employee_id'])
        result = dict((data['employee_id'][0], data['employee_id_count']) for data in fetch_data)
        for employee in self:
            employee.checkup_count = result.get(employee.id, 0)


class MedicalCheckup(models.Model):
    _name = 'hr.medical.checkup'
    _description = 'Medical checkup'
    _rec_name = 'employee_id'
    _inherit = ['mail.thread']

    employee_id = fields.Many2one(
        'hr.employee', 'Employee', index=True, required=True)
    number_employee = fields.Integer('Number employee')
    company_id = fields.Many2one(related='employee_id.company_id',
                                 string='Company', store=True, readonly=True)
    date_revision = fields.Date('Revision date', default=fields.Date.context_today, required=True)
    observation = fields.Text('Observations')
    apt_type = fields.Selection([('apt', 'Apt'), ('no_apt', 'No apt')], "Type apt", default='no_apt')
    done_type = fields.Selection([('done', 'Done'), ('no_done', 'No done')], "Type done", default='no_done')
    is_future = fields.Boolean(compute='_compute_is_future', store=True)

    @api.one
    @api.depends('date_revision')
    def _compute_is_future(self):
        for record in self:
            record.is_future = True if record.date_revision > fields.Date.context_today(self) else False

    @api.constrains('done_type', 'date_revision')
    def check_done(self):
        for employee in self:
            if employee.done_type == 'done' and employee.date_revision > fields.Date.context_today(self):
                raise UserError(_('The medical review cannot be marked as completed, '
                                  'the review date is in the future.'))





