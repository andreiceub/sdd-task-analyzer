"""Exceções customizadas do TaskAnalyzer (seção 1.4 da especificação).

Toda falha de entrada é uma ``TaskValidationError``. As subclasses dizem qual
regra foi violada, e a mensagem sempre identifica a tarefa e o campo, para que
o diagnóstico não exija leitura do código-fonte.
"""

from __future__ import annotations


class TaskValidationError(ValueError):
    """Base de todas as falhas de validação do módulo.

    Nunca é lançada diretamente: o código lança uma das subclasses, e quem
    chama pode capturar a base para tratar qualquer entrada inválida.

    Attributes:
        motivo: Descrição do problema encontrado.
        id_tarefa: Identificador da tarefa com problema, quando conhecido.
        campo: Nome do campo com problema, quando aplicável.
    """

    def __init__(
        self,
        motivo: str,
        *,
        id_tarefa: object | None = None,
        campo: str | None = None,
    ) -> None:
        """Monta a exceção e a mensagem padronizada.

        Args:
            motivo: Descrição do problema encontrado.
            id_tarefa: Identificador da tarefa com problema.
            campo: Nome do campo com problema.
        """
        self.motivo = motivo
        self.id_tarefa = id_tarefa
        self.campo = campo
        super().__init__(self._formatar_mensagem())

    def _formatar_mensagem(self) -> str:
        """Junta tarefa, campo e motivo em uma única linha legível.

        Returns:
            Mensagem no formato ``tarefa 7, campo 'x': motivo``.
        """
        partes: list[str] = []
        if self.id_tarefa is not None:
            partes.append(f"tarefa {self.id_tarefa!r}")
        if self.campo is not None:
            partes.append(f"campo '{self.campo}'")
        prefixo = ", ".join(partes)
        return f"{prefixo}: {self.motivo}" if prefixo else self.motivo


class CampoObrigatorioError(TaskValidationError):
    """Campo obrigatório ausente, nulo, vazio ou com tipo inválido (RN06)."""


class DataInvalidaError(TaskValidationError):
    """Data malformada ou cronologia inconsistente (RN02)."""


class PrioridadeInvalidaError(TaskValidationError):
    """Prioridade fora do domínio ALTA / MEDIA / BAIXA (RN05)."""


class StatusInvalidoError(TaskValidationError):
    """Status fora do domínio PENDENTE / EM_ANDAMENTO / CONCLUIDA / CANCELADA."""


class IdDuplicadoError(TaskValidationError):
    """Dois ou mais registros com o mesmo ``id_tarefa`` (RN07)."""


class ConfiguracaoInvalidaError(TaskValidationError):
    """Parâmetro da chamada inválido: coleção que não é lista ou SLA inválido."""
