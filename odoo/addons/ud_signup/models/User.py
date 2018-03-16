# encoding: UTF-8
from ast import literal_eval

from odoo import models, fields, api
from odoo.addons.auth_signup.models.res_partner import SignupError
from odoo.loglevels import ustr


class User(models.Model):
    _name = 'res.users'
    _inherit = 'res.users'

