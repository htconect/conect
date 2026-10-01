# Connect 1.0.85

- SSO Humiat v2 assinado por HMAC e validado localmente no Connect.
- Remove a chamada HTTP ao Humiat no caminho normal de login.
- Mantém fallback para tickets antigos.
- Reaproveita sessão local quando o usuário já está conectado ao mesmo destino.
- Adiciona medição das etapas `sso.humiat_validar` e `sso.localizar_usuario`.
- Reduz timeout do fallback legado para 5 segundos.
