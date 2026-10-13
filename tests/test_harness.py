"""Test Harness do TaskAnalyzer.

Cada teste traduz um cenário de aceite da especificação
(``specs/task_analyzer_spec.md``, capítulo 2). O bloco "Dado" vira a massa
de dados, o "Quando" vira a chamada de ``analyze_tasks`` e o "Então" vira a
asserção. Os valores esperados foram calculados à mão antes do código.
"""

from __future__ import annotations

import copy
import logging
from collections.abc import Callable
from datetime import date, datetime
from typing import Any

import pytest

from src.exceptions import (
    CampoObrigatorioError,
    ConfiguracaoInvalidaError,
    DataInvalidaError,
    IdDuplicadoError,
    PrioridadeInvalidaError,
    StatusInvalidoError,
)
from src.models import Prioridade, Status, Tarefa
from src.task_analyzer import TaskValidationError, analyze_tasks

Registro = dict[str, Any]
FabricaTarefa = Callable[..., Registro]

PRIORIDADE_ZERADA = {
    "total": 0,
    "concluidas": 0,
    "tempo_medio_conclusao_horas": 0.0,
    "taxa_atraso_percentual": 0.0,
}


# ---------------------------------------------------------------------------
# Cenário 1 — caminho de sucesso
# ---------------------------------------------------------------------------


def test_ca01_calcula_metricas_com_dados_validos(
    massa_referencia: list[Registro],
) -> None:
    """CA01: seis tarefas válidas geram exatamente os valores da seção 2.4."""
    relatorio = analyze_tasks(massa_referencia)

    assert relatorio == {
        "total_tarefas": 6,
        "total_concluidas": 4,
        "total_pendentes": 2,
        "total_canceladas": 0,
        "percentual_conclusao": 66.67,
        "tempo_medio_conclusao_horas": 162.0,
        "taxa_atraso_percentual": 50.0,
        "metricas_por_prioridade": {
            "ALTA": {
                "total": 2,
                "concluidas": 1,
                "tempo_medio_conclusao_horas": 24.0,
                "taxa_atraso_percentual": 0.0,
            },
            "MEDIA": {
                "total": 2,
                "concluidas": 2,
                "tempo_medio_conclusao_horas": 144.0,
                "taxa_atraso_percentual": 50.0,
            },
            "BAIXA": {
                "total": 2,
                "concluidas": 1,
                "tempo_medio_conclusao_horas": 336.0,
                "taxa_atraso_percentual": 100.0,
            },
        },
    }


def test_ca01_tarefas_nao_concluidas_nao_alteram_tempo_nem_atraso(
    massa_referencia: list[Registro], criar_tarefa: FabricaTarefa
) -> None:
    """CA01: acrescentar uma pendente muda os totais, mas não as médias."""
    pendente = criar_tarefa(
        id_tarefa=99, status="PENDENTE", data_inicio=None, data_conclusao=None
    )

    relatorio = analyze_tasks([*massa_referencia, pendente])

    assert relatorio["total_tarefas"] == 7
    assert relatorio["total_pendentes"] == 3
    assert relatorio["tempo_medio_conclusao_horas"] == 162.0
    assert relatorio["taxa_atraso_percentual"] == 50.0


# ---------------------------------------------------------------------------
# Cenário 2 — caminho de exceção
# ---------------------------------------------------------------------------


def test_ca02_lanca_erro_para_conclusao_anterior_a_criacao(
    criar_tarefa: FabricaTarefa,
) -> None:
    """CA02: conclusão em 05/03 para tarefa criada em 10/03 é rejeitada."""
    tarefa = criar_tarefa(
        id_tarefa=7,
        data_criacao="2026-03-10",
        data_inicio=None,
        data_conclusao="2026-03-05",
    )

    with pytest.raises(TaskValidationError) as erro:
        analyze_tasks([tarefa])

    assert isinstance(erro.value, DataInvalidaError)
    assert erro.value.id_tarefa == 7
    assert erro.value.campo == "data_conclusao"
    assert "tarefa 7" in str(erro.value)


def test_ca02_lanca_erro_para_inicio_anterior_a_criacao(
    criar_tarefa: FabricaTarefa,
) -> None:
    """CA02: início antes da criação também quebra a cronologia (RN02)."""
    tarefa = criar_tarefa(data_inicio="2026-03-01T07:00:00")

    with pytest.raises(DataInvalidaError, match="data_inicio"):
        analyze_tasks([tarefa])


def test_ca02_lanca_erro_para_conclusao_anterior_ao_inicio(
    criar_tarefa: FabricaTarefa,
) -> None:
    """CA02: com início informado, a conclusão é comparada a ele."""
    tarefa = criar_tarefa(
        data_inicio="2026-03-01T10:00:00", data_conclusao="2026-03-01T09:00:00"
    )

    with pytest.raises(DataInvalidaError, match="anterior à data_inicio"):
        analyze_tasks([tarefa])


@pytest.mark.parametrize("data", ["2026-13-01", "01/03/2026", "ontem"])
def test_ca02_lanca_erro_para_data_malformada(
    criar_tarefa: FabricaTarefa, data: str
) -> None:
    """CA02: datas fora do ISO 8601 são rejeitadas, não adivinhadas."""
    with pytest.raises(DataInvalidaError, match="ISO 8601"):
        analyze_tasks([criar_tarefa(data_criacao=data)])


def test_ca02_lanca_erro_para_tipo_de_data_nao_suportado(
    criar_tarefa: FabricaTarefa,
) -> None:
    """CA02: um número no lugar da data é rejeitado pelo tipo."""
    with pytest.raises(DataInvalidaError, match="não suportado"):
        analyze_tasks([criar_tarefa(data_criacao=20260301)])
