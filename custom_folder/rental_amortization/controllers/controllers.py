# from odoo import http


# class RentalAmortization(http.Controller):
#     @http.route('/rental_amortization/rental_amortization', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rental_amortization/rental_amortization/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('rental_amortization.listing', {
#             'root': '/rental_amortization/rental_amortization',
#             'objects': http.request.env['rental_amortization.rental_amortization'].search([]),
#         })

#     @http.route('/rental_amortization/rental_amortization/objects/<model("rental_amortization.rental_amortization"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rental_amortization.object', {
#             'object': obj
#         })

