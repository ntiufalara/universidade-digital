#coding:utf8

from osv import fields, osv


class ud_solicitacao_responsavel (osv.osv):
    _name = "ud.solicitacao.responsavel"
    _columns = {
                "name": fields.char("Nome"),
                "responsavel_id": fields.many2one ("ud.employee","Responsável"),                                
                }
    
    def nome (self, cr, uid, ids,context=None):
        responsavel = self.read(cr, uid, ids)[0]['responsavel_id'][0]
        resp = self.pool.get("ud.employee").browse(cr, uid, responsavel)
        if not self.read (cr, uid, ids)[0]['name']:
#             self.add_grupo(cr, uid, ids, context, resp)
            self.write (cr, uid, ids, {"name":resp.name})
        return True
    
    def add_grupo (self, cr, uid, ids, context, pessoa_id):
        '''
        Adiciona o responsável ao grupo "base.responsavel_os"
        '''
        cr.execute('''SELECT 
                      resource_resource.user_id
                    FROM 
                      public.ud_employee, 
                      public.resource_resource
                    WHERE 
                      ud_employee.id = %s AND
                      ud_employee.resource_id = resource_resource.id''' %(pessoa_id.id))

        user_id = cr.fetchone()[0]
        cr.execute('''SELECT
                        ir_model_access.group_id
                      FROM
                        public.ir_model_access,
                        public.res_groups
                      WHERE
                        ir_model_access.name = 'ud_solicitacao.responsavel'
            ''')
        group_id = cr.fetchone()[0]
        grupo = self.pool.get("res.groups").browse(cr, uid, 10)
        usuario = self.pool.get("res.users").browse(cr, uid, user_id)
        for user in grupo.users:
            print user
        novo_grupo = grupo.users
        novo_grupo.append(grupo)
        self.pool.get("res.groups").write(cr, uid, [group_id], {"users":novo_grupo})

    _constraints = [(nome, "Criado", ["Salvar"])]
    