# Conect 1.0.215 — navegação e carregamento global

## Causa
O `templates/base.html` acionava o bloqueio visual para **todo** clique em um link interno. Vários links internos respondem `303` direcionando para aplicativos externos (`wa.me`, InfinitePay, etc.). Ao abrir WhatsApp no iOS, o navegador nem sempre descarrega a página original e o bloqueio `Abrindo tela` continuava ativo.

## Correção
- Links voltam a navegar normalmente, sem overlay genérico (inclusive em redirecionamentos externos).
- Submissões reais de formulários mantêm a sinalização de processamento, mas fecham o overlay no retorno por foco/visibilidade e após 15 s de segurança.
- Formulários que abrem em outra aba não bloqueiam a aba corrente.
- O catálogo público usa a mesma proteção de retorno do iPhone.
- O botão de compartilhar da vitrine deixa de abrir uma aba provisória `about:blank`; primeiro obtém o link, depois navega diretamente para o WhatsApp.
- Nenhuma regra financeira, aceite, cobrança ou conteúdo de mensagem foi alterada nesta versão.

## Operação
A versão 1.0.215 substitui a 1.0.214 e inclui todas as correções anteriores. O PATCH incremental só deve ser aplicado sobre a 1.0.214 exata; o ZIP completo pode ser usado quando a base local divergir.

## Validação manual após deploy
1. No iPhone, clique Enviar aceite e Enviar contrato no painel. Confirme que o WhatsApp abre e a tela do Conect continua utilizável ao voltar.
2. Abra o catálogo de opcionais via WhatsApp e retorne, sem overlay.
3. Aceite um contrato de teste, confira redirecionamento e retorno à tela.
4. Envie um formulário normal (por exemplo, salvar opcionais) para verificar indicador e conclusão.
5. Compartilhe a vitrine; confira que não há página `about:blank`.
