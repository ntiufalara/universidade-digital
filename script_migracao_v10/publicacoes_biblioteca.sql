select pb.name, 
	   pb.ano_pub, 
	   o.name
from ud_biblioteca_publicacao as pb, ud_biblioteca_orientador as o, ud_biblioteca_publicacao_orientador_rel as orientador_rel where pb.id = orientador_rel.pub_id and orientador_rel.orientador_id = o.id;
