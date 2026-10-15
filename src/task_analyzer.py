"""Ponto de entrada público do TaskAnalyzer.

Expõe ``analyze_tasks``, que recebe uma coleção de tarefas e devolve as
métricas de produtividade definidas na especificação
(``specs/task_analyzer_spec.md``), e ``TaskValidationError``, a exceção base
para qualquer entrada inválida.

O módulo é determinístico: não persiste dados, não acessa rede e devolve
sempre o mesmo relatório para a mesma entrada.

Exemplo:
    >>> from src.task_analyzer import analyze_tasks
    >>> relatorio = analyze_tasks([])
    >>> relatorio["total_tarefas"]
    0
"""

from __future__ import annotations

import logging
from collections.abc import Mapping, Sequence
from typing import Any, Final

from .exceptions import ConfiguracaoInvalidaError, TaskValidationError
from .models import (
    SLA_PADRAO_HORAS,
    MetricasPrioridade,
    Prioridade,
    RelatorioProdutividade,
    Status,
    Tarefa,
)
from .validators import validar_tarefas

__all__ = ["TaskValidationError", "analyze_tasks"]

logger = logging.getLogger(__name__)

CASAS_DECIMAIS: Final[int] = 2
STATUS_PENDENTES: Final[frozenset[Status]] = frozenset(
    {Status.PENDENTE, Status.EM_ANDAMENTO}
)


def analyze_tasks(
    tarefas: Sequence[Mapping[str, Any]],
    sla_por_prioridade: Mapping[Prioridade, float] | None = None,
) -> RelatorioProdutividade:
    """Calcula as métricas de produtividade de uma coleção de tarefas.

    A coleção inteira é validada antes de qualquer cálculo (RN09). Se tudo
    estiver válido, calcula totais, tempo médio de conclusão em horas, taxa
    de atraso contra o SLA de cada prioridade e os mesmos indicadores
    separados por prioridade.

    Args:
        tarefas: Lista de dicionários, um por tarefa, com os campos da
            tabela 1.3.2 da especificação. Uma lista vazia é válida (RN04).
        sla_por_prioridade: Prazos em horas que substituem o SLA padrão
            (ALTA 48, MEDIA 120, BAIXA 240) para as prioridades informadas.

    Returns:
        Relatório com todas as métricas, arredondadas em duas casas.

    Raises:
        TaskValidationError: Se qualquer tarefa ou parâmetro for inválido.
            A subclasse lançada indica qual regra foi violada.
    """
    try:
        sla = _resolver_sla(sla_por_prioridade)
        tarefas_validadas = validar_tarefas(tarefas)
    except TaskValidationError as erro:
        logger.error("Análise interrompida por entrada inválida: %s", erro)
        raise

    logger.info("Iniciando análise de %d tarefa(s)", len(tarefas_validadas))
    relatorio = _montar_relatorio(tarefas_validadas, sla)
    logger.info(
        "Análise concluída: %d tarefa(s), %d concluída(s)",
        relatorio["total_tarefas"],
        relatorio["total_concluidas"],
    )
    return relatorio


def _resolver_sla(
    personalizado: Mapping[Prioridade, float] | None,
) -> dict[Prioridade, float]:
    """Combina o SLA padrão com os valores informados pelo chamador.

    Args:
        personalizado: Prazos em horas para substituir os padrões.

    Returns:
        SLA completo, com um prazo positivo para cada prioridade.

    Raises:
        ConfiguracaoInvalidaError: Se uma chave não for prioridade válida
            ou se um prazo não for número positivo.
    """
    sla = dict(SLA_PADRAO_HORAS)
    if personalizado is None:
        return sla
    for chave, horas in personalizado.items():
        try:
            prioridade = Prioridade(chave)
        except ValueError:
            raise ConfiguracaoInvalidaError(
                f"chave {chave!r} não é uma prioridade válida",
                campo="sla_por_prioridade",
            ) from None
        if isinstance(horas, bool) or not isinstance(horas, (int, float)):
            raise ConfiguracaoInvalidaError(
                f"prazo de {prioridade} deve ser numérico",
                campo="sla_por_prioridade",
            )
        if horas <= 0:
            raise ConfiguracaoInvalidaError(
                f"prazo de {prioridade} deve ser maior que zero",
                campo="sla_por_prioridade",
            )
        sla[prioridade] = float(horas)
    return sla


def _montar_relatorio(
    tarefas: Sequence[Tarefa], sla: Mapping[Prioridade, float]
) -> RelatorioProdutividade:
    """Reúne os indicadores gerais e os separados por prioridade.

    Args:
        tarefas: Tarefas já validadas.
        sla: Prazo em horas de cada prioridade.

    Returns:
        O relatório completo de produtividade.
    """
    geral = _metricas_do_grupo(tarefas, sla)
    por_prioridade = {
        prioridade.value: _metricas_do_grupo(
            [t for t in tarefas if t.prioridade is prioridade], sla
        )
        for prioridade in Prioridade
    }
    return {
        "total_tarefas": geral["total"],
        "total_concluidas": geral["concluidas"],
        "total_pendentes": sum(
            1 for tarefa in tarefas if tarefa.status in STATUS_PENDENTES
        ),
        "total_canceladas": sum(
            1 for tarefa in tarefas if tarefa.status is Status.CANCELADA
        ),
        "percentual_conclusao": _arredondar(
            _percentual(geral["concluidas"], geral["total"])
        ),
        "tempo_medio_conclusao_horas": geral["tempo_medio_conclusao_horas"],
        "taxa_atraso_percentual": geral["taxa_atraso_percentual"],
        "metricas_por_prioridade": por_prioridade,
    }


def _metricas_do_grupo(
    tarefas: Sequence[Tarefa], sla: Mapping[Prioridade, float]
) -> MetricasPrioridade:
    """Calcula total, concluídas, tempo médio e atraso de um grupo.

    Só tarefas concluídas entram no tempo médio e no atraso (RN01).

    Args:
        tarefas: Grupo de tarefas (todas, ou as de uma prioridade).
        sla: Prazo em horas de cada prioridade.

    Returns:
        Indicadores do grupo, arredondados em duas casas.
    """
    concluidas = [tarefa for tarefa in tarefas if tarefa.concluida]
    duracoes = [tarefa.duracao_horas() for tarefa in concluidas]
    atrasadas = sum(1 for tarefa in concluidas if _esta_atrasada(tarefa, sla))
    return {
        "total": len(tarefas),
        "concluidas": len(concluidas),
        "tempo_medio_conclusao_horas": _arredondar(_media(duracoes)),
        "taxa_atraso_percentual": _arredondar(
            _percentual(atrasadas, len(concluidas))
        ),
    }


def _esta_atrasada(tarefa: Tarefa, sla: Mapping[Prioridade, float]) -> bool:
    """Indica se a tarefa passou do prazo da sua prioridade (RN08).

    Concluir exatamente no limite do SLA não é atraso.

    Args:
        tarefa: Tarefa concluída.
        sla: Prazo em horas de cada prioridade.

    Returns:
        ``True`` se a duração for estritamente maior que o prazo.
    """
    return tarefa.duracao_horas() > sla[tarefa.prioridade]


def _media(valores: Sequence[float]) -> float:
    """Calcula a média aritmética sem risco de divisão por zero (RN03).

    Args:
        valores: Números a serem somados.

    Returns:
        A média, ou ``0.0`` para uma sequência vazia.
    """
    if not valores:
        return 0.0
    return sum(valores) / len(valores)


def _percentual(parte: int, total: int) -> float:
    """Calcula ``parte / total * 100`` sem risco de divisão por zero (RN03).

    Args:
        parte: Quantidade que compõe o numerador.
        total: Quantidade de referência.

    Returns:
        O percentual, ou ``0.0`` quando ``total`` é zero.
    """
    if total == 0:
        return 0.0
    return parte / total * 100


def _arredondar(valor: float) -> float:
    """Arredonda em duas casas, só na montagem do relatório (RN10).

    Args:
        valor: Valor já calculado.

    Returns:
        O valor com duas casas decimais.
    """
    return round(valor, CASAS_DECIMAIS)
