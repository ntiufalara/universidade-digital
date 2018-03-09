# encoding: UTF-8
from ast import literal_eval

from odoo import models, fields, api
from odoo.addons.auth_signup.models.res_partner import SignupError
from odoo.loglevels import ustr


class User(models.Model):
    _name = 'res.users'
    _inherit = 'res.users'

    @api.model
    def _signup_create_user(self, values):
        """
        Copiado de auth_signup.models.res_users.ResUsers
        :param values:
        :return:
        """
        """ create a new user from the template user """
        IrConfigParam = self.env['ir.config_parameter']
        template_user_id = literal_eval(IrConfigParam.get_param('auth_signup.template_user_id', 'False'))
        template_user = self.browse(template_user_id)
        assert template_user.exists(), 'Signup: invalid template user'

        # check that uninvited users may sign up
        if 'partner_id' not in values:
            if not literal_eval(IrConfigParam.get_param('auth_signup.allow_uninvited', 'False')):
                raise SignupError('Signup is not allowed for uninvited users')

        assert values.get('login'), "Signup: no login given for new user"
        assert values.get('partner_id') or values.get('name'), "Signup: no name or partner given for new user"

        # create a copy of the template user (attached to a specific partner_id if given)
        values['active'] = True
        try:
            with self.env.cr.savepoint():
                print(values)
                result = self.search([('email', '=', values.get('login'))])
                print(result)
                if not result:
                    result = template_user.with_context(no_reset_password=True).copy(values)
                if result.perfil_ids:
                    print(result.perfil_ids)
                print(result)
                return result
        except Exception, e:
            # copy may failed if asked login is not available.
            raise SignupError(ustr(e))

