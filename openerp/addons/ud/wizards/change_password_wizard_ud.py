# -*- coding: utf-8 -*-
from openerp.osv import fields, osv


class change_password_wizard(osv.TransientModel):
    """
       Troca a senha do Pessoa selecionada na visão tree.
    """

    _name = "change.password.wizard.ud"
    _description = "Change Password Wizard"
    _columns = {
        'user_ids': fields.one2many('change.password.user.ud', 'wizard_id', string='Users'),
    }

    def default_get(self, cr, uid, fields_list, context=None):
        context = context or {}
        res = super(change_password_wizard, self).default_get(cr, uid, fields_list, context)
        ids = context.get("active_ids", None)
        if context.get("active_model", False) == "ud.employee" and ids:
            users = []
            for pessoa in self.pool.get("ud.employee").browse(cr, uid, ids, context):
                if pessoa.user_id:
                    users.append((0, 0, {"user_id": pessoa.user_id.id, "user_login": pessoa.user_id.login}))
            if users:
                res["user_ids"] = users
        return res

    def change_password_button(self, cr, uid, ids, context=None):
        wizard = self.browse(cr, uid, ids, context=context)[0]
        need_reload = any(uid == user.user_id.id for user in wizard.user_ids)
        line_ids = [user.id for user in wizard.user_ids]

        self.pool.get('change.password.user.ud').change_password_button(cr, uid, line_ids, context=context)

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
        'user_login': fields.char('Login do Usuário', readonly=True),
        'new_passwd': fields.char('Nova Senha'),
    }
    _defaults = {
        'new_passwd': '',
    }

    def change_password_button(self, cr, uid, ids, context=None):
        for usuario_senha in self.browse(cr, uid, ids, context=context):
            usuario_senha.user_id.write({'password': usuario_senha.new_passwd})
            # self.pool.get('res.users').write(cr, uid)

