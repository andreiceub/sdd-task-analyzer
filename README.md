# sdd-task-analyzer

[![CI Workflow](https://github.com/andreiceub/sdd-task-analyzer/actions/workflows/ci.yml/badge.svg)](https://github.com/andreiceub/sdd-task-analyzer/actions)

Módulo **TaskAnalyzer**, desenvolvido com **Spec-Driven Development (SDD)** e geração de código assistida por IA no Bootcamp III (CEUB).

Recebe uma lista de tarefas e devolve métricas de produtividade: totais, tempo médio de conclusão em horas, taxa de atraso e os mesmos indicadores separados por prioridade.

## Status do build

| Verificação | Resultado |
| --- | --- |
| `pytest -v` | 68 testes, 100% aprovados |
| Cobertura (`pytest --cov=src`) | 100% das linhas de `src/` |
| Tipagem (`mypy --strict`) | Sem erros |
| Integração contínua (GitHub Actions) | `pytest` em Python 3.11 a cada push e pull request nas branches `main` e `develop` |
| Docker (`python:3.11-slim`) | `docker run` e `docker compose run`: 68 testes aprovados |

## Como executar

Requer Python 3.11 ou superior (validado no 3.11, pelo Docker e pelo GitHub Actions, e no 3.12).

    git clone https://github.com/<seu-usuario>/sdd-task-analyzer.git
    cd sdd-task-analyzer
    python -m venv .venv
    # Linux/macOS: source .venv/bin/activate
    # Windows:     .venv\Scripts\activate
    pip install -r requirements.txt
    pytest -v

Para ver a cobertura:

    pytest -v --cov=src --cov-report=term-missing

## Execução com Docker

Com o Docker instalado, a suíte roda num ambiente isolado, sem instalar Python na máquina:

    docker build -t task-analyzer .
    docker run --rm task-analyzer

Ou, pelo Compose, com um único comando:

    docker compose run --rm task-analyzer-tests

## Integração contínua

O workflow `.github/workflows/ci.yml` roda no GitHub Actions a cada push e pull request nas branches `main` e `develop`: sobe uma máquina `ubuntu-latest`, configura o Python 3.11, instala o `requirements.txt` e executa `pytest tests/test_harness.py -v`. Se um teste falhar, o build fica vermelho e o problema aparece no pull request antes do merge.

## Google Colab

No Google Colab, rode numa célula:

    !git clone https://github.com/<seu-usuario>/sdd-task-analyzer.git
    %cd sdd-task-analyzer
    !pip install -q -r requirements.txt
    !pytest -v

## Exemplo de uso

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

## Estrutura

    sdd-task-analyzer/
    ├── README.md               # este arquivo
    ├── CONTEXT_RULES.md        # regras de governança entregues à IA
    ├── .github/
    │   └── workflows/
    │       └── ci.yml          # pipeline de CI no GitHub Actions
    ├── Dockerfile              # imagem python:3.11-slim que roda o pytest
    ├── docker-compose.yml      # serviço task-analyzer-tests
    ├── .dockerignore
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

## Fluxo de trabalho

1. **Especificar** — o contrato em `specs/` define entradas, saídas, regras e cenários de aceite.
2. **Escrever o harness** — os testes em `tests/` traduzem os cenários antes do código existir.
3. **Gerar com IA** — o assistente recebe a especificação e o `CONTEXT_RULES.md` e gera o código em etapas.
4. **Homologar** — revisão humana em cinco etapas (seção 4 da especificação), feita no Pull Request.
5. **Integrar** — merge na `main` só com 100% dos testes aprovados, conferidos também pelo GitHub Actions.

Branches: `main` (estável), `develop` (integração da Fase 3), `feature/sdd-specification`, `feature/test-harness` e `feature/task-analyzer-impl`. Commits seguem Conventional Commits (`feat:`, `test:`, `docs:`, `chore:`, `build:`, `ci:`).

## Uso de IA

O código de `src/` e os testes de `tests/` foram gerados com apoio do assistente **Claude** (Anthropic), a partir da especificação e das regras de contexto deste repositório, e revisados por mim antes da integração. Commits com código gerado por IA trazem a linha `Co-Authored-By` identificando o assistente.

Na Fase 3, o workflow de CI, o `Dockerfile` e o `docker-compose.yml` foram gerados com o **Gemini** (conta educacional do CEUB) e revisados por mim antes do commit, com apoio do Claude na conferência. Os ajustes feitos na revisão (versão do Python, versões das actions e uma reescrita do README fora do contrato, que foi rejeitada) estão registrados no relatório de governança.

## Autor

Andrei Barone Romaskevis · Ciência da Computação — CEUB · andrei.barone@sempreceub.comEspecificação da Fase 1: [Google Docs](https://docs.google.com/document/d/1UShTgmNH7D07mt4KzTqrDS1DUCqOr44yccvYN0fY8Jo/edit?usp=sharing)