# CONTEXT_RULES — Regras persistentes de contexto para a IA

Este arquivo é entregue ao assistente de IA no início de **toda** sessão de trabalho, junto com `specs/task_analyzer_spec.md`. Ele existe porque o modelo não guarda o que foi combinado entre sessões e, numa conversa longa, vai deixando instruções antigas para trás. Com as regras num arquivo versionado, toda resposta gerada pode ser conferida contra um padrão definido antes da geração.

A especificação diz **o que** o sistema faz. Este arquivo diz **como** o código pode ser produzido.

---

## 1. Diretrizes obrigatórias

| Categoria | Regra |
|---|---|
| Linguagem | Python 3.12 ou superior. O código não usa recurso exclusivo do 3.12, então também roda no 3.11 exigido pelo enunciado. |
| Bibliotecas | Biblioteca padrão. pandas e numpy são autorizados pelo docente, mas este módulo não precisa deles. Testes: `pytest` e `pytest-cov`. |
| Tipagem | Type hints em 100% das funções, parâmetros e retornos. O código passa em `mypy --strict`. |
| Estilo | PEP 8, linhas de até 88 colunas, nomes descritivos sem abreviação obscura. |
| Responsabilidade única | Um módulo por responsabilidade: `models` (forma dos dados), `exceptions` (erros), `validators` (validação), `task_analyzer` (cálculo e API pública). |
| Funções | Pequenas, puras e com um único propósito. Sem estado global mutável. |
| Documentação | Docstring no padrão Google em todo módulo, classe e função, com `Args`, `Returns` e `Raises`. |
| Erros | Apenas as exceções da seção 1.6 da especificação, todas herdando de `TaskValidationError`. Mensagens identificam tarefa e campo. |
| Observabilidade | Módulo `logging`: `INFO` no início e no fim da análise, `ERROR` quando a entrada é rejeitada. |
| Nomenclatura | Termos de domínio em português (tarefa, prioridade, atraso). A API pública segue o nome exigido pelo enunciado: `analyze_tasks` e `TaskValidationError`. |

## 2. Proibições explícitas

1. Não usar biblioteca externa não autorizada. Na dúvida, perguntar ao docente antes.
2. Não alterar, flexibilizar ou apagar cenários de aceite e testes para o código passar.
3. Não modificar a assinatura, o nome ou os parâmetros de `analyze_tasks`.
4. Não modificar a estrutura de pastas definida na especificação.
5. Não persistir dados em arquivo, banco ou cache, e não acessar a rede.
6. Não devolver estrutura de saída diferente da seção 1.4 da especificação.
7. Não assumir comportamento que o contrato não descreve. Na dúvida, perguntar antes de gerar.
8. Não gerar funcionalidade nova sem o teste correspondente.
9. Não usar `print()` nem `input()` no módulo.
10. Não gerar código duplicado, morto ou não solicitado.
11. Não usar `except:` genérico nem silenciar exceções.
12. Não incluir dado real, pessoal ou sensível em exemplos, testes ou prompts.

## 3. Regras de interação com a IA

1. Sempre fornecer a especificação e este arquivo antes de pedir código.
2. Pedir que a IA resuma o contrato com as próprias palavras antes de gerar, para confirmar o entendimento.
3. Gerar em etapas pequenas: modelos e exceções, depois validação, depois cálculo, depois testes.
4. Ler criticamente todo trecho gerado. Nada entra no repositório sem revisão humana.
5. Rejeitar e refazer o pedido sempre que a resposta violar uma proibição da seção 2.
6. Quando a especificação e o enunciado divergirem, registrar a decisão numa nova versão da especificação antes de mudar o código.
7. Commits com código gerado por IA identificam a origem na mensagem.
