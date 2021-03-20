# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HrJob(models.Model):
    _inherit = 'hr.job'

    job_code = fields.Integer('Job code')


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    job_code = fields.Integer(related='job_id.job_code', store=True, readonly=False)
    expiration_date = fields.Date('Date expiration DNI')
    number_nss = fields.Integer('Number NSS')
    indicator = fields.Boolean('Advance indicator')
    advance_amount = fields.Float('Advance amount')
    antiquity_date = fields.Date('Antiquity date')
    clothing_size = fields.Char('Clothing size')
    shoe_size = fields.Char('Shoe size')
    pant_size = fields.Char('Pant size')
    holiday_group = fields.Char('Holiday group')
    medical_cost = fields.Float('Medical insurance cost')

    # Fields Conductor
    driving_license = fields.Boolean('Driving license', help="Driving license indicator.")
    driving_license_date_start = fields.Date('Driving license start date', help="Driving license start date.")
    driving_license_expiration_date = fields.Date('Driving license expiration date',
                                                  help="Driving license expiration date.")

    indicator_adr = fields.Boolean('Indicator A.D.R', help="Indicator A.D.R.")
    date_start_adr = fields.Date('Date start A.D.R', help="Date start A.D.R.")
    date_expiration_adr = fields.Date('Date expiration A.D.R', help="Date expiration A.D.R.")

    indicator_adr_cistern = fields.Boolean('Indicator A.D.R Cistern', help="Indicator A.D.R Cistern.")
    date_start_cistern = fields.Date('Date start A.D.R Cistern', help="Date start A.D.R Cistern.")
    date_expiration_cistern = fields.Date('Date expiration A.D.R Cistern', help="Date expiration A.D.R Cistern.")

    indicator_card = fields.Boolean('Digital tachograph card indicator', help="Digital tachograph card indicator.")
    date_start_card = fields.Date('Date start card', help="Start date of digital tachograph card.")
    date_expiration_card = fields.Date('Date expiration card', help="Expiration date of digital tachograph card.")

    indicator_certificate = fields.Boolean('Professional aptitude certificate',
                                           help="Professional aptitude certificate indicator.")
    date_start_certificate = fields.Date('Date start certificate', help="Start date professional aptitude certificate.")
    date_expiration_certificate = fields.Date('Date expiration certificate',
                                              help="Expiration date professional aptitude certificate.")

    identification_card = fields.Boolean('Identification card',
                                         help="Indicator Identification card.")
    number_driver = fields.Integer('Driver number LURBE')
    is_conductor = fields.Boolean('Is conductor', default=True)

    @api.onchange('address_id')
    def _onchange_work_location(self):
        for employee in self:
            if employee.address_id:
                employee.work_location = employee.address_id.city




