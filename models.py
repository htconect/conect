from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, String, Text, Time,
    UniqueConstraint, func
)
from sqlalchemy.orm import relationship
from database import Base


class Empresa(Base):
    __tablename__ = "empresas"

    id = Column(Integer, primary_key=True)
    nome = Column(String(120), nullable=False)
    slug = Column(String(80), nullable=False, unique=True, index=True)
    identificador_principal = Column(String(20), nullable=False, default="telefone")  # telefone, cpf, cnpj
    ativa = Column(Boolean, default=True)
    usuario_admin = Column(String(80), nullable=True, unique=True, index=True)
    senha_admin = Column(String(120), nullable=True)
    criado_em = Column(DateTime, server_default=func.now())
    pix_copia_cola = Column(Text, nullable=True)
    suporte_inicio = Column(String(5), nullable=True)
    suporte_fim = Column(String(5), nullable=True)
    mostrar_suporte_contrato = Column(Boolean, default=False)
    logo_url = Column(String(300), nullable=True)
    tema = Column(String(30), default="azul")
    mensagem_reserva = Column(Text, nullable=True)
    mensagem_aceite = Column(Text, nullable=True)
    mensagem_pagamento = Column(Text, nullable=True)
    mensagem_confirmacao = Column(Text, nullable=True)
    mensagem_preparacao = Column(Text, nullable=True)
    mensagem_a_caminho = Column(Text, nullable=True)
    mensagem_localizacao = Column(Text, nullable=True)
    mensagem_hora_fim = Column(Text, nullable=True)
    mostrar_mensagem_hora_fim = Column(Boolean, default=True)
    logo_idb_url = Column(String(300), nullable=True)

    clientes = relationship("Cliente", back_populates="empresa")
    produtos = relationship("ProdutoServico", back_populates="empresa")
    contratos = relationship("Contrato", back_populates="empresa")



class UsuarioEmpresa(Base):
    __tablename__ = "usuarios_empresa"
    __table_args__ = (UniqueConstraint("empresa_id", "usuario", name="uq_usuario_empresa"),)

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    nome = Column(String(120), nullable=False)
    usuario = Column(String(80), nullable=False, index=True)
    senha = Column(String(120), nullable=False)
    ativo = Column(Boolean, default=True)
    visualiza_financeiro = Column(Boolean, default=True)
    criado_em = Column(DateTime, server_default=func.now())

    empresa = relationship("Empresa")


class CampoGlobal(Base):
    __tablename__ = "campos_globais"

    id = Column(Integer, primary_key=True)
    chave = Column(String(80), nullable=False, unique=True)
    rotulo = Column(String(120), nullable=False)
    tipo = Column(String(30), nullable=False, default="texto")  # texto, data, hora, email, telefone
    ativo = Column(Boolean, default=True)


class CampoEmpresa(Base):
    __tablename__ = "campos_empresa"
    __table_args__ = (UniqueConstraint("empresa_id", "campo_id", name="uq_empresa_campo"),)

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    campo_id = Column(Integer, ForeignKey("campos_globais.id"), nullable=False)
    obrigatorio = Column(Boolean, default=False)
    visivel = Column(Boolean, default=True)
    ordem = Column(Integer, default=0)

    empresa = relationship("Empresa")
    campo = relationship("CampoGlobal")


class Cliente(Base):
    __tablename__ = "clientes"
    __table_args__ = (UniqueConstraint("empresa_id", "identificador", name="uq_cliente_empresa_identificador"),)

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    identificador = Column(String(60), nullable=False, index=True)
    telefone = Column(String(30))
    cpf = Column(String(20))
    cnpj = Column(String(25))
    nome = Column(String(160))
    data_nascimento = Column(Date, nullable=True)
    email = Column(String(160))
    endereco = Column(String(200))
    numero = Column(String(30))
    complemento = Column(String(120))
    bairro = Column(String(120))
    cidade = Column(String(120))
    estado = Column(String(40))
    cep = Column(String(20))
    observacoes = Column(Text)
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())
    criado_em = Column(DateTime, server_default=func.now())

    empresa = relationship("Empresa", back_populates="clientes")
    solicitacoes = relationship("Solicitacao", back_populates="cliente")
    equipamentos = relationship("EquipamentoCliente", back_populates="cliente")


class EquipamentoCliente(Base):
    __tablename__ = "equipamentos_clientes"

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    nome = Column(String(140), nullable=False)
    marca = Column(String(100))
    modelo = Column(String(100))
    numero_serie = Column(String(120))
    observacoes = Column(Text)
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, server_default=func.now())

    cliente = relationship("Cliente", back_populates="equipamentos")


class Contrato(Base):
    __tablename__ = "contratos"

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    nome = Column(String(140), nullable=False)
    descricao = Column(Text)
    clausulas = Column(Text, nullable=False)
    ativo = Column(Boolean, default=True)

    empresa = relationship("Empresa", back_populates="contratos")


class ProdutoServico(Base):
    __tablename__ = "produtos_servicos"

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    contrato_id = Column(Integer, ForeignKey("contratos.id"))
    nome = Column(String(140), nullable=False)
    descricao = Column(Text)
    tipo_locacao = Column(String(50), default="livre")  # livre ou horas_fixas
    horas_fixas = Column(Integer, nullable=True)
    quantidade_disponivel = Column(Integer, default=1)
    valor_base = Column(Float, default=0)
    duracao_minutos = Column(Integer, default=240)
    prazo_retirada_dias = Column(Integer, default=1)
    ativo = Column(Boolean, default=True)

    empresa = relationship("Empresa", back_populates="produtos")
    contrato = relationship("Contrato")


class Solicitacao(Base):
    __tablename__ = "solicitacoes"

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos_servicos.id"), nullable=True)
    contrato_id = Column(Integer, ForeignKey("contratos.id"), nullable=True)

    data_evento = Column(Date, nullable=False)
    hora_inicio = Column(Time, nullable=False)
    hora_fim = Column(Time, nullable=True)
    bairro = Column(String(120))
    local = Column(String(200))
    local_nome = Column(String(160))
    local_responsavel_nome = Column(String(160))
    local_responsavel_telefone = Column(String(40))
    acesso_local = Column(String(40))
    valor = Column(Float, default=0)
    sinal = Column(Float, default=0)
    valor_pago = Column(Float, default=0)
    sinal_recebido = Column(Boolean, default=False)
    pagamento_confirmado_em = Column(DateTime, nullable=True)
    observacoes = Column(Text)
    status = Column(String(30), default="pre_reserva")  # pre_reserva, aprovada, rejeitada, alteracao
    aceite_em = Column(DateTime, server_default=func.now())
    criado_em = Column(DateTime, server_default=func.now())

    cliente = relationship("Cliente", back_populates="solicitacoes")
    produto = relationship("ProdutoServico")
    contrato = relationship("Contrato")
    itens = relationship("ReservaItem", back_populates="solicitacao", cascade="all, delete-orphan")
    aprovado_em = Column(DateTime, nullable=True)
    cancelado_em = Column(DateTime, nullable=True)

    agenda = relationship("Agenda", back_populates="solicitacao", uselist=False)
    pagamentos = relationship("Pagamento", back_populates="solicitacao", cascade="all, delete-orphan")


class ReservaItem(Base):
    __tablename__ = "reserva_itens"

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    solicitacao_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=False)
    produto_id = Column(Integer, ForeignKey("produtos_servicos.id"), nullable=True)
    nome = Column(String(160), nullable=False)
    descricao = Column(Text)
    quantidade = Column(Integer, default=1)
    valor_unitario = Column(Float, default=0)
    valor_total = Column(Float, default=0)

    solicitacao = relationship("Solicitacao", back_populates="itens")
    produto = relationship("ProdutoServico")


class Pagamento(Base):
    __tablename__ = "pagamentos"

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    solicitacao_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=False)
    data_pagamento = Column(Date, nullable=False)
    valor = Column(Float, default=0)
    forma_pagamento = Column(String(30))
    comprovante_no_nome_cliente = Column(Boolean, default=True)
    nome_comprovante = Column(String(160))
    observacoes = Column(Text)
    usuario_registro = Column(String(120))
    conciliado_por = Column(String(120))
    conciliado_em = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, server_default=func.now())

    solicitacao = relationship("Solicitacao", back_populates="pagamentos")


class Agenda(Base):
    __tablename__ = "agenda"

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    solicitacao_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=False)
    data = Column(Date, nullable=False, index=True)
    hora_inicio = Column(Time, nullable=False)
    hora_fim = Column(Time, nullable=True)
    titulo = Column(String(180), nullable=False)
    bairro = Column(String(120))
    criado_em = Column(DateTime, server_default=func.now())
    ordem_rota = Column(Integer, default=0)
    previsao_entrega = Column(String(5))
    link_localizacao = Column(Text)
    tipo_evento = Column(String(20), default="entrega")  # entrega ou retirada
    status_operacional = Column(String(20), default="pendente")  # pendente ou concluido
    observacoes_operacionais = Column(Text, nullable=True)

    solicitacao = relationship("Solicitacao", back_populates="agenda")


class ContaFinanceira(Base):
    __tablename__ = "contas_financeiras"

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    nome = Column(String(80), nullable=False)
    tipo = Column(String(20), default="banco")  # banco, dinheiro, cartao
    saldo_inicial = Column(Float, default=0)
    ativa = Column(Boolean, default=True)
    criado_em = Column(DateTime, server_default=func.now())


class LancamentoBanco(Base):
    __tablename__ = "lancamentos_banco"

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    conta_id = Column(Integer, ForeignKey("contas_financeiras.id"), nullable=False)
    data = Column(Date, nullable=False, index=True)
    historico = Column(Text, nullable=False)
    documento = Column(String(80), nullable=True)
    valor = Column(Float, default=0)
    saldo = Column(Float, default=0)
    categoria = Column(String(20), default="aluguel")  # casa, empresa, aluguel, manutencao
    categoria_confirmada = Column(Boolean, default=False)
    pagamento_id = Column(Integer, ForeignKey("pagamentos.id"), nullable=True)
    hash_importacao = Column(String(64), nullable=True, index=True)
    origem_importacao = Column(String(120), nullable=True)
    ordem = Column(Integer, default=0, index=True)
    criado_em = Column(DateTime, server_default=func.now())

    conta = relationship("ContaFinanceira")
    pagamento = relationship("Pagamento")


class LancamentoManualFinanceiro(Base):
    __tablename__ = "lancamentos_manuais_financeiros"

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False)
    conta_id = Column(Integer, ForeignKey("contas_financeiras.id"), nullable=False)
    data = Column(Date, nullable=False, index=True)
    descricao = Column(Text, nullable=False)
    valor = Column(Float, default=0)
    categoria = Column(String(20), default="empresa")
    tipo = Column(String(20), default="real")  # real ou receber
    recebido = Column(Boolean, default=False)
    pagamento_id = Column(Integer, ForeignKey("pagamentos.id"), nullable=True)
    ordem = Column(Integer, default=0, index=True)
    criado_em = Column(DateTime, server_default=func.now())

    conta = relationship("ContaFinanceira")
    pagamento = relationship("Pagamento")
