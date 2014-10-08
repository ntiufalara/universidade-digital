# -*- coding: utf-8 -*-

from osv import fields, osv


class Pais(osv.osv):
    _name = 'ud.pais'
    _description = 'País'
    _columns = {
        'name': fields.char('Nome do País', size=64,
            help='O nome completo do país.', required=True, translate=True),
        'code': fields.char('Código do país', size=2,
            help='O código do país \'ISO\' em dois caracteres.', required=True),
        'address_format': fields.text('Address Format', help="""You can state here the usual format to use for the \
addresses belonging to this country.\n\nYou can use the python-style string patern with all the field of the address \
(for example, use '%(street)s' to display the field 'street') plus
            \n%(state_name)s: the name of the state
            \n%(state_code)s: the code of the state
            \n%(country_name)s: the name of the country
            \n%(country_code)s: the code of the country"""),
    }
    _sql_constraints = [
        ('name_uniq', 'unique (name)',
            'O nome do país deve ser único !'),
        ('code_uniq', 'unique (code)',
            'O código do país deve ser único !')
    ]
    _defaults = {
        'address_format': "%(street)s\n%(street2)s\n%(city)s,%(state_code)s %(zip)s\n%(country_name)s",
    }
    def create(self, cursor, user, vals, context=None):
        if 'code' in vals:
            vals['code'] = vals['code'].upper()
        return super(Country, self).create(cursor, user, vals,
                context=context)

    def write(self, cursor, user, ids, vals, context=None):
        if 'code' in vals:
            vals['code'] = vals['code'].upper()
        return super(Country, self).write(cursor, user, ids, vals,
                context=context)

Pais()


class PaisEstado(osv.osv):
    _description="Estado do País"
    _name = 'ud.pais.estado'
    _columns = {
        'pais_id': fields.many2one('ud.pais', 'País',
            required=True),
        'name': fields.char('Nome do estado', size=64, required=True),
        'code': fields.char('Código do estado', size=3,
            help='O código do estado em três caracteres.'),
    }
#    def name_search(self, cr, user, name='', args=None, operator='ilike',
#            context=None, limit=100):
#        if not args:
#            args = []
#        if not context:
#            context = {}
#        ids = self.search(cr, user, [('code', 'ilike', name)] + args, limit=limit,
#                context=context)
#        if not ids:
#            ids = self.search(cr, user, [('name', operator, name)] + args,
#                    limit=limit, context=context)
#        return self.name_get(cr, user, ids, context)

    _order = 'code'
PaisEstado()