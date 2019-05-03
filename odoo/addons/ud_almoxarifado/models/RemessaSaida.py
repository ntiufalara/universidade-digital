# encoding: UTF-8

from odoo import models, fields, api


class RemessaSaida(models.Model):
    """
    Saída de remessa, agrupa várias saídas de estoque
    """
    _name = 'ud.almoxarifado.remessa_saida'
    _order = 'id desc'

    name = fields.Char(u'Código', compute='get_name', readonly=True)
    data_hora = fields.Datetime(u'Data/hora', default=fields.datetime.now(), readonly=True)
    saida_ids = fields.One2many('ud.almoxarifado.saida', 'remessa_id', u'Saídas', required=True)
    campus_id = fields.Many2one('ud.campus', u'Campus', required=True)
    polo_id = fields.Many2one('ud.polo', u'Polo', domain="[('campus_id', '=', campus_id)]", required=True)
    almoxarifado_id = fields.Many2one('ud.almoxarifado.almoxarifado', u'Almoxarifado',
                                      domain="[('polo_id', '=', polo_id)]", required=True)

    def process_domain(self):
        """
        Usado para filtrar as listas apenas com itens aos quais o responsável tem acesso.
        :return: [(), (),...]
        """
        user = self.env.user
        grupo_gerente = self.env.ref('ud_almoxarifado.group_ud_almoxarifado_gerente')
        grupo_admin = self.env.ref('ud_almoxarifado.group_ud_almoxarifado_administrador')
        domain = []
        if grupo_gerente in user.groups_id and grupo_admin not in user.groups_id:
            alm_resposavel = []
            for res in user.almoxarifado_responsavel_ids:
                for alm in res.almoxarifado_ids:
                    alm_resposavel.append(alm.id)
            domain = [('almoxarifado_id', 'in', list(alm_resposavel))]
        return domain

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        domain = [] if not domain else domain
        domain += self.process_domain()
        return super(RemessaSaida, self).search_read(domain, fields, offset, limit, order)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        domain = [] if not domain else domain
        domain += self.process_domain()
        return super(RemessaSaida, self).read_group(domain, fields, groupby, offset, limit, orderby, lazy)

    @api.one
    def get_name(self):
        self.name = 'ALM_RM_SAIDA_{}'.format(self.id)
