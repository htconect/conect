
from sqlalchemy.orm import Session
from models import CampoGlobal

CAMPOS_PADRAO = [
    ("telefone", "Telefone", "telefone"),
    ("cpf", "CPF", "texto"),
    ("cnpj", "CNPJ", "texto"),
    ("nome", "Nome", "texto"),
    ("data_nascimento", "Data de nascimento", "data"),
    ("email", "E-mail", "email"),
    ("endereco", "Endereço", "texto"),
    ("numero", "Número", "texto"),
    ("complemento", "Complemento", "texto"),
    ("bairro", "Bairro", "texto"),
    ("cidade", "Cidade", "texto"),
    ("estado", "Estado", "texto"),
    ("cep", "CEP", "texto"),
    ("local_nome", "Nome do local", "texto"),
    ("local", "Referência do local", "texto"),
    ("acesso_local", "Acesso ao local", "texto"),
    ("local_responsavel_nome", "Responsável no local", "texto"),
    ("local_responsavel_telefone", "Telefone do responsável", "telefone"),
    ("data_evento", "Data do evento", "data"),
    ("hora_inicio", "Hora de início", "hora"),
    ("hora_fim", "Hora de término", "hora"),
    ("observacoes", "Observações", "texto"),
]

def inicializar_dados(db: Session):
    for chave, rotulo, tipo in CAMPOS_PADRAO:
        if not db.query(CampoGlobal).filter_by(chave=chave).first():
            db.add(CampoGlobal(chave=chave, rotulo=rotulo, tipo=tipo))
    db.commit()
