from odoo import models, fields


class RentalApprovalConfig(models.Model):
    _name = 'rental.approval.config'
    _description = 'Rental Approval Configuration'
    _rec_name = 'level'

    level = fields.Selection([
        ('1', 'L1 Manager'),
        ('2', 'L2 Sr Manager'),
        ('3', 'L3 Director'),
    ], required=True)

    user_id = fields.Many2one(
        'res.users',
        required=True
    )

    def name_get(self):
        res = []
        # Show selection label + approver name for clarity in dropdowns/tags
        labels = dict(self._fields['level'].selection)
        for rec in self:
            level_label = labels.get(rec.level, rec.level or '')
            if rec.user_id and rec.user_id.name:
                display = f"{level_label} — {rec.user_id.name}"
            else:
                display = level_label
            res.append((rec.id, display))
        return res
    
    
    
    