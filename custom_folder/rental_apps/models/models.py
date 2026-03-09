# from odoo import models, fields, api


# class rental_apps(models.Model):
#     _name = 'rental_apps.rental_apps'
#     _description = 'rental_apps.rental_apps'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

