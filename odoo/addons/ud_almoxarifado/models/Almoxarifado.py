# encoding: UTF-8

from odoo import models, fields, api


class Almoxarifado(models.Model):
    """
    Cadastro de almoxarifado, localização e responsável
    """
    _name = 'ud.almoxarifado.almoxarifado'

    name = fields.Char(u'Nome')
    campus_id = fields.Many2one('ud.campus', u'Campus', required=True)
    polo_id = fields.Many2one('ud.polo', u'Polo', domain="[('campus_id', '=', campus_id)]", required=True)
    setor_id = fields.Many2one('ud.setor', u'Setor', domain="[('polo_id', '=', polo_id)]", required=True)
    observacoes = fields.Text(u'Observações')
    responsavel_ids = fields.Many2many('ud.almoxarifado.responsavel', 'almoxarifado_responsavel_rel',
                                       string=u'Responsáveis')

    @api.model
    def create(self, vals):
        """
        Caso o usuário não escreva um nome, cira um nome tipo: Almoxarifado (setor) (polo)
        :param vals:
        :return:
        """
        obj = super(Almoxarifado, self).create(vals)
        if not obj.name:
            obj.name = 'Almoxarifado {} {}'.format(obj.setor_id.name, obj.polo_id.name)
        return obj
