"""Validação estrita das entradas do TaskAnalyzer.

Converte registros brutos (dicionários) em ``Tarefa`` validadas. A validação
roda inteira antes de qualquer cálculo e para na primeira falha (RN09):
um único registro inválido invalida a análise toda.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from datetime import date, datetime, time, timezone
from typing import Any, Final

from .exceptions import (
    CampoObrigatorioError,
    ConfiguracaoInvalidaError,
    DataInvalidaError,
    IdDuplicadoError,
    PrioridadeInvalidaError,
    StatusInvalidoError,
)
from .models import Prioridade, Status, Tarefa

TAMANHO_MAXIMO_TITULO: Final[int] = 200


def validar_tarefas(registros: Sequence[Mapping[str, Any]]) -> list[Tarefa]:
    """Valida a coleção inteira e devolve as tarefas convertidas.

    Args:
        registros: Lista (ou tupla) de dicionários, um por tarefa.

    Returns:
        Tarefas validadas, na mesma ordem da entrada.

    Raises:
        ConfiguracaoInvalidaError: Se a coleção não for lista nem tupla.
        IdDuplicadoError: Se dois registros tiverem o mesmo ``id_tarefa``.
        TaskValidationError: Qualquer outra falha de um registro.
    """
    if not isinstance(registros, (list, tuple)):
        raise ConfiguracaoInvalidaError(
            "deve ser uma lista de tarefas", campo="tarefas"
        )
    tarefas = [validar_tarefa(registro) for registro in registros]
    _verificar_ids_unicos(tarefas)
    return tarefas


def validar_tarefa(registro: Mapping[str, Any]) -> Tarefa:
    """Valida um único registro e o converte em ``Tarefa``.

    Campos fora do contrato são ignorados; os do contrato são conferidos
    um a um, na ordem da tabela 1.3.2 da especificação.

    Args:
        registro: Dicionário com os campos de uma tarefa.

    Returns:
        Tarefa validada.

    Raises:
        CampoObrigatorioError: Campo ausente, vazio ou com tipo inválido.
        PrioridadeInvalidaError: Prioridade fora do domínio.
        StatusInvalidoError: Status fora do domínio.
        DataInvalidaError: Data malformada ou fora de ordem.
    """
    if not isinstance(registro, Mapping):
        raise CampoObrigatorioError(
            "cada tarefa deve ser um dicionário", campo="tarefa"
        )

    id_tarefa = _validar_id(registro.get("id_tarefa"))
    titulo = _validar_titulo(registro.get("titulo"), id_tarefa)
    prioridade = _validar_prioridade(registro.get("prioridade"), id_tarefa)
    status = _validar_status(registro.get("status"), id_tarefa)

    data_criacao = _converter_data(
        registro.get("data_criacao"), id_tarefa, "data_criacao"
    )
    if data_criacao is None:
        raise CampoObrigatorioError(
            "é obrigatório", id_tarefa=id_tarefa, campo="data_criacao"
        )
    data_inicio = _converter_data(
        registro.get("data_inicio"), id_tarefa, "data_inicio"
    )
    data_conclusao = _converter_data(
        registro.get("data_conclusao"), id_tarefa, "data_conclusao"
    )
    if status is Status.CONCLUIDA and data_conclusao is None:
        raise CampoObrigatorioError(
            "é obrigatório quando o status é CONCLUIDA",
            id_tarefa=id_tarefa,
            campo="data_conclusao",
        )

    _validar_cronologia(id_tarefa, data_criacao, data_inicio, data_conclusao)

    return Tarefa(
        id_tarefa=id_tarefa,
        titulo=titulo,
        prioridade=prioridade,
        status=status,
        data_criacao=data_criacao,
        data_inicio=data_inicio,
        data_conclusao=data_conclusao,
    )


def _validar_id(valor: object) -> int:
    """Confere que o identificador é um inteiro positivo.

    Args:
        valor: Valor bruto do campo ``id_tarefa``.

    Returns:
        O identificador validado.

    Raises:
        CampoObrigatorioError: Se ausente ou se não for inteiro positivo.
    """
    if valor is None:
        raise CampoObrigatorioError("é obrigatório", campo="id_tarefa")
    # bool é subclasse de int em Python; True não pode virar o id 1.
    if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
        raise CampoObrigatorioError(
            "deve ser um inteiro positivo", id_tarefa=valor, campo="id_tarefa"
        )
    return valor


def _validar_titulo(valor: object, id_tarefa: int) -> str:
    """Confere que o título é texto não vazio dentro do limite.

    Args:
        valor: Valor bruto do campo ``titulo``.
        id_tarefa: Tarefa dona do campo, para a mensagem de erro.

    Returns:
        O título sem espaços nas pontas.

    Raises:
        CampoObrigatorioError: Se ausente, vazio ou longo demais.
    """
    if not isinstance(valor, str) or not valor.strip():
        raise CampoObrigatorioError(
            "deve ser um texto não vazio", id_tarefa=id_tarefa, campo="titulo"
        )
    titulo = valor.strip()
    if len(titulo) > TAMANHO_MAXIMO_TITULO:
        raise CampoObrigatorioError(
            f"excede {TAMANHO_MAXIMO_TITULO} caracteres",
            id_tarefa=id_tarefa,
            campo="titulo",
        )
    return titulo


def _validar_prioridade(valor: object, id_tarefa: int) -> Prioridade:
    """Confere que a prioridade pertence ao domínio fechado.

    Args:
        valor: Valor bruto do campo ``prioridade``.
        id_tarefa: Tarefa dona do campo, para a mensagem de erro.

    Returns:
        A prioridade como membro do enum.

    Raises:
        CampoObrigatorioError: Se ausente.
        PrioridadeInvalidaError: Se fora de ALTA / MEDIA / BAIXA.
    """
    if valor is None:
        raise CampoObrigatorioError(
            "é obrigatório", id_tarefa=id_tarefa, campo="prioridade"
        )
    try:
        if not isinstance(valor, str):
            raise ValueError
        return Prioridade(valor)
    except ValueError:
        raise PrioridadeInvalidaError(
            f"valor {valor!r} fora do domínio ALTA / MEDIA / BAIXA",
            id_tarefa=id_tarefa,
            campo="prioridade",
        ) from None


def _validar_status(valor: object, id_tarefa: int) -> Status:
    """Confere que o status pertence ao domínio fechado.

    Args:
        valor: Valor bruto do campo ``status``.
        id_tarefa: Tarefa dona do campo, para a mensagem de erro.

    Returns:
        O status como membro do enum.

    Raises:
        CampoObrigatorioError: Se ausente.
        StatusInvalidoError: Se fora do domínio de status.
    """
    if valor is None:
        raise CampoObrigatorioError(
            "é obrigatório", id_tarefa=id_tarefa, campo="status"
        )
    try:
        if not isinstance(valor, str):
            raise ValueError
        return Status(valor)
    except ValueError:
        raise StatusInvalidoError(
            f"valor {valor!r} fora do domínio "
            "PENDENTE / EM_ANDAMENTO / CONCLUIDA / CANCELADA",
            id_tarefa=id_tarefa,
            campo="status",
        ) from None


def _converter_data(
    valor: object, id_tarefa: int, campo: str
) -> datetime | None:
    """Converte o valor bruto de uma data em ``datetime`` sem fuso.

    Aceita ``datetime``, ``date`` (vira meia-noite) e texto ISO 8601. Datas
    com fuso são convertidas para UTC e perdem o fuso, para que comparar uma
    data com fuso e outra sem fuso nunca lance ``TypeError``.

    Args:
        valor: Valor bruto do campo.
        id_tarefa: Tarefa dona do campo, para a mensagem de erro.
        campo: Nome do campo, para a mensagem de erro.

    Returns:
        A data convertida, ou ``None`` se o campo estiver vazio.

    Raises:
        DataInvalidaError: Se o texto não for ISO 8601 ou o tipo não for
            suportado.
    """
    if valor is None:
        return None
    if isinstance(valor, datetime):
        return _remover_fuso(valor)
    if isinstance(valor, date):
        return datetime.combine(valor, time.min)
    if isinstance(valor, str):
        texto = valor.strip()
        if not texto:
            return None
        try:
            return _remover_fuso(datetime.fromisoformat(texto))
        except ValueError:
            raise DataInvalidaError(
                f"valor {valor!r} não está no formato ISO 8601",
                id_tarefa=id_tarefa,
                campo=campo,
            ) from None
    raise DataInvalidaError(
        f"tipo {type(valor).__name__} não suportado para datas",
        id_tarefa=id_tarefa,
        campo=campo,
    )


def _remover_fuso(momento: datetime) -> datetime:
    """Normaliza um ``datetime`` com fuso para UTC sem fuso.

    Args:
        momento: Data e hora, com ou sem fuso.

    Returns:
        A mesma data em UTC, sem ``tzinfo``. Datas sem fuso voltam intactas.
    """
    if momento.tzinfo is None:
        return momento
    return momento.astimezone(timezone.utc).replace(tzinfo=None)


def _validar_cronologia(
    id_tarefa: int,
    data_criacao: datetime,
    data_inicio: datetime | None,
    data_conclusao: datetime | None,
) -> None:
    """Confere a ordem criação ≤ início ≤ conclusão (RN02).

    Args:
        id_tarefa: Tarefa sendo validada, para a mensagem de erro.
        data_criacao: Momento de criação.
        data_inicio: Momento de início, se houver.
        data_conclusao: Momento de conclusão, se houver.

    Raises:
        DataInvalidaError: Se alguma data vier antes da anterior.
    """
    if data_inicio is not None and data_inicio < data_criacao:
        raise DataInvalidaError(
            "é anterior à data_criacao",
            id_tarefa=id_tarefa,
            campo="data_inicio",
        )
    if data_conclusao is None:
        return
    if data_inicio is not None:
        referencia, nome_referencia = data_inicio, "data_inicio"
    else:
        referencia, nome_referencia = data_criacao, "data_criacao"
    if data_conclusao < referencia:
        raise DataInvalidaError(
            f"é anterior à {nome_referencia}",
            id_tarefa=id_tarefa,
            campo="data_conclusao",
        )


def _verificar_ids_unicos(tarefas: Sequence[Tarefa]) -> None:
    """Garante que nenhum identificador se repete na coleção (RN07).

    Args:
        tarefas: Tarefas já validadas individualmente.

    Raises:
        IdDuplicadoError: Para o menor identificador repetido.
    """
    contagem = Counter(tarefa.id_tarefa for tarefa in tarefas)
    repetidos = sorted(id_ for id_, vezes in contagem.items() if vezes > 1)
    if repetidos:
        primeiro = repetidos[0]
        raise IdDuplicadoError(
            f"aparece {contagem[primeiro]} vezes na coleção",
            id_tarefa=primeiro,
            campo="id_tarefa",
        )
