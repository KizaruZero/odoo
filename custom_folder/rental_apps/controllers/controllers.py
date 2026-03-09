# from odoo import http


# class RentalApps(http.Controller):
#     @http.route('/rental_apps/rental_apps', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/rental_apps/rental_apps/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('rental_apps.listing', {
#             'root': '/rental_apps/rental_apps',
#             'objects': http.request.env['rental_apps.rental_apps'].search([]),
#         })

#     @http.route('/rental_apps/rental_apps/objects/<model("rental_apps.rental_apps"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('rental_apps.object', {
#             'object': obj
#         })

