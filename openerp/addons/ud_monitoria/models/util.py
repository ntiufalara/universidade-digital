# coding: utf-8
from datetime import datetime
from re import compile, IGNORECASE
from openerp import SUPERUSER_ID
from openerp.osv.fields import date
from openerp.tools import DEFAULT_SERVER_DATE_FORMAT

regex_order = compile("^((?:(?:CASE(?: WHEN \w+ *= *'\w+' THEN \d+)+ ELSE \d+ END)|(?:\w+))(?: (?:(?:asc)|(?:desc)))?)(, *(?:(?:CASE(?: WHEN \w+ *= *'\w+' THEN \d+)+ ELSE \d+ END)|(?:\w+))(?: (?:(?:asc)|(?:desc)))?)?$", IGNORECASE)
regex_regra = compile('CASE .+ ELSE (?P<ord>\d+) END (?P<dir>(?:asc)|(?:desc))?', IGNORECASE)
regex_clausula = compile("WHEN (?P<campo>\w+) *= *(?P<valor>'\w+') THEN (?P<ord>\d+)", IGNORECASE)
regex_espacos = compile("\s+")

_MESES = [('01', u'Janeiro'), ('02', u'Fevereiro'), ('03', u'Março'), ('04', u'Abril'), ('05', u'Maio'),
          ('06', u'Junho'), ('07', u'julho'), ('08', u'Agosto'), ('09', u'Setembro'), ('10', u'Outubro'),
          ('11', u'Novembro'), ('12', u'Dezembro')]


def get_ud_pessoa_id(cls, cr, uid):
    res = cls.pool.get('ud.employee').search(cr, SUPERUSER_ID, [('user_id', '=', uid)], limit=2)
    if res:
        return res[0]


def get_ud_pessoa(cls, cr, uid):
    pessoa_id = get_ud_pessoa_id(cls, cr, uid)
    if pessoa_id:
        return cls.pool.get('ud.employee').browse(cr, SUPERUSER_ID, pessoa_id)


def data_hoje(cls, cr, uid=SUPERUSER_ID):
    return datetime.strptime(date.context_today(cls, cr, uid, {'tz': u'America/Maceio'}), DEFAULT_SERVER_DATE_FORMAT).date()
