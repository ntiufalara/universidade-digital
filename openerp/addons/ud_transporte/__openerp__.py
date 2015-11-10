{
    "name": "Transporte (UD)",
    "version": "1.1",
    "depends": ["base",'ud'],
    "author": "LaPEC",
    "category": "Universidade Digital",
    "description": """
    Módulo para gerenciamente de transporte universitário
    """,
    'data' : [
	      'security/ud_transporte_security.xml',
              'security/ir.model.access.csv',
              'ud_transporte_motorista_view.xml',
              'ud_transporte_veiculo_view.xml',
              'ud_transporte_manutencao_view.xml',
              'ud_transporte_solicitacao_view.xml',
              'ud_transporte_viagem_view.xml',
              'wizards/concluir_viagem_view.xml',

              ],
    'installable': True,
    'active': False,
#    'certificate': 'certificate',
}
