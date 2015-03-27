# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2011 OpenERP S.A (<http://www.openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv

class change_password_wizard(osv.TransientModel):
    """
        A wizard to manage the change of users' passwords
    """

    _name = "change.password.wizard.ud"
    _description = "Change Password Wizard"
    _columns = {
        'user_ids': fields.one2many('change.password.user.ud', 'wizard_id', string='Users'),
    }

    def default_get(self, cr, uid, fields, context=None):
        if context == None:
            context = {}
        user_ids = context.get('active_ids', [])
        wiz_id = context.get('active_id', None)
        res = []
        users = self.pool.get('ud.employee').browse(cr, uid, user_ids, context=context)
        for user in users:
            res.append((0, 0, {
                'wizard_id': wiz_id,
                'user_id': user.res_users_id,
                'user_login': user.login_user,
            }))
            
        print users
        print "\n\n\n\n\n\n\n"
        return {'user_ids': res}


    def change_password_button(self, cr, uid, id, context=None):
        wizard = self.browse(cr, uid, id, context=context)[0]
        need_reload = any(uid == user.user_id.id for user in wizard.user_ids)
        line_ids = [user.id for user in wizard.user_ids]

        self.pool.get('change.password.user.ud').change_password_button(cr, uid, line_ids, context=context)
        # don't keep temporary password copies in the database longer than necessary
        self.pool.get('change.password.user.ud').write(cr, uid, line_ids, {'new_passwd': False}, context=context)

        if need_reload:
            return {
                'type': 'ir.actions.client',
                'tag': 'reload'
            }

        return {'type': 'ir.actions.act_window_close'}


class change_password_user(osv.TransientModel):
    """
        A model to configure users in the change password wizard
    """

    _name = 'change.password.user.ud'
    _description = 'Change Password Wizard User'
    _columns = {
        'wizard_id': fields.many2one('change.password.wizard.ud', string='Wizard', required=True),
        'user_id': fields.many2one('res.users', string='User', required=True),
        'user_login': fields.char('User Login', readonly=True),
        'new_passwd': fields.char('New Password'),
    }
    _defaults = {
        'new_passwd': '',
    }

    def change_password_button(self, cr, uid, ids, context=None):
        for user in self.browse(cr, uid, ids, context=context):
            self.pool.get('res.users').write(cr, uid, user.user_id.id, {'password': user.new_passwd})

