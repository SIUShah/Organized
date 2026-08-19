from findcut.domain.models import Project
from findcut.services.history import ProjectHistory


def test_project_history_undo_and_redo_round_trip() -> None:
    project = Project(name="Before")
    history = ProjectHistory(limit=2)
    history.checkpoint(project)
    project.name = "After"
    restored = history.undo(project)
    assert restored is not None
    assert restored.name == "Before"
    redone = history.redo(restored)
    assert redone is not None
    assert redone.name == "After"


def test_project_history_is_bounded_and_clears_redo_on_checkpoint() -> None:
    project = Project()
    history = ProjectHistory(limit=2)
    for name in ("one", "two", "three"):
        history.checkpoint(project)
        project.name = name
    assert history.can_undo
    history.undo(project)
    assert history.can_redo
    history.checkpoint(project)
    assert not history.can_redo
