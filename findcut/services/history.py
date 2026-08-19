from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from findcut.domain.models import Project


@dataclass
class ProjectHistory:
    """Bounded snapshot history for safe editor undo/redo operations."""

    limit: int = 50

    def __post_init__(self) -> None:
        self._undo: list[dict[str, Any]] = []
        self._redo: list[dict[str, Any]] = []

    def checkpoint(self, project: Project) -> None:
        self._undo.append(copy.deepcopy(project.to_dict()))
        if len(self._undo) > self.limit:
            del self._undo[0]
        self._redo.clear()

    def undo(self, project: Project) -> Project | None:
        if not self._undo:
            return None
        self._redo.append(copy.deepcopy(project.to_dict()))
        return Project.from_dict(self._undo.pop())

    def redo(self, project: Project) -> Project | None:
        if not self._redo:
            return None
        self._undo.append(copy.deepcopy(project.to_dict()))
        return Project.from_dict(self._redo.pop())

    @property
    def can_undo(self) -> bool:
        return bool(self._undo)

    @property
    def can_redo(self) -> bool:
        return bool(self._redo)
