# Correção da geocodificação automática

- Remove repetição de bairro, cidade e estado na consulta.
- Usa os campos reais do contrato para gerar variações de endereço.
- Tenta endereço completo, sem complemento, CEP com número e forma simplificada.
- Usa Nominatim como provedor principal e Photon como alternativa.
- Registra no Render cada tentativa, provedor, consulta e erro HTTP/rede.
- Mantém o contrato salvo mesmo quando a geocodificação falhar.
- Iniciar rota tenta calcular; se falhar, abre pelo endereço textual.
- A Inteligência calcula e salva coordenadas ausentes antes de montar a rota.
