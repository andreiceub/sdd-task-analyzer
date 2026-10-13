"""Fixtures compartilhadas pelo Test Harness.

A massa de referência é a mesma da seção 2.4 da especificação: dados
sintéticos, sem nenhuma informação pessoal, com valores esperados calculados
à mão antes da implementação existir.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pytest

Registro = dict[str, Any]


@pytest.fixture
def massa_referencia() -> list[Registro]:
    """Seis tarefas do cenário CA01: quatro concluídas, uma em andamento e
    uma pendente, duas de cada prioridade.

    Returns:
        Uma lista nova a cada teste, para nenhum teste afetar outro.
    """
    return [
        {
            "id_tarefa": 1,
            "titulo": "Corrigir bug de login",
            "prioridade": "ALTA",
            "status": "CONCLUIDA",
            "data_criacao": "2026-03-01",
            "data_inicio": "2026-03-01",
            "data_conclusao": "2026-03-02",
        },
        {
            "id_tarefa": 2,
            "titulo": "Atualizar documentação",
            "prioridade": "BAIXA",
            "status": "CONCLUIDA",
            "data_criacao": "2026-03-01",
            "data_inicio": "2026-03-03",
            "data_conclusao": "2026-03-15",
        },
        {
            "id_tarefa": 3,
            "titulo": "Refatorar relatórios",
            "prioridade": "MEDIA",
            "status": "CONCLUIDA",
            "data_criacao": "2026-03-02",
            "data_inicio": "2026-03-04",
            "data_conclusao": "2026-03-10",
        },
        {
            "id_tarefa": 4,
            "titulo": "Implementar filtro",
            "prioridade": "MEDIA",
            "status": "CONCLUIDA",
            "data_criacao": "2026-03-05",
            "data_inicio": "2026-03-06",
            "data_conclusao": "2026-03-09",
        },
        {
            "id_tarefa": 5,
            "titulo": "Migrar banco de dados",
            "prioridade": "ALTA",
            "status": "EM_ANDAMENTO",
            "data_criacao": "2026-03-06",
            "data_inicio": "2026-03-07",
            "data_conclusao": None,
        },
        {
            "id_tarefa": 6,
            "titulo": "Revisar contrato de API",
            "prioridade": "BAIXA",
            "status": "PENDENTE",
            "data_criacao": "2026-03-07",
            "data_inicio": None,
            "data_conclusao": None,
        },
    ]


@pytest.fixture
def criar_tarefa() -> Callable[..., Registro]:
    """Fábrica de uma tarefa válida, com campos sobrescrevíveis.

    Returns:
        Função que recebe os campos a trocar e devolve um registro novo.
    """

    def _criar(**campos: Any) -> Registro:
        registro: Registro = {
            "id_tarefa": 100,
            "titulo": "Tarefa de teste",
            "prioridade": "MEDIA",
            "status": "CONCLUIDA",
            "data_criacao": "2026-03-01T08:00:00",
            "data_inicio": "2026-03-01T09:00:00",
            "data_conclusao": "2026-03-01T12:00:00",
        }
        registro.update(campos)
        return registro

    return _criar
