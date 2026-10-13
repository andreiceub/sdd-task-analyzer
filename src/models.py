"""Modelos de domínio do TaskAnalyzer.

Define os domínios fechados de prioridade e status, a entidade ``Tarefa``
já validada e as estruturas tipadas do relatório de produtividade. Nenhuma
regra de validação mora aqui: este módulo só descreve a forma dos dados.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from types import MappingProxyType
from typing import Final, TypedDict

from .exceptions import CampoObrigatorioError

SEGUNDOS_POR_HORA: Final[int] = 3600


class Prioridade(StrEnum):
    """Domínio fechado de prioridades aceitas pelo módulo (RN05)."""

    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAIXA = "BAIXA"


class Status(StrEnum):
    """Domínio fechado de status aceitos pelo módulo (RN05)."""

    PENDENTE = "PENDENTE"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"


SLA_PADRAO_HORAS: Final[Mapping[Prioridade, float]] = MappingProxyType(
    {
        Prioridade.ALTA: 48.0,
        Prioridade.MEDIA: 120.0,
        Prioridade.BAIXA: 240.0,
    }
)
"""Prazo máximo de conclusão por prioridade, em horas corridas (RN08)."""


@dataclass(frozen=True, slots=True)
class Tarefa:
    """Tarefa já validada, pronta para entrar no cálculo das métricas.

    Attributes:
        id_tarefa: Identificador inteiro positivo, único na coleção.
        titulo: Título sem espaços nas pontas, com até 200 caracteres.
        prioridade: Prioridade dentro do domínio fechado.
        status: Status dentro do domínio fechado.
        data_criacao: Momento de criação, sem fuso (normalizado para UTC).
        data_inicio: Momento de início, quando informado.
        data_conclusao: Momento de conclusão, obrigatório se concluída.
    """

    id_tarefa: int
    titulo: str
    prioridade: Prioridade
    status: Status
    data_criacao: datetime
    data_inicio: datetime | None = None
    data_conclusao: datetime | None = None

    @property
    def concluida(self) -> bool:
        """Indica se a tarefa entra no cálculo de tempo e atraso (RN01)."""
        return self.status is Status.CONCLUIDA

    def duracao_horas(self) -> float:
        """Calcula o tempo entre criação e conclusão, em horas.

        Returns:
            Duração em horas corridas, sem arredondamento (RN10).

        Raises:
            CampoObrigatorioError: Se a tarefa não tiver data de conclusão.
        """
        if self.data_conclusao is None:
            raise CampoObrigatorioError(
                "é necessária para calcular a duração",
                id_tarefa=self.id_tarefa,
                campo="data_conclusao",
            )
        intervalo = self.data_conclusao - self.data_criacao
        return intervalo.total_seconds() / SEGUNDOS_POR_HORA


class MetricasPrioridade(TypedDict):
    """Indicadores calculados para um grupo de tarefas."""

    total: int
    concluidas: int
    tempo_medio_conclusao_horas: float
    taxa_atraso_percentual: float


class RelatorioProdutividade(TypedDict):
    """Saída completa de ``analyze_tasks`` (seção 1.3.3 da especificação)."""

    total_tarefas: int
    total_concluidas: int
    total_pendentes: int
    total_canceladas: int
    percentual_conclusao: float
    tempo_medio_conclusao_horas: float
    taxa_atraso_percentual: float
    metricas_por_prioridade: dict[str, MetricasPrioridade]
