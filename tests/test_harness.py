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


# ---------------------------------------------------------------------------
# Casos de borda
# ---------------------------------------------------------------------------


def test_ca03_colecao_vazia_retorna_metricas_zeradas() -> None:
    """CA03: lista vazia é entrada válida e não divide por zero (RN03, RN04)."""
    relatorio = analyze_tasks([])

    assert relatorio == {
        "total_tarefas": 0,
        "total_concluidas": 0,
        "total_pendentes": 0,
        "total_canceladas": 0,
        "percentual_conclusao": 0.0,
        "tempo_medio_conclusao_horas": 0.0,
        "taxa_atraso_percentual": 0.0,
        "metricas_por_prioridade": {
            "ALTA": PRIORIDADE_ZERADA,
            "MEDIA": PRIORIDADE_ZERADA,
            "BAIXA": PRIORIDADE_ZERADA,
        },
    }


def test_ca04_apenas_tarefas_pendentes_nao_divide_por_zero(
    criar_tarefa: FabricaTarefa,
) -> None:
    """CA04: sem nenhuma concluída, médias voltam 0.0 sem exceção."""
    pendentes = [
        criar_tarefa(
            id_tarefa=i, status=status, data_inicio=None, data_conclusao=None
        )
        for i, status in enumerate(
            ["PENDENTE", "EM_ANDAMENTO", "PENDENTE", "PENDENTE", "EM_ANDAMENTO"],
            start=1,
        )
    ]

    relatorio = analyze_tasks(pendentes)

    assert relatorio["total_tarefas"] == 5
    assert relatorio["total_pendentes"] == 5
    assert relatorio["total_concluidas"] == 0
    assert relatorio["percentual_conclusao"] == 0.0
    assert relatorio["tempo_medio_conclusao_horas"] == 0.0
    assert relatorio["taxa_atraso_percentual"] == 0.0


def test_ca05_prioridade_sem_tarefas_aparece_zerada(
    criar_tarefa: FabricaTarefa,
) -> None:
    """CA05: toda prioridade do domínio aparece, mesmo sem tarefas."""
    relatorio = analyze_tasks([criar_tarefa(prioridade="ALTA")])

    assert set(relatorio["metricas_por_prioridade"]) == {"ALTA", "MEDIA", "BAIXA"}
    assert relatorio["metricas_por_prioridade"]["MEDIA"] == PRIORIDADE_ZERADA
    assert relatorio["metricas_por_prioridade"]["BAIXA"] == PRIORIDADE_ZERADA


# ---------------------------------------------------------------------------
# Cenários complementares
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("prioridade", ["URGENTE", "alta", "Media", "", 1])
def test_ca06_lanca_erro_para_prioridade_invalida(
    criar_tarefa: FabricaTarefa, prioridade: object
) -> None:
    """CA06: prioridade fora do domínio é rejeitada, inclusive minúscula."""
    with pytest.raises(PrioridadeInvalidaError):
        analyze_tasks([criar_tarefa(prioridade=prioridade)])


@pytest.mark.parametrize("status", ["FEITA", "concluida", "ATRASADA", 3])
def test_ca06_lanca_erro_para_status_invalido(
    criar_tarefa: FabricaTarefa, status: object
) -> None:
    """CA06: status fora do domínio é rejeitado; não há status 'desconhecido'."""
    with pytest.raises(StatusInvalidoError):
        analyze_tasks([criar_tarefa(status=status)])


def test_ca07_lanca_erro_para_concluida_sem_data_de_conclusao(
    criar_tarefa: FabricaTarefa,
) -> None:
    """CA07: tarefa CONCLUIDA sem data de conclusão é rejeitada (RN06)."""
    with pytest.raises(CampoObrigatorioError, match="data_conclusao"):
        analyze_tasks([criar_tarefa(data_conclusao=None)])


def test_ca08_conclusao_no_limite_do_sla_nao_e_atraso(
    criar_tarefa: FabricaTarefa,
) -> None:
    """CA08: ALTA concluída em exatamente 48 horas está dentro do prazo."""
    tarefa = criar_tarefa(
        prioridade="ALTA",
        data_criacao="2026-03-01T08:00:00",
        data_inicio=None,
        data_conclusao="2026-03-03T08:00:00",
    )

    relatorio = analyze_tasks([tarefa])

    assert relatorio["tempo_medio_conclusao_horas"] == 48.0
    assert relatorio["taxa_atraso_percentual"] == 0.0


def test_ca08_um_minuto_apos_o_sla_ja_e_atraso(
    criar_tarefa: FabricaTarefa,
) -> None:
    """CA08: passar um minuto do limite já conta como atraso."""
    tarefa = criar_tarefa(
        prioridade="ALTA",
        data_criacao="2026-03-01T08:00:00",
        data_inicio=None,
        data_conclusao="2026-03-03T08:01:00",
    )

    assert analyze_tasks([tarefa])["taxa_atraso_percentual"] == 100.0


def test_ca09_lanca_erro_para_id_duplicado(criar_tarefa: FabricaTarefa) -> None:
    """CA09: dois registros com o mesmo id invalidam a coleção (RN07)."""
    with pytest.raises(IdDuplicadoError) as erro:
        analyze_tasks([criar_tarefa(id_tarefa=3), criar_tarefa(id_tarefa=3)])

    assert erro.value.id_tarefa == 3


def test_ca10_tarefa_cancelada_e_ignorada_nas_metricas(
    criar_tarefa: FabricaTarefa,
) -> None:
    """CA10: cancelada com data de conclusão conta só no total."""
    cancelada = criar_tarefa(
        id_tarefa=1,
        status="CANCELADA",
        data_conclusao="2026-03-20T08:00:00",
    )
    concluida = criar_tarefa(id_tarefa=2)

    relatorio = analyze_tasks([cancelada, concluida])

    assert relatorio["total_tarefas"] == 2
    assert relatorio["total_canceladas"] == 1
    assert relatorio["total_concluidas"] == 1
    assert relatorio["tempo_medio_conclusao_horas"] == 4.0


# ---------------------------------------------------------------------------
# Robustez de entrada — regras de validação da tabela 1.3.2
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "campo", ["id_tarefa", "titulo", "prioridade", "status", "data_criacao"]
)
def test_lanca_erro_quando_campo_obrigatorio_esta_ausente(
    criar_tarefa: FabricaTarefa, campo: str
) -> None:
    """Cada campo obrigatório ausente gera CampoObrigatorioError."""
    tarefa = criar_tarefa()
    del tarefa[campo]

    with pytest.raises(CampoObrigatorioError, match=campo):
        analyze_tasks([tarefa])


@pytest.mark.parametrize("id_invalido", [0, -1, "1", True, 1.5])
def test_lanca_erro_para_id_que_nao_e_inteiro_positivo(
    criar_tarefa: FabricaTarefa, id_invalido: object
) -> None:
    """O id precisa ser inteiro positivo; True não vira 1."""
    with pytest.raises(CampoObrigatorioError, match="inteiro positivo"):
        analyze_tasks([criar_tarefa(id_tarefa=id_invalido)])


@pytest.mark.parametrize("titulo", ["", "   ", 42, "x" * 201])
def test_lanca_erro_para_titulo_invalido(
    criar_tarefa: FabricaTarefa, titulo: object
) -> None:
    """Título vazio, não textual ou com mais de 200 caracteres é rejeitado."""
    with pytest.raises(CampoObrigatorioError, match="titulo"):
        analyze_tasks([criar_tarefa(titulo=titulo)])


def test_titulo_com_200_caracteres_e_aceito(criar_tarefa: FabricaTarefa) -> None:
    """O limite de 200 caracteres é inclusivo."""
    assert analyze_tasks([criar_tarefa(titulo="x" * 200)])["total_tarefas"] == 1


@pytest.mark.parametrize("entrada", ["texto", None, {"id_tarefa": 1}, 42])
def test_lanca_erro_quando_colecao_nao_e_lista(entrada: Any) -> None:
    """A coleção precisa ser lista ou tupla; texto e dicionário não servem."""
    with pytest.raises(ConfiguracaoInvalidaError, match="lista"):
        analyze_tasks(entrada)


def test_lanca_erro_quando_registro_nao_e_dicionario() -> None:
    """Cada item da coleção precisa ser um dicionário."""
    with pytest.raises(CampoObrigatorioError, match="dicionário"):
        analyze_tasks([["id", 1]])  # type: ignore[list-item]


def test_aceita_tupla_de_tarefas(massa_referencia: list[Registro]) -> None:
    """Tupla é aceita como coleção, com o mesmo resultado da lista."""
    assert analyze_tasks(tuple(massa_referencia)) == analyze_tasks(
        massa_referencia
    )


def test_aceita_enums_date_e_datetime(criar_tarefa: FabricaTarefa) -> None:
    """Além de texto, aceita os próprios enums e objetos date/datetime."""
    tarefa = criar_tarefa(
        prioridade=Prioridade.BAIXA,
        status=Status.CONCLUIDA,
        data_criacao=date(2026, 3, 1),
        data_inicio=None,
        data_conclusao=datetime(2026, 3, 1, 6, 30),
    )

    relatorio = analyze_tasks([tarefa])

    assert relatorio["tempo_medio_conclusao_horas"] == 6.5


def test_normaliza_datas_com_fuso_para_utc(criar_tarefa: FabricaTarefa) -> None:
    """Data com fuso e data sem fuso podem ser comparadas sem TypeError.

    08:00 em -03:00 é 11:00 UTC; conclusão às 13:00 sem fuso dá 2 horas.
    """
    tarefa = criar_tarefa(
        data_criacao="2026-03-01T08:00:00-03:00",
        data_inicio="2026-03-01T11:00:00Z",
        data_conclusao="2026-03-01T13:00:00",
    )

    assert analyze_tasks([tarefa])["tempo_medio_conclusao_horas"] == 2.0


def test_campos_vazios_opcionais_sao_tratados_como_ausentes(
    criar_tarefa: FabricaTarefa,
) -> None:
    """Texto vazio em data opcional equivale a não informar a data."""
    tarefa = criar_tarefa(status="PENDENTE", data_inicio="", data_conclusao="  ")

    assert analyze_tasks([tarefa])["total_pendentes"] == 1


def test_campos_fora_do_contrato_sao_ignorados(
    criar_tarefa: FabricaTarefa,
) -> None:
    """Um campo extra, como data_prevista, não altera o cálculo."""
    tarefa = criar_tarefa(data_prevista="2026-03-01T09:00:00")

    assert analyze_tasks([tarefa])["taxa_atraso_percentual"] == 0.0


def test_entrada_nao_e_modificada(massa_referencia: list[Registro]) -> None:
    """A função é pura: os dicionários recebidos voltam intactos."""
    original = copy.deepcopy(massa_referencia)

    analyze_tasks(massa_referencia)

    assert massa_referencia == original


# ---------------------------------------------------------------------------
# SLA parametrizável (RN08)
# ---------------------------------------------------------------------------


def test_sla_personalizado_substitui_apenas_a_prioridade_informada(
    massa_referencia: list[Registro],
) -> None:
    """Com SLA de ALTA em 12h, a tarefa 1 (24h) passa a contar como atraso."""
    relatorio = analyze_tasks(
        massa_referencia, sla_por_prioridade={Prioridade.ALTA: 12}
    )

    assert relatorio["metricas_por_prioridade"]["ALTA"][
        "taxa_atraso_percentual"
    ] == 100.0
    assert relatorio["metricas_por_prioridade"]["MEDIA"][
        "taxa_atraso_percentual"
    ] == 50.0
    assert relatorio["taxa_atraso_percentual"] == 75.0


@pytest.mark.parametrize(
    "sla",
    [
        {Prioridade.ALTA: 0},
        {Prioridade.MEDIA: -5},
        {Prioridade.BAIXA: "48"},
        {Prioridade.ALTA: True},
        {"URGENTE": 10},
    ],
)
def test_lanca_erro_para_sla_invalido(
    massa_referencia: list[Registro], sla: dict[Any, Any]
) -> None:
    """Prazo zero, negativo, não numérico ou com chave inválida é rejeitado."""
    with pytest.raises(ConfiguracaoInvalidaError, match="sla_por_prioridade"):
        analyze_tasks(massa_referencia, sla_por_prioridade=sla)


# ---------------------------------------------------------------------------
# Contrato das exceções e observabilidade
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "classe",
    [
        CampoObrigatorioError,
        DataInvalidaError,
        PrioridadeInvalidaError,
        StatusInvalidoError,
        IdDuplicadoError,
        ConfiguracaoInvalidaError,
    ],
)
def test_toda_excecao_herda_de_task_validation_error(classe: type) -> None:
    """Capturar TaskValidationError cobre qualquer falha de entrada."""
    assert issubclass(classe, TaskValidationError)


def test_mensagem_sem_tarefa_nem_campo_mostra_so_o_motivo() -> None:
    """Sem tarefa e campo, a mensagem é apenas o motivo."""
    assert str(CampoObrigatorioError("motivo puro")) == "motivo puro"


def test_duracao_exige_data_de_conclusao() -> None:
    """Calcular duração de tarefa sem conclusão é um erro explícito."""
    tarefa = Tarefa(
        id_tarefa=1,
        titulo="Sem conclusão",
        prioridade=Prioridade.ALTA,
        status=Status.PENDENTE,
        data_criacao=datetime(2026, 3, 1),
    )

    with pytest.raises(CampoObrigatorioError):
        tarefa.duracao_horas()


def test_registra_inicio_e_fim_da_analise_em_info(
    massa_referencia: list[Registro], caplog: pytest.LogCaptureFixture
) -> None:
    """O fluxo normal deixa dois registros INFO: início e conclusão."""
    with caplog.at_level(logging.INFO, logger="src.task_analyzer"):
        analyze_tasks(massa_referencia)

    mensagens = [r.getMessage() for r in caplog.records if r.levelno == logging.INFO]
    assert mensagens == [
        "Iniciando análise de 6 tarefa(s)",
        "Análise concluída: 6 tarefa(s), 4 concluída(s)",
    ]


def test_registra_falha_de_validacao_em_error(
    criar_tarefa: FabricaTarefa, caplog: pytest.LogCaptureFixture
) -> None:
    """Uma entrada inválida deixa um registro ERROR antes de propagar."""
    with caplog.at_level(logging.ERROR, logger="src.task_analyzer"):
        with pytest.raises(PrioridadeInvalidaError):
            analyze_tasks([criar_tarefa(prioridade="URGENTE")])

    assert any(r.levelno == logging.ERROR for r in caplog.records)
