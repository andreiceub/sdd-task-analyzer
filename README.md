# sdd-task-analyzer

Módulo **TaskAnalyzer**, desenvolvido com **Spec-Driven Development (SDD)** e geração de código assistida por IA no Bootcamp III (CEUB).

Recebe uma lista de tarefas e devolve métricas de produtividade: totais, tempo médio de conclusão em horas, taxa de atraso e os mesmos indicadores separados por prioridade.

## Status do build

| Verificação | Resultado |
|---|---|
| `pytest -v` | 68 testes, 100% aprovados |
| Cobertura (`pytest --cov=src`) | 100% das linhas de `src/` |
| Tipagem (`mypy --strict`) | Sem erros |
| Integração contínua | GitHub Actions entra na Fase 3 |

## Como executar

Requer Python 3.11 ou superior (o projeto foi validado no 3.12+).

```bash
git clone https://github.com/<seu-usuario>/sdd-task-analyzer.git
cd sdd-task-analyzer
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows:     .venv\Scripts\activate
pip install -r requirements.txt
pytest -v
```

Para ver a cobertura:

```bash
pytest -v --cov=src --cov-report=term-missing
```

No Google Colab, rode numa célula:

```python
!git clone https://github.com/<seu-usuario>/sdd-task-analyzer.git
%cd sdd-task-analyzer
!pip install -q -r requirements.txt
!pytest -v
```

## Exemplo de uso

```python
from src.task_analyzer import TaskValidationError, analyze_tasks

tarefas = [
    {
        "id_tarefa": 1,
        "titulo": "Corrigir bug de login",
        "prioridade": "ALTA",
        "status": "CONCLUIDA",
        "data_criacao": "2026-03-01T08:00:00",
        "data_conclusao": "2026-03-01T12:00:00",
    },
    {
        "id_tarefa": 2,
        "titulo": "Revisar contrato de API",
        "prioridade": "BAIXA",
        "status": "PENDENTE",
        "data_criacao": "2026-03-02T09:00:00",
    },
]

try:
    relatorio = analyze_tasks(tarefas)
except TaskValidationError as erro:
    print(f"Entrada inválida: {erro}")
else:
    print(relatorio["tempo_medio_conclusao_horas"])  # 4.0
    print(relatorio["taxa_atraso_percentual"])       # 0.0
```

## Estrutura

```
sdd-task-analyzer/
├── README.md               # este arquivo
├── CONTEXT_RULES.md        # regras de governança entregues à IA
├── .gitignore
├── requirements.txt        # pytest e pytest-cov
├── specs/
│   └── task_analyzer_spec.md   # contrato SDD v1.1 — fonte de verdade
├── tests/
│   ├── conftest.py         # massa de referência (dados sintéticos)
│   └── test_harness.py     # Test Harness: cenários CA01 a CA10
└── src/
    ├── models.py           # Prioridade, Status, Tarefa, relatório tipado
    ├── exceptions.py       # TaskValidationError e subclasses
    ├── validators.py       # validação estrita da entrada
    └── task_analyzer.py    # analyze_tasks
```

## Fluxo de trabalho

1. **Especificar** — o contrato em `specs/` define entradas, saídas, regras e cenários de aceite.
2. **Escrever o harness** — os testes em `tests/` traduzem os cenários antes do código existir.
3. **Gerar com IA** — o assistente recebe a especificação e o `CONTEXT_RULES.md` e gera o código em etapas.
4. **Homologar** — revisão humana em cinco etapas (seção 4 da especificação), feita no Pull Request.
5. **Integrar** — merge na `main` só com 100% dos testes aprovados.

Branches: `main` (estável), `feature/sdd-specification`, `feature/test-harness` e `feature/task-analyzer-impl`. Commits seguem Conventional Commits (`feat:`, `test:`, `docs:`, `chore:`).

## Uso de IA

O código de `src/` e os testes de `tests/` foram gerados com apoio do assistente **Claude** (Anthropic), a partir da especificação e das regras de contexto deste repositório, e revisados por mim antes da integração. Commits com código gerado por IA trazem a linha `Co-Authored-By` identificando o assistente.

## Autor

Andrei Barone Romaskevis · Ciência da Computação — CEUB · andrei.barone@sempreceub.com
Especificação da Fase 1: [Google Docs](https://docs.google.com/document/d/1UShTgmNH7D07mt4KzTqrDS1DUCqOr44yccvYN0fY8Jo/edit?usp=sharing)
