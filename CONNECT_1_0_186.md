# Conect 1.0.186

Quando o frete fica sob consulta, abre um campo para digitar o valor.
Orientação: Favor solicitar o valor do frete ao locador.
O valor informado deve ser maior que zero, validado na tela e no servidor.
O valor é somado uma única vez ao pedido e segue para o cadastro.
Alterar CEP ou número apaga o valor manual anterior.

Aplicação: substituir app.py, config.py e templates/publico/vitrine.html.
O pacote contém o sistema completo. Não exige migração de banco.

Validação: sintaxe Python e JavaScript; valores positivos, zero, negativos,
não finitos e formato monetário brasileiro. A suíte pytest não foi executada
porque pytest não está instalado neste ambiente.
