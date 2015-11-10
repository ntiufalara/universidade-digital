{
'name':'Gerenciamento de Espaço (UD)',
'version':'1.0',
'category':'Universidade Digital',
'description':'Aplicação para gerenciamento de espaço',
'author':'NTI',
'depends':['base','ud'],
'data': [
         'ud_reserva_view.xml',
         'forms/cancelar_view.xml',
         'security/ir.model.access.csv'
         ],
'installable':True,

'update_xml':['security/ud_reserva_security.xml'
              ]
}