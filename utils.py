import re
from datetime import datetime, timedelta

def limpar_identificador(valor: str) -> str:
    return re.sub(r"\D+", "", valor or "")

def texto_para_float(valor: str) -> float:
    """
    Converte valores digitados no padrão brasileiro ou técnico sem multiplicar zeros.
    Exemplos aceitos:
    - 310000.00 -> 310000.00
    - 310.000,00 -> 310000.00
    - 310000,00 -> 310000.00
    - R$ 310.000,00 -> 310000.00
    """
    if valor is None:
        return 0.0

    texto = str(valor).strip()
    if not texto:
        return 0.0

    texto = re.sub(r"[^0-9,.-]", "", texto)

    if "," in texto and "." in texto:
        # O separador decimal é o último símbolo encontrado.
        if texto.rfind(",") > texto.rfind("."):
            texto = texto.replace(".", "").replace(",", ".")
        else:
            texto = texto.replace(",", "")
    elif "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    elif "." in texto:
        partes = texto.split(".")
        # Quando existem vários pontos, são separadores de milhar.
        if len(partes) > 2:
            texto = "".join(partes[:-1]) + "." + partes[-1]
        # Com um único ponto e duas casas, mantém como decimal.
        # Com três casas após o ponto, trata como milhar: 310.000 -> 310000.
        elif len(partes[-1]) == 3 and len(partes[0]) <= 3:
            texto = "".join(partes)

    try:
        return float(texto)
    except ValueError:
        return 0.0

def somar_horas(hora, horas: int):
    if not hora or not horas:
        return None
    base = datetime.combine(datetime.today(), hora)
    return (base + timedelta(hours=horas)).time()

def somar_minutos(hora, minutos: int):
    if not hora or not minutos:
        return None
    base = datetime.combine(datetime.today(), hora)
    return (base + timedelta(minutes=int(minutos))).time()

def hora_meia_em_meia_valida(hora_str: str) -> bool:
    try:
        hora = datetime.strptime(hora_str, "%H:%M").time()
        return hora.minute in (0, 30)
    except Exception:
        return False


def cpf_valido(cpf: str) -> bool:
    cpf = limpar_identificador(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
    digito1 = (soma * 10) % 11
    digito1 = 0 if digito1 == 10 else digito1
    soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
    digito2 = (soma * 10) % 11
    digito2 = 0 if digito2 == 10 else digito2
    return digito1 == int(cpf[9]) and digito2 == int(cpf[10])


def cnpj_valido(cnpj: str) -> bool:
    cnpj = limpar_identificador(cnpj)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    pesos2 = [6] + pesos1
    soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
    resto = soma % 11
    digito1 = 0 if resto < 2 else 11 - resto
    soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
    resto = soma % 11
    digito2 = 0 if resto < 2 else 11 - resto
    return digito1 == int(cnpj[12]) and digito2 == int(cnpj[13])


def aplicar_variaveis_mensagem(texto: str, **dados) -> str:
    texto = texto or ""
    for chave, valor in dados.items():
        texto = texto.replace("{{" + chave + "}}", str(valor or ""))
    return texto
