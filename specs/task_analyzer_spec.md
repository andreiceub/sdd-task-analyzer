# Especificação SDD — TaskAnalyzer

**Versão 1.1** · Transposta da especificação da Fase 1 (Google Docs) e ajustada ao enunciado da Fase 2.
**Autor:** Andrei Barone Romaskevis · Ciência da Computação — CEUB · Bootcamp III, turma A · andrei.barone@sempreceub.com
**Versão anterior:** [Especificação SDD TaskAnalyzer v1.0 (Google Docs)](https://docs.google.com/document/d/1UShTgmNH7D07mt4KzTqrDS1DUCqOr44yccvYN0fY8Jo/edit?usp=sharing)

Este arquivo é a fonte de verdade do projeto. O código em `src/` e os testes em `tests/` derivam dele; em caso de divergência, quem está errado é o código.

---

## Histórico de versões

| Versão | O que mudou | Por quê |
|---|---|---|
| 1.0 | Especificação original (Fase 1). | — |
| 1.1 | Função pública renomeada de `analisar_tarefas` para `analyze_tasks`. | O enunciado da Fase 2 exige esse nome. |
| 1.1 | Exceção base renomeada de `TaskAnalyzerError` para `TaskValidationError`. | O enunciado da Fase 2 exige esse nome. As subclasses da v1.0 foram mantidas. |
| 1.1 | Tempo médio passa de dias para **horas** (`tempo_medio_conclusao_horas`), e o SLA da RN08 vai junto: 2/5/10 dias viram 48/120/240 horas. | O enunciado da Fase 2 define as métricas em horas. Os valores da massa de referência são os mesmos, só convertidos. |
| 1.1 | Saída ganha `total_pendentes` e `total_canceladas`. | O enunciado pede `total_pendentes`; `total_canceladas` fecha a soma dos totais. |
| 1.1 | Entrada passa a ser uma lista de **dicionários** (registros brutos), validados e convertidos internamente em `Tarefa`. | Com objetos já tipados, várias regras de validação nunca poderiam falhar. Dicionário é também o formato usado em sala. |
| 1.1 | Nova exceção `ConfiguracaoInvalidaError`, para coleção que não é lista e SLA inválido. | A v1.0 não previa erro para parâmetros da chamada, e a base não pode ser lançada diretamente. |
| 1.1 | Datas com fuso horário são normalizadas para UTC. | Comparar data com fuso e data sem fuso lança `TypeError` em Python; achado na homologação. |

---

## 1. Visão geral e contrato de negócio

### 1.1 Propósito

O TaskAnalyzer recebe uma coleção de tarefas e devolve métricas de produtividade. Não tem interface, não persiste dados e não acessa rede: é uma transformação determinística, cuja saída depende só da entrada. Por isso todo o comportamento pode ser descrito aqui antes do código e verificado por teste automatizado.

### 1.2 Assinatura pública

```python
def analyze_tasks(
    tarefas: Sequence[Mapping[str, Any]],
    sla_por_prioridade: Mapping[Prioridade, float] | None = None,
) -> RelatorioProdutividade: ...
```

Nenhuma implementação, gerada por IA ou humana, pode alterar esta assinatura sem uma nova versão deste documento.

### 1.3 Entradas

Cada item da lista é um dicionário com os campos abaixo. Campos fora desta tabela são ignorados.

| Campo | Tipo aceito | Obrig. | Regra de validação |
|---|---|---|---|
| `id_tarefa` | `int` | Sim | Inteiro positivo e único na coleção. `bool` é rejeitado. |
| `titulo` | `str` | Sim | Não vazio após remover espaços; até 200 caracteres. |
| `prioridade` | `str` ou `Prioridade` | Sim | Domínio fechado: `ALTA`, `MEDIA`, `BAIXA`. Maiúsculas exatas. |
| `status` | `str` ou `Status` | Sim | Domínio fechado: `PENDENTE`, `EM_ANDAMENTO`, `CONCLUIDA`, `CANCELADA`. |
| `data_criacao` | ISO 8601, `date` ou `datetime` | Sim | Data válida. |
| `data_inicio` | idem | Não | Se informada, ≥ `data_criacao`. |
| `data_conclusao` | idem | Cond. | Obrigatória se `status = CONCLUIDA`; ≥ `data_inicio` (ou ≥ `data_criacao` sem início). |

Uma `date` sem hora é tratada como meia-noite. Texto vazio em data opcional equivale a não informar.

### 1.4 Saídas

| Chave | Tipo | Definição |
|---|---|---|
| `total_tarefas` | `int` | Tarefas recebidas. |
| `total_concluidas` | `int` | Tarefas com status `CONCLUIDA`. |
| `total_pendentes` | `int` | Tarefas `PENDENTE` ou `EM_ANDAMENTO`. |
| `total_canceladas` | `int` | Tarefas `CANCELADA`. |
| `percentual_conclusao` | `float` | `total_concluidas ÷ total_tarefas × 100` |
| `tempo_medio_conclusao_horas` | `float` | Média de `data_conclusao − data_criacao`, em horas, só das concluídas. |
| `taxa_atraso_percentual` | `float` | Concluídas fora do SLA `÷ total_concluidas × 100` |
| `metricas_por_prioridade` | `dict` | Para `ALTA`, `MEDIA` e `BAIXA`: `total`, `concluidas`, `tempo_medio_conclusao_horas`, `taxa_atraso_percentual`. |

Todo `float` sai arredondado em duas casas. As três prioridades sempre aparecem, zeradas quando não houver tarefa.

### 1.5 Restrições de negócio

| ID | Restrição |
|---|---|
| RN01 | Só tarefas `CONCLUIDA` entram no tempo médio e na taxa de atraso. As demais contam apenas nos totais. |
| RN02 | `data_criacao ≤ data_inicio ≤ data_conclusao`. |
| RN03 | Nenhuma divisão por zero. Denominador zero devolve `0.0`. |
| RN04 | Lista vazia é entrada válida e devolve a estrutura completa zerada. |
| RN05 | Prioridade ou status fora do domínio interrompem com exceção específica. |
| RN06 | Tarefa `CONCLUIDA` sem `data_conclusao` interrompe com exceção específica. |
| RN07 | `id_tarefa` repetido na coleção interrompe com exceção específica. |
| RN08 | Atraso é apurado contra o SLA da prioridade, em horas corridas: ALTA 48, MEDIA 120, BAIXA 240. Parametrizável por `sla_por_prioridade`. Concluir exatamente no limite **não** é atraso. |
| RN09 | A coleção inteira é validada antes de qualquer cálculo; um registro inválido invalida a análise toda. |
| RN10 | Arredondamento em duas casas só na montagem do relatório, nunca nos cálculos intermediários. |
| RN11 | Datas com fuso são convertidas para UTC e perdem o fuso; datas sem fuso são tratadas como UTC. |

### 1.6 Exceções

Todas herdam de `TaskValidationError` (que herda de `ValueError`). A base nunca é lançada diretamente. Toda mensagem identifica a tarefa e o campo.

| Exceção | Quando |
|---|---|
| `CampoObrigatorioError` | Campo ausente, vazio ou com tipo inválido; registro que não é dicionário; concluída sem data de conclusão. |
| `DataInvalidaError` | Data fora do ISO 8601, tipo não suportado, ou cronologia quebrada. |
| `PrioridadeInvalidaError` | Prioridade fora de ALTA / MEDIA / BAIXA. |
| `StatusInvalidoError` | Status fora do domínio. |
| `IdDuplicadoError` | `id_tarefa` repetido. |
| `ConfiguracaoInvalidaError` | Coleção que não é lista/tupla, ou SLA com chave ou prazo inválido. |

---

## 2. Cenários de aceite e Test Harness

### 2.1 Cenário 1 — sucesso

**CA01 — Cálculo com coleção válida**
- **Dado** a massa de referência da seção 2.4 (seis tarefas: quatro concluídas, uma em andamento, uma pendente);
- **Quando** `analyze_tasks` for executada;
- **Então** o relatório traz 6 tarefas, 4 concluídas, 2 pendentes, 66,67% de conclusão, tempo médio de 162,0 h e 50,0% de atraso;
- **E** os indicadores por prioridade batem com a tabela da seção 2.4;
- **E** tarefas não concluídas não alteram tempo médio nem atraso.

### 2.2 Cenário 2 — exceção

**CA02 — Data de conclusão anterior à criação**
- **Dado** uma tarefa criada em 2026-03-10 e concluída em 2026-03-05;
- **Quando** `analyze_tasks` for executada;
- **Então** é lançada `DataInvalidaError` (uma `TaskValidationError`) identificando a tarefa e o campo `data_conclusao`;
- **E** nenhuma métrica é devolvida.

### 2.3 Casos de borda e complementares

| ID | Cenário | Resultado esperado |
|---|---|---|
| CA03 | Coleção vazia. | Estrutura completa zerada, sem `ZeroDivisionError`. |
| CA04 | Apenas tarefas pendentes ou em andamento. | Totais preenchidos; médias `0.0`, sem exceção. |
| CA05 | Prioridade sem nenhuma tarefa. | Prioridade presente no resultado, zerada. |
| CA06 | Prioridade `URGENTE` ou status `FEITA`. | `PrioridadeInvalidaError` / `StatusInvalidoError`. |
| CA07 | `CONCLUIDA` sem `data_conclusao`. | `CampoObrigatorioError`. |
| CA08 | ALTA concluída em exatamente 48 h. | Não é atraso. Com 48 h e 1 min, é. |
| CA09 | Dois registros com o mesmo id. | `IdDuplicadoError`. |
| CA10 | `CANCELADA` com data de conclusão. | Conta só no total; fora das médias. |

### 2.4 Massa de referência

Dados sintéticos, sem informação pessoal (ano 2026).

| ID | Título | Prior. | Criação | Início | Conclusão | Status | Horas | Atraso |
|---|---|---|---|---|---|---|---|---|
| 1 | Corrigir bug de login | ALTA | 01/03 | 01/03 | 02/03 | CONCLUIDA | 24 | Não |
| 2 | Atualizar documentação | BAIXA | 01/03 | 03/03 | 15/03 | CONCLUIDA | 336 | Sim |
| 3 | Refatorar relatórios | MEDIA | 02/03 | 04/03 | 10/03 | CONCLUIDA | 192 | Sim |
| 4 | Implementar filtro | MEDIA | 05/03 | 06/03 | 09/03 | CONCLUIDA | 96 | Não |
| 5 | Migrar banco de dados | ALTA | 06/03 | 07/03 | — | EM_ANDAMENTO | — | — |
| 6 | Revisar contrato de API | BAIXA | 07/03 | — | — | PENDENTE | — | — |

| Prioridade | Total | Concluídas | Tempo médio (h) | Atraso |
|---|---|---|---|---|
| ALTA | 2 | 1 | 24,00 | 0,00% |
| MEDIA | 2 | 2 | 144,00 | 50,00% |
| BAIXA | 2 | 1 | 336,00 | 100,00% |
| **Geral** | **6** | **4** | **162,00** | **50,00%** |

Na v1.0 o tempo médio geral era 6,75 dias; 6,75 × 24 = 162 horas.

### 2.5 Rastreabilidade cenário → teste

Os testes ficam em `tests/test_harness.py`, com a massa em `tests/conftest.py`. O "Dado" vira fixture, o "Quando" vira a chamada e o "Então" vira asserção.

| Cenário | Teste(s) |
|---|---|
| CA01 | `test_ca01_calcula_metricas_com_dados_validos`, `test_ca01_tarefas_nao_concluidas_nao_alteram_tempo_nem_atraso` |
| CA02 | `test_ca02_lanca_erro_para_conclusao_anterior_a_criacao` e mais quatro variações de data |
| CA03 | `test_ca03_colecao_vazia_retorna_metricas_zeradas` |
| CA04 | `test_ca04_apenas_tarefas_pendentes_nao_divide_por_zero` |
| CA05 | `test_ca05_prioridade_sem_tarefas_aparece_zerada` |
| CA06 | `test_ca06_lanca_erro_para_prioridade_invalida`, `test_ca06_lanca_erro_para_status_invalido` |
| CA07 | `test_ca07_lanca_erro_para_concluida_sem_data_de_conclusao` |
| CA08 | `test_ca08_conclusao_no_limite_do_sla_nao_e_atraso`, `test_ca08_um_minuto_apos_o_sla_ja_e_atraso` |
| CA09 | `test_ca09_lanca_erro_para_id_duplicado` |
| CA10 | `test_ca10_tarefa_cancelada_e_ignorada_nas_metricas` |

Meta: 100% dos cenários aprovados e cobertura de linhas ≥ 90%.

---

## 3. Arquitetura do repositório

```
sdd-task-analyzer/
├── README.md
├── CONTEXT_RULES.md
├── .gitignore
├── requirements.txt
├── specs/
│   └── task_analyzer_spec.md
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_harness.py
└── src/
    ├── __init__.py
    ├── models.py
    ├── exceptions.py
    ├── validators.py
    └── task_analyzer.py
```

## 4. Plano de homologação humana

Nenhum código gerado por IA entra na `main` sem passar pelas cinco etapas:

1. Execução completa dos testes automatizados (`pytest -v`), sem falha nem teste ignorado.
2. Revisão de conformidade com este contrato e com o `CONTEXT_RULES.md`.
3. Análise de qualidade: legibilidade, tratamento de erros, aderência a PEP 8 e docstrings.
4. Testes manuais complementares em casos de borda.
5. Merge somente após aprovação, via Pull Request.
