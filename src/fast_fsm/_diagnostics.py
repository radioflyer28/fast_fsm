"""Bounded, snapshot-backed graph diagnostics.

This interpreted private module deliberately depends only on standard-library
types.  ``core.py`` owns snapshot capture and never imports this module, keeping
diagnostics outside the compiled runtime hot path.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import _GraphSnapshot


@dataclass(frozen=True, slots=True)
class DiagnosticLimits:
    """Finite, deterministic ceilings for one diagnostic operation."""

    max_work: int = 100_000
    max_results: int = 10_000
    max_dense_cells: int = 1_000_000
    max_path_expansions: int = 100_000

    def __post_init__(self) -> None:
        for field_name in (
            "max_work",
            "max_results",
            "max_dense_cells",
            "max_path_expansions",
        ):
            value = getattr(self, field_name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{field_name} must be a non-negative integer")


@dataclass(frozen=True, slots=True)
class DiagnosticStatus:
    """Scalar completion metadata that never includes caller-controlled text."""

    complete: bool
    exhausted_dimension: str | None
    exhausted_stage: str | None
    work_count: int
    result_count: int
    dense_cell_count: int
    path_expansion_count: int


class DiagnosticBudgetExceeded(RuntimeError):
    """Raised instead of returning a partial legacy diagnostic value."""

    __slots__ = ("status",)

    def __init__(self, status: DiagnosticStatus) -> None:
        super().__init__("diagnostic budget exhausted")
        self.status = status


@dataclass(frozen=True, slots=True)
class _DiagnosticEdge:
    """One scalar edge in immutable snapshot order."""

    from_index: int
    trigger: str
    to_index: int
    condition_name: str | None


@dataclass(frozen=True, slots=True)
class _DiagnosticGraph:
    """Tuple-backed scalar graph projection for interpreted diagnostics."""

    state_names: tuple[str, ...]
    edges: tuple[_DiagnosticEdge, ...]
    forward: tuple[tuple[int, ...], ...]
    reverse: tuple[tuple[int, ...], ...]
    initial_index: int | None
    initial_state_name: str
    current_state_name: str
    graph_version: int


class _DiagnosticBudget:
    """Mutable reserve-before-work ledger shared by one diagnostic graph call."""

    __slots__ = (
        "limits",
        "_complete",
        "_exhausted_dimension",
        "_exhausted_stage",
        "_work_count",
        "_result_count",
        "_dense_cell_count",
        "_path_expansion_count",
    )

    def __init__(self, limits: DiagnosticLimits | None = None) -> None:
        self.limits = limits if limits is not None else DiagnosticLimits()
        self._complete = True
        self._exhausted_dimension: str | None = None
        self._exhausted_stage: str | None = None
        self._work_count = 0
        self._result_count = 0
        self._dense_cell_count = 0
        self._path_expansion_count = 0

    @property
    def status(self) -> DiagnosticStatus:
        """Return the current scalar-only ledger state."""
        return DiagnosticStatus(
            complete=self._complete,
            exhausted_dimension=self._exhausted_dimension,
            exhausted_stage=self._exhausted_stage,
            work_count=self._work_count,
            result_count=self._result_count,
            dense_cell_count=self._dense_cell_count,
            path_expansion_count=self._path_expansion_count,
        )

    def reserve_work(self, *, stage: str, amount: int = 1) -> None:
        self._reserve("max_work", "_work_count", stage, amount)

    def reserve_result(self, *, stage: str, amount: int = 1) -> None:
        self._reserve("max_results", "_result_count", stage, amount)

    def reserve_dense_cells(self, *, stage: str, amount: int = 1) -> None:
        self._reserve("max_dense_cells", "_dense_cell_count", stage, amount)

    def reserve_path_expansion(self, *, stage: str, amount: int = 1) -> None:
        self._reserve("max_path_expansions", "_path_expansion_count", stage, amount)

    def _reserve(
        self, dimension: str, counter_name: str, stage: str, amount: int
    ) -> None:
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
            raise ValueError(
                "diagnostic reservation amount must be a non-negative integer"
            )
        current = getattr(self, counter_name)
        limit = getattr(self.limits, dimension)
        if current + amount > limit:
            self._complete = False
            self._exhausted_dimension = dimension
            self._exhausted_stage = stage
            raise DiagnosticBudgetExceeded(self.status)
        setattr(self, counter_name, current + amount)


def _graph_from_snapshot(snapshot: _GraphSnapshot) -> _DiagnosticGraph:
    """Convert a captured core snapshot to a scalar, index-addressed graph."""
    state_names = snapshot.state_names
    state_indices = {name: index for index, name in enumerate(state_names)}
    edges = tuple(
        _DiagnosticEdge(
            state_indices[transition.from_state_name],
            transition.trigger,
            state_indices[transition.to_state_name],
            transition.condition_name,
        )
        for transition in snapshot.transitions
    )
    forward_lists: list[list[int]] = [[] for _ in state_names]
    reverse_lists: list[list[int]] = [[] for _ in state_names]
    for edge_index, edge in enumerate(edges):
        forward_lists[edge.from_index].append(edge_index)
        reverse_lists[edge.to_index].append(edge_index)
    return _DiagnosticGraph(
        state_names=state_names,
        edges=edges,
        forward=tuple(tuple(indices) for indices in forward_lists),
        reverse=tuple(tuple(indices) for indices in reverse_lists),
        initial_index=state_indices.get(snapshot.initial_state_name),
        initial_state_name=snapshot.initial_state_name,
        current_state_name=snapshot.current_state_name,
        graph_version=snapshot.graph_version,
    )


def _reachable_indices(
    graph: _DiagnosticGraph,
    budget: _DiagnosticBudget,
    *,
    start_index: int | None = None,
) -> tuple[int, ...]:
    """Return reachable snapshot indices with reserve-before-work accounting."""
    initial_index = graph.initial_index if start_index is None else start_index
    if initial_index is None:
        return ()

    seen = [False] * len(graph.state_names)
    seen[initial_index] = True
    budget.reserve_result(stage="reachability.result")
    queue: deque[int] = deque([initial_index])
    while queue:
        current_index = queue.popleft()
        budget.reserve_work(stage="reachability.visit")
        for edge_index in graph.forward[current_index]:
            budget.reserve_work(stage="reachability.edge")
            next_index = graph.edges[edge_index].to_index
            if not seen[next_index]:
                budget.reserve_result(stage="reachability.result")
                seen[next_index] = True
                queue.append(next_index)
    return tuple(index for index, is_seen in enumerate(seen) if is_seen)


def _strongly_connected_components(*args: object, **kwargs: object) -> object:
    """Reserved for the strict-RED SCC contract implemented in Plan 19-03."""
    raise NotImplementedError("SCC diagnostics are implemented in Plan 19-03")


def _structural_depth(*args: object, **kwargs: object) -> object:
    """Reserved for the strict-RED depth contract implemented in Plan 19-03."""
    raise NotImplementedError("depth diagnostics are implemented in Plan 19-03")


def _sparse_adjacency(*args: object, **kwargs: object) -> object:
    """Reserved for the strict-RED sparse contract implemented in Plan 19-03."""
    raise NotImplementedError("sparse diagnostics are implemented in Plan 19-03")


def _dense_adjacency(*args: object, **kwargs: object) -> object:
    """Reserved for the strict-RED dense contract implemented in Plan 19-03."""
    raise NotImplementedError("dense diagnostics are implemented in Plan 19-03")


def _generate_paths(*args: object, **kwargs: object) -> object:
    """Reserved for the strict-RED path contract implemented in Plan 19-03."""
    raise NotImplementedError("path diagnostics are implemented in Plan 19-03")
