{
'name':'Solicitação de OS (UD)',
'version':'1.0',
'category':'Universidade Digital',
'description':'Aplicação para solicitação de ordem de serviço',
'author':'NTI',
'depends':['base','ud'],
'data': [
         'ud_solicitacao_view.xml',
         "ud_solicitacao_view_gerente.xml",
         "ud_solicitacao_view_responsavel.xml",
         'wizards/atribuir_view.xml',
         'wizards/aprovar_view.xml',
         'wizards/executar_view.xml',
         "wizards/finalizar_view.xml",
         "wizards/cancelar_view.xml",
         "security/ir.model.access.csv",
         ],
'update_xml':[
            'security/ud_solicitacao_security.xml'
            ],
'installable':True,
}
