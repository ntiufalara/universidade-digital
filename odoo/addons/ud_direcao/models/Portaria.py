# encoding: UTF-8

from odoo import models, fields, api


class Portaria(models.Model):
    """
    Representa um documento (Portaria) emitido por algum setor dentro da universidade
    """
    _name = 'ud.direcao.portaria'

    _rec_name = 'nro_portaria'

    nro_portaria = fields.Char(u'Número', required=True)
    descricao = fields.Text(u'Descrição', required=True)
    data = fields.Date('Data', required=True)
    file_name = fields.Char('Nome do arquivo', )
    anexo = fields.Binary('Anexo', required=True)
    campus_id = fields.Many2one('ud.campus', "Campus", required=True)
    polo_id = fields.Many2one('ud.polo', 'Polo', required=True, domain="[('campus_id', '=', campus_id)]")
    setor_id = fields.Many2one('ud.setor', 'Emissor', required=True,
                               domain="[('polo_id', '=', polo_id), ('emite_portaria', '=', True)]")
    responsavel_id = fields.Many2one('res.users', u'Responsável', readonly=True, related='setor_id.responsavel_id')
    setor_destino_id = fields.Many2one('ud.setor', "Destino", required=False, domain="[('polo_id', '=', polo_id)]")
