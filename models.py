from datetime import time
from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, ForeignKey, Integer, Numeric, String, Text, Time,
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
    pix_nome_recebedor = Column(String(160), nullable=True)
    pix_banco = Column(String(120), nullable=True)
    whatsapp_retorno = Column(String(30), nullable=True)
    infinitepay_ativa = Column(Boolean, default=False)
    infinitepay_handle = Column(String(80), nullable=True)
    infinitepay_valor_sinal = Column(Float, default=0)
    exige_sinal = Column(Boolean, default=False)
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
    # Carteira Humiat da empresa. A franquia mensal reinicia por competência; o saldo não vence.
    humiat_saldo = Column(Integer, nullable=False, default=0)
    humiat_gratis_mes = Column(Integer, nullable=False, default=4)
    humiat_custo_contrato = Column(Integer, nullable=False, default=1)

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
    telefone = Column(String(30), nullable=True)
    senha = Column(String(120), nullable=False)
    ativo = Column(Boolean, default=True)
    # Acessos por área de trabalho. O administrador principal da empresa ignora estas marcações.
    acesso_agenda = Column(Boolean, default=False)
    acesso_operacao = Column(Boolean, default=False)
    acesso_buscar_cliente = Column(Boolean, default=False)
    acesso_financeiro = Column(Boolean, default=False)
    acesso_cadastros = Column(Boolean, default=False)
    acesso_relatorios = Column(Boolean, default=False)
    # Permite visualizar cards ainda sem equipe/roteirização na Operação.
    acesso_nao_roteirizados = Column(Boolean, default=False)
    criado_em = Column(DateTime, server_default=func.now())

    empresa = relationship("Empresa")
    equipes = relationship("Equipe", secondary="usuarios_equipes", back_populates="usuarios")


class Equipe(Base):
    __tablename__ = "equipes"
    __table_args__ = (UniqueConstraint("empresa_id", "nome", name="uq_equipe_empresa_nome"),)

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    nome = Column(String(80), nullable=False)
    ativa = Column(Boolean, default=True)
    criado_em = Column(DateTime, server_default=func.now())

    empresa = relationship("Empresa")
    usuarios = relationship("UsuarioEmpresa", secondary="usuarios_equipes", back_populates="equipes")


class UsuarioEquipe(Base):
    __tablename__ = "usuarios_equipes"
    __table_args__ = (UniqueConstraint("usuario_id", "equipe_id", name="uq_usuario_equipe"),)

    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios_empresa.id"), nullable=False, index=True)
    equipe_id = Column(Integer, ForeignKey("equipes.id"), nullable=False, index=True)


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
    enderecos = relationship("EnderecoCliente", back_populates="cliente", cascade="all, delete-orphan")


class EnderecoCliente(Base):
    __tablename__ = "enderecos_clientes"
    __table_args__ = (
        UniqueConstraint(
            "empresa_id", "cliente_id", "endereco", "numero", "complemento", "bairro", "cidade", "estado", "cep",
            name="uq_endereco_cliente_completo"
        ),
    )

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    cliente_id = Column(Integer, ForeignKey("clientes.id"), nullable=False, index=True)
    apelido = Column(String(120))
    endereco = Column(String(200), nullable=False)
    numero = Column(String(30))
    complemento = Column(String(120))
    bairro = Column(String(120))
    cidade = Column(String(120))
    estado = Column(String(40))
    cep = Column(String(20))
    ativo = Column(Boolean, default=True)
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())

    cliente = relationship("Cliente", back_populates="enderecos")


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
    carga_pontos = Column(Integer, nullable=False, default=1)
    volume_logistico = Column(Integer, nullable=False, default=1)
    permite_interno = Column(Boolean, nullable=False, default=True)
    permite_mala = Column(Boolean, nullable=False, default=True)
    permite_teto = Column(Boolean, nullable=False, default=False)
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
    retirada_obrigatoria = Column(Boolean, default=False)
    retirada_data = Column(Date, nullable=True)
    retirada_hora = Column(Time, nullable=True)
    bairro = Column(String(120))
    # Endereço do EVENTO pertence ao contrato/reserva. ``local`` é o logradouro
    # legado e continua sendo usado para compatibilidade; os demais campos
    # congelam o destino daquele contrato para não depender do cadastro do cliente.
    local = Column(String(200))
    local_numero = Column(String(30), nullable=True)
    local_complemento = Column(String(120), nullable=True)
    local_cidade = Column(String(120), nullable=True)
    local_estado = Column(String(40), nullable=True)
    local_cep = Column(String(20), nullable=True)
    local_nome = Column(String(160))
    local_responsavel_nome = Column(String(160))
    local_responsavel_telefone = Column(String(40))
    retirada_responsavel_nome = Column(String(160))
    retirada_responsavel_telefone = Column(String(40))
    acesso_local = Column(String(40))
    valor = Column(Float, default=0)
    sinal = Column(Float, default=0)
    valor_pago = Column(Float, default=0)
    sinal_recebido = Column(Boolean, default=False)
    pagamento_confirmado_em = Column(DateTime, nullable=True)
    # Transferência operacional/financeira: o contrato continua pertencendo à empresa de origem,
    # mas pode ser marcado para execução/repasse a outra empresa.
    empresa_transferida_id = Column(Integer, ForeignKey("empresas.id"), nullable=True)
    valor_repasse = Column(Float, default=0)
    # Quando a empresa de destino também usa o Conect, o registro de destino
    # é uma cópia operacional vinculada ao contrato original.
    transferencia_origem_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=True, index=True)
    transferencia_copia_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=True, index=True)
    transferida_em = Column(DateTime, nullable=True)
    repasse_pago_em = Column(DateTime, nullable=True)
    repasse_pago_por = Column(String(120), nullable=True)
    observacoes = Column(Text)
    status = Column(String(30), default="pre_reserva")  # pre_reserva, aprovada, rejeitada, alteracao
    aceite_em = Column(DateTime, server_default=func.now())
    criado_em = Column(DateTime, server_default=func.now())

    cliente = relationship("Cliente", back_populates="solicitacoes")
    produto = relationship("ProdutoServico")
    contrato = relationship("Contrato")
    empresa_transferida = relationship("Empresa", foreign_keys=[empresa_transferida_id])
    itens = relationship("ReservaItem", back_populates="solicitacao", cascade="all, delete-orphan")
    aprovado_em = Column(DateTime, nullable=True)
    contrato_enviado_em = Column(DateTime, nullable=True)
    # Responsáveis de comunicação: contrato/comercial e operação/logística.
    responsavel_contrato = Column(String(120), nullable=True)
    responsavel_contrato_telefone = Column(String(30), nullable=True)
    responsavel_operacao = Column(String(120), nullable=True)
    cancelado_em = Column(DateTime, nullable=True)
    # Controle de cobrança Humiat: somente definido quando o contrato é aceito.
    humiat_processado = Column(Boolean, nullable=False, default=False)
    humiat_competencia = Column(String(7), nullable=True)  # AAAA-MM do aceite
    humiat_custo = Column(Integer, nullable=False, default=0)
    humiat_status = Column(String(30), nullable=True)  # gratuito, debitado, pendente_saldo
    # Coordenadas internas usadas somente pela Inteligência Logística.
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    status_geocodificacao = Column(String(20), nullable=True, default="pendente")
    data_geocodificacao = Column(DateTime, nullable=True)

    agenda = relationship("Agenda", back_populates="solicitacao", uselist=False)
    pagamentos = relationship("Pagamento", back_populates="solicitacao", cascade="all, delete-orphan")


class HumiatMovimento(Base):
    __tablename__ = "humiat_movimentos"

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    solicitacao_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=True, index=True)
    tipo = Column(String(30), nullable=False)  # credito, consumo_contrato, ajuste, estorno
    quantidade = Column(Integer, nullable=False)  # positivo=entrada, negativo=saída
    saldo_anterior = Column(Integer, nullable=False, default=0)
    saldo_posterior = Column(Integer, nullable=False, default=0)
    motivo = Column(String(200), nullable=True)
    observacao = Column(Text, nullable=True)
    usuario = Column(String(120), nullable=True)
    criado_em = Column(DateTime, server_default=func.now(), nullable=False)

    empresa = relationship("Empresa")
    solicitacao = relationship("Solicitacao")


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


class InfinitePayTaxa(Base):
    __tablename__ = "infinitepay_taxas"
    __table_args__ = (UniqueConstraint("empresa_id", "parcelas", name="uq_infinitepay_taxa_empresa_parcelas"),)

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    parcelas = Column(Integer, nullable=False)
    taxa_percentual = Column(Float, nullable=False, default=0)
    ativa = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime, server_default=func.now())


class InfinitePayCobranca(Base):
    __tablename__ = "infinitepay_cobrancas"

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    solicitacao_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=False, index=True)
    pagamento_id = Column(Integer, ForeignKey("pagamentos.id"), nullable=True, index=True)
    order_nsu = Column(String(120), nullable=False, unique=True, index=True)
    tipo_pagamento = Column(String(20), nullable=False)  # sinal | integral | restante
    valor_centavos = Column(Integer, nullable=False, default=0)
    status = Column(String(30), nullable=False, default="AGUARDANDO_PAGAMENTO")
    checkout_url = Column(Text, nullable=True)
    transaction_nsu = Column(String(180), nullable=True, unique=True, index=True)
    invoice_slug = Column(String(180), nullable=True)
    receipt_url = Column(Text, nullable=True)
    capture_method = Column(String(40), nullable=True)
    installments = Column(Integer, nullable=False, default=0)
    paid_amount_centavos = Column(Integer, nullable=False, default=0)
    pago_em = Column(DateTime, nullable=True)
    criado_em = Column(DateTime, server_default=func.now())
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())


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
    equipe_id = Column(Integer, ForeignKey("equipes.id"), nullable=True, index=True)
    roteirizado = Column(Boolean, default=False)
    previsao_entrega = Column(String(5))
    link_localizacao = Column(Text)
    tipo_evento = Column(String(20), default="entrega")  # entrega ou retirada
    status_operacional = Column(String(20), default="pendente")  # pendente ou concluido
    observacoes_operacionais = Column(Text, nullable=True)

    solicitacao = relationship("Solicitacao", back_populates="agenda")
    equipe = relationship("Equipe")


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
    organiza_lancamento_id = Column(Integer, ForeignKey("lancamentos_organiza.id"), nullable=True)
    repasse_solicitacao_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=True)
    hash_importacao = Column(String(64), nullable=True, index=True)
    origem_importacao = Column(String(120), nullable=True)
    ordem = Column(Integer, default=0, index=True)
    criado_em = Column(DateTime, server_default=func.now())

    conta = relationship("ContaFinanceira")
    pagamento = relationship("Pagamento")
    organiza_lancamento = relationship("LancamentoOrganiza", foreign_keys=[organiza_lancamento_id])
    repasse_solicitacao = relationship("Solicitacao", foreign_keys=[repasse_solicitacao_id])
    vinculos_repasse = relationship(
        "VinculoRepasseBanco",
        back_populates="lancamento",
        cascade="all, delete-orphan",
    )



class VinculoRepasseBanco(Base):
    """Rateio de um lançamento bancário entre um ou mais repasses de contratos."""
    __tablename__ = "vinculos_repasse_banco"
    __table_args__ = (
        UniqueConstraint("lancamento_banco_id", "solicitacao_id", name="uq_vinculo_repasse_banco"),
    )

    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    lancamento_banco_id = Column(Integer, ForeignKey("lancamentos_banco.id"), nullable=False, index=True)
    solicitacao_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=False, index=True)
    valor = Column(Float, default=0)
    criado_em = Column(DateTime, server_default=func.now())
    criado_por = Column(String(120), nullable=True)

    lancamento = relationship("LancamentoBanco", back_populates="vinculos_repasse")
    solicitacao = relationship("Solicitacao")


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
    organiza_lancamento_id = Column(Integer, ForeignKey("lancamentos_organiza.id"), nullable=True, index=True)
    repasse_solicitacao_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=True)
    ordem = Column(Integer, default=0, index=True)
    criado_em = Column(DateTime, server_default=func.now())

    conta = relationship("ContaFinanceira")
    pagamento = relationship("Pagamento")
    organiza_lancamento = relationship("LancamentoOrganiza", foreign_keys=[organiza_lancamento_id])
    repasse_solicitacao = relationship("Solicitacao", foreign_keys=[repasse_solicitacao_id])


class LancamentoOrganiza(Base):
    """Lançamento financeiro recebido do sistema Organiza."""
    __tablename__ = "lancamentos_organiza"

    id = Column(Integer, primary_key=True, index=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=True, index=True)
    id_externo = Column(String(120), unique=True, nullable=False, index=True)
    tipo = Column(String(30), nullable=False)  # venda | manutencao
    cliente = Column(String(255), nullable=True)
    descricao = Column(String(500), nullable=True)
    valor = Column(Numeric(12, 2), nullable=False, default=0)
    falta_receber = Column(Numeric(12, 2), nullable=False, default=0)
    data_pagamento = Column(Date, nullable=False)
    banco = Column(String(255), nullable=False)
    criado_em = Column(DateTime, server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)

class VeiculoLogistico(Base):
    __tablename__ = "veiculos_logisticos"
    __table_args__ = (UniqueConstraint("empresa_id", "nome", name="uq_veiculo_logistico_nome"),)
    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    capacidade_pontos = Column(Integer, nullable=True)
    capacidade_interno = Column(Integer, nullable=False, default=4)
    capacidade_mala = Column(Integer, nullable=False, default=1)
    capacidade_teto = Column(Integer, nullable=False, default=3)
    ativo = Column(Boolean, nullable=False, default=True)
    criado_em = Column(DateTime, server_default=func.now(), nullable=False)
    perfis_carga = relationship("VeiculoPerfilCarga", back_populates="veiculo", cascade="all, delete-orphan")

class VeiculoPerfilCarga(Base):
    __tablename__ = "veiculos_perfis_carga"
    __table_args__ = (UniqueConstraint("veiculo_id", "produto_id", name="uq_veiculo_produto_carga"),)
    id = Column(Integer, primary_key=True)
    veiculo_id = Column(Integer, ForeignKey("veiculos_logisticos.id", ondelete="CASCADE"), nullable=False, index=True)
    produto_id = Column(Integer, ForeignKey("produtos_servicos.id", ondelete="CASCADE"), nullable=False, index=True)
    volumes = Column(Integer, nullable=False, default=1)
    permite_interno = Column(Boolean, nullable=False, default=True)
    permite_mala = Column(Boolean, nullable=False, default=False)
    permite_teto = Column(Boolean, nullable=False, default=False)  # teto / outros suportes externos
    ativo = Column(Boolean, nullable=False, default=True)
    veiculo = relationship("VeiculoLogistico", back_populates="perfis_carga")
    produto = relationship("ProdutoServico")


class ConfiguracaoRotaInteligente(Base):
    __tablename__ = "configuracoes_rota_inteligente"
    __table_args__ = (UniqueConstraint("empresa_id", name="uq_config_rota_empresa"),)
    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    endereco_loja = Column(String(300), nullable=True)
    latitude_loja = Column(Float, nullable=True)
    longitude_loja = Column(Float, nullable=True)
    minutos_montagem = Column(Integer, nullable=False, default=30)
    minutos_desmontagem = Column(Integer, nullable=False, default=20)
    antecedencia_entrega = Column(Integer, nullable=False, default=60)
    horario_minimo_cliente = Column(Time, nullable=False, default=time(8, 0))
    raio_retirada_estrategica_km = Column(Float, nullable=False, default=10)
    desvio_max_retirada_estrategica_min = Column(Integer, nullable=False, default=60)
    minutos_parada_loja = Column(Integer, nullable=False, default=20)
    velocidade_media_kmh = Column(Float, nullable=False, default=30)
    custo_km = Column(Float, nullable=False, default=0)
    custo_hora_equipe = Column(Float, nullable=False, default=0)
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())

class RotaInteligente(Base):
    __tablename__ = "rotas_inteligentes"
    __table_args__ = (
        UniqueConstraint("empresa_id", "chave_consumo", name="uq_rota_chave_consumo"),
    )
    id = Column(Integer, primary_key=True)
    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    equipe_id = Column(Integer, ForeignKey("equipes.id"), nullable=True, index=True)
    veiculo_id = Column(Integer, ForeignKey("veiculos_logisticos.id"), nullable=True, index=True)
    codigo = Column(String(40), nullable=False, unique=True, index=True)
    chave_consumo = Column(String(120), nullable=False)
    data_operacao = Column(Date, nullable=False, index=True)
    horario_saida = Column(Time, nullable=False)
    status = Column(String(30), nullable=False, default="planejada")
    humiat_consumido = Column(Boolean, nullable=False, default=False)
    custo_humiat = Column(Integer, nullable=False, default=1)
    distancia_total_km = Column(Float, nullable=False, default=0)
    duracao_total_min = Column(Integer, nullable=False, default=0)
    retornos_loja = Column(Integer, nullable=False, default=0)
    carga_maxima_pontos = Column(Integer, nullable=False, default=0)
    custo_estimado = Column(Float, nullable=False, default=0)
    versao_calculo = Column(Integer, nullable=False, default=1)
    criado_por = Column(String(120), nullable=True)
    criado_em = Column(DateTime, server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())
    equipe = relationship("Equipe")
    veiculo = relationship("VeiculoLogistico")
    paradas = relationship("RotaInteligenteParada", back_populates="rota", cascade="all, delete-orphan", order_by="RotaInteligenteParada.ordem")

class RotaInteligenteParada(Base):
    __tablename__ = "rotas_inteligentes_paradas"
    id = Column(Integer, primary_key=True)
    rota_id = Column(Integer, ForeignKey("rotas_inteligentes.id"), nullable=False, index=True)
    agenda_id = Column(Integer, ForeignKey("agenda.id"), nullable=True, index=True)
    solicitacao_id = Column(Integer, ForeignKey("solicitacoes.id"), nullable=True, index=True)
    ordem = Column(Integer, nullable=False)
    tipo = Column(String(20), nullable=False)  # loja, entrega, retirada
    titulo = Column(String(180), nullable=False)
    endereco = Column(String(300), nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    horario_limite = Column(Time, nullable=True)
    chegada_prevista = Column(DateTime, nullable=True)
    saida_prevista = Column(DateTime, nullable=True)
    chegada_real = Column(DateTime, nullable=True)
    distancia_anterior_km = Column(Float, nullable=False, default=0)
    deslocamento_anterior_min = Column(Integer, nullable=False, default=0)
    servico_min = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="pendente")
    risco = Column(String(20), nullable=False, default="normal")
    motivo_prioridade = Column(Text, nullable=True)
    fixada = Column(Boolean, nullable=False, default=False)
    retorno_loja = Column(Boolean, nullable=False, default=False)
    carga_movimento = Column(Integer, nullable=False, default=0)
    carga_apos_parada = Column(Integer, nullable=False, default=0)
    criado_em = Column(DateTime, server_default=func.now(), nullable=False)
    rota = relationship("RotaInteligente", back_populates="paradas")
    agenda = relationship("Agenda")
    solicitacao = relationship("Solicitacao")
