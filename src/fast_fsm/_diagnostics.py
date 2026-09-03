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


def _all_strongly_connected_components(
    graph: _DiagnosticGraph, budget: _DiagnosticBudget
) -> tuple[tuple[int, ...], ...]:
    """Return all snapshot-indexed SCCs with iterative Kosaraju passes."""
    state_count = len(graph.state_names)
    forward_seen = [False] * state_count
    finish_order: list[int] = []

    for start_index in range(state_count):
        if forward_seen[start_index]:
            continue

        budget.reserve_work(stage="scc.forward.visit")
        forward_seen[start_index] = True
        stack: list[tuple[int, int]] = [(start_index, 0)]
        while stack:
            state_index, edge_offset = stack[-1]
            outgoing = graph.forward[state_index]
            if edge_offset == len(outgoing):
                finish_order.append(state_index)
                stack.pop()
                continue

            edge_index = outgoing[edge_offset]
            stack[-1] = (state_index, edge_offset + 1)
            budget.reserve_work(stage="scc.forward.edge")
            next_index = graph.edges[edge_index].to_index
            if not forward_seen[next_index]:
                budget.reserve_work(stage="scc.forward.visit")
                forward_seen[next_index] = True
                stack.append((next_index, 0))

    reverse_seen = [False] * state_count
    components: list[tuple[int, ...]] = []
    for start_index in reversed(finish_order):
        if reverse_seen[start_index]:
            continue

        budget.reserve_work(stage="scc.reverse.visit")
        reverse_seen[start_index] = True
        component: list[int] = []
        stack = [start_index]
        while stack:
            state_index = stack.pop()
            component.append(state_index)
            for edge_index in graph.reverse[state_index]:
                budget.reserve_work(stage="scc.reverse.edge")
                next_index = graph.edges[edge_index].from_index
                if not reverse_seen[next_index]:
                    budget.reserve_work(stage="scc.reverse.visit")
                    reverse_seen[next_index] = True
                    stack.append(next_index)

        components.append(tuple(sorted(component)))

    return tuple(sorted(components, key=lambda component: component[0]))


def _cyclic_component_indices(
    graph: _DiagnosticGraph, budget: _DiagnosticBudget
) -> tuple[tuple[int, ...], ...]:
    """Return every cyclic component, ordered by its first snapshot index."""
    cyclic_components: list[tuple[int, ...]] = []
    for component in _all_strongly_connected_components(graph, budget):
        if len(component) > 1:
            cyclic_components.append(component)
            continue

        state_index = component[0]
        has_self_loop = False
        for edge_index in graph.forward[state_index]:
            budget.reserve_work(stage="scc.classify.edge")
            if graph.edges[edge_index].to_index == state_index:
                has_self_loop = True
                break
        if has_self_loop:
            cyclic_components.append(component)

    return tuple(cyclic_components)


def _strongly_connected_components(
    graph: _DiagnosticGraph, budget: _DiagnosticBudget
) -> tuple[tuple[str, ...], ...]:
    """Return all and only cyclic SCC members in stable snapshot order."""
    components = _cyclic_component_indices(graph, budget)
    budget.reserve_result(
        stage="scc.membership", amount=sum(len(component) for component in components)
    )
    return tuple(
        tuple(graph.state_names[state_index] for state_index in component)
        for component in components
    )


def _structural_depth(
    graph: _DiagnosticGraph, budget: _DiagnosticBudget
) -> dict[str, str | int]:
    """Compute iterative longest depth on the SCC condensation DAG.

    A cyclic graph reports the depth between its condensed components rather than
    claiming an exponential longest-simple-path calculation inside an SCC.
    """
    components = _all_strongly_connected_components(graph, budget)
    component_index_by_state = [0] * len(graph.state_names)
    has_cycle = False
    for component_index, component in enumerate(components):
        if len(component) > 1:
            has_cycle = True
        for state_index in component:
            component_index_by_state[state_index] = component_index

    component_edges: list[list[int]] = [[] for _ in components]
    seen_component_edges: set[tuple[int, int]] = set()
    for edge in graph.edges:
        budget.reserve_work(stage="depth.condense.edge")
        source_component = component_index_by_state[edge.from_index]
        target_component = component_index_by_state[edge.to_index]
        if source_component == target_component:
            if edge.from_index == edge.to_index:
                has_cycle = True
            continue
        component_edge = (source_component, target_component)
        if component_edge not in seen_component_edges:
            seen_component_edges.add(component_edge)
            component_edges[source_component].append(target_component)

    for targets in component_edges:
        targets.sort()

    indegree = [0] * len(components)
    for targets in component_edges:
        for target_component in targets:
            budget.reserve_work(stage="depth.indegree.edge")
            indegree[target_component] += 1

    ready = deque(
        component_index
        for component_index, degree in enumerate(indegree)
        if degree == 0
    )
    topological_order: list[int] = []
    while ready:
        component_index = ready.popleft()
        budget.reserve_work(stage="depth.topological.component")
        topological_order.append(component_index)
        for target_component in component_edges[component_index]:
            budget.reserve_work(stage="depth.topological.edge")
            indegree[target_component] -= 1
            if indegree[target_component] == 0:
                ready.append(target_component)

    depths = [0] * len(components)
    for component_index in reversed(topological_order):
        budget.reserve_work(stage="depth.memo.component")
        for target_component in component_edges[component_index]:
            budget.reserve_work(stage="depth.memo.edge")
            depths[component_index] = max(
                depths[component_index], 1 + depths[target_component]
            )

    initial_component = (
        component_index_by_state[graph.initial_index]
        if graph.initial_index is not None
        else None
    )
    budget.reserve_result(stage="depth.result")
    return {
        "interpretation": (
            "condensation_dag_depth" if has_cycle else "dag_longest_path"
        ),
        "depth": 0 if initial_component is None else depths[initial_component],
    }


def _sparse_adjacency(*args: object, **kwargs: object) -> object:
    """Reserved for the strict-RED sparse contract implemented in Plan 19-03."""
    raise NotImplementedError("sparse diagnostics are implemented in Plan 19-03")


def _dense_adjacency(*args: object, **kwargs: object) -> object:
    """Reserved for the strict-RED dense contract implemented in Plan 19-03."""
    raise NotImplementedError("dense diagnostics are implemented in Plan 19-03")


def _generate_paths(*args: object, **kwargs: object) -> object:
    """Reserved for the strict-RED path contract implemented in Plan 19-03."""
    raise NotImplementedError("path diagnostics are implemented in Plan 19-03")
