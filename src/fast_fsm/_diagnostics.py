"""Bounded, snapshot-backed graph diagnostics.

This interpreted private module deliberately depends only on standard-library
types.  ``core.py`` owns snapshot capture and never imports this module, keeping
diagnostics outside the compiled runtime hot path.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from .core import _GraphSnapshot


_SAFE_MARKDOWN_TEXT = frozenset(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 _.-"
)


def _escape_markdown_text(value: str) -> str:
    """Encode caller text as inert Markdown on one physical line."""
    return "".join(
        character if character in _SAFE_MARKDOWN_TEXT else f"&#x{ord(character):04X};"
        for character in value
    )


@dataclass(frozen=True, slots=True)
class DiagnosticLimits:
    """Finite, deterministic ceilings for one diagnostic operation."""

    DEFAULT_MAX_WORK: ClassVar[int] = 50_000
    DEFAULT_MAX_RESULTS: ClassVar[int] = 10_000
    DEFAULT_MAX_DENSE_CELLS: ClassVar[int] = 200_000
    DEFAULT_MAX_PATH_EXPANSIONS: ClassVar[int] = 20_000

    max_work: int = DEFAULT_MAX_WORK
    max_results: int = DEFAULT_MAX_RESULTS
    max_dense_cells: int = DEFAULT_MAX_DENSE_CELLS
    max_path_expansions: int = DEFAULT_MAX_PATH_EXPANSIONS

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

    def reserve_path_expansion(
        self, *, stage: str, amount: int = 1, maximum: int | None = None
    ) -> None:
        self._reserve(
            "max_path_expansions",
            "_path_expansion_count",
            stage,
            amount,
            limit_override=maximum,
        )

    def _reserve(
        self,
        dimension: str,
        counter_name: str,
        stage: str,
        amount: int,
        *,
        limit_override: int | None = None,
    ) -> None:
        if isinstance(amount, bool) or not isinstance(amount, int) or amount < 0:
            raise ValueError(
                "diagnostic reservation amount must be a non-negative integer"
            )
        current = getattr(self, counter_name)
        limit = getattr(self.limits, dimension)
        if limit_override is not None:
            if (
                isinstance(limit_override, bool)
                or not isinstance(limit_override, int)
                or limit_override < 0
            ):
                raise ValueError(
                    "diagnostic reservation limit must be a non-negative integer"
                )
            limit = min(limit, limit_override)
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
        reverse_stack: list[int] = [start_index]
        while reverse_stack:
            state_index = reverse_stack.pop()
            component.append(state_index)
            for edge_index in graph.reverse[state_index]:
                budget.reserve_work(stage="scc.reverse.edge")
                next_index = graph.edges[edge_index].from_index
                if not reverse_seen[next_index]:
                    budget.reserve_work(stage="scc.reverse.visit")
                    reverse_seen[next_index] = True
                    reverse_stack.append(next_index)

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


def _ordered_event_names(graph: _DiagnosticGraph) -> tuple[str, ...]:
    """Return deterministic event labels without materializing state-event cells."""
    return tuple(sorted({edge.trigger for edge in graph.edges}))


def _sparse_adjacency(
    graph: _DiagnosticGraph, budget: _DiagnosticBudget
) -> dict[str, object]:
    """Return ordered O(V+E) graph rows without constructing a dense matrix."""
    event_names = _ordered_event_names(graph)
    budget.reserve_result(stage="sparse.states", amount=len(graph.state_names))
    budget.reserve_result(stage="sparse.events", amount=len(event_names))
    budget.reserve_result(stage="sparse.edges", amount=len(graph.edges))
    event_indices = {event: index for index, event in enumerate(event_names)}
    edge_rows: list[dict[str, int | str | None]] = []
    for edge_index, edge in enumerate(graph.edges):
        budget.reserve_work(stage="sparse.edge")
        edge_rows.append(
            {
                "idx": edge_index,
                "from_state_idx": edge.from_index,
                "from_state": graph.state_names[edge.from_index],
                "to_state_idx": edge.to_index,
                "to_state": graph.state_names[edge.to_index],
                "event_idx": event_indices[edge.trigger],
                "event": edge.trigger,
                "condition": edge.condition_name,
            }
        )
    return {
        "states": graph.state_names,
        "events": event_names,
        "edges": tuple(edge_rows),
    }


def _allocate_dense_matrix(state_count: int) -> list[list[list[int]]]:
    """Allocate the compatibility matrix only after its full-cell preflight."""
    return [[[] for _ in range(state_count)] for _ in range(state_count)]


def _dense_adjacency(
    graph: _DiagnosticGraph,
    budget: _DiagnosticBudget,
    *,
    representation: str = "adjacency",
) -> object:
    """Materialize one preflighted dense compatibility representation."""
    state_names = graph.state_names
    event_names = _ordered_event_names(graph)
    state_count = len(state_names)

    if representation == "transition":
        required_cells = state_count * len(event_names)
        budget.reserve_dense_cells(
            stage="dense.transition.preflight", amount=required_cells
        )
        transition_matrix: dict[str, dict[str, list[str]]] = {
            state_name: {event_name: [] for event_name in event_names}
            for state_name in state_names
        }
        for edge in graph.edges:
            budget.reserve_work(stage="dense.transition.edge")
            budget.reserve_result(stage="dense.transition.result")
            transition_matrix[state_names[edge.from_index]][edge.trigger].append(
                state_names[edge.to_index]
            )
        return transition_matrix

    if representation != "adjacency":
        raise ValueError("unknown dense diagnostic representation")

    required_cells = state_count * state_count
    budget.reserve_dense_cells(stage="dense.adjacency.preflight", amount=required_cells)
    adjacency_matrix = _allocate_dense_matrix(state_count)
    event_indices = {event: index for index, event in enumerate(event_names)}
    transitions: list[dict[str, int | str]] = []
    for edge_index, edge in enumerate(graph.edges):
        budget.reserve_work(stage="dense.adjacency.edge")
        budget.reserve_result(stage="dense.adjacency.transition")
        transitions.append(
            {
                "idx": edge_index,
                "from_state_idx": edge.from_index,
                "from_state": state_names[edge.from_index],
                "to_state_idx": edge.to_index,
                "to_state": state_names[edge.to_index],
                "event_idx": event_indices[edge.trigger],
                "event": edge.trigger,
            }
        )
        adjacency_matrix[edge.from_index][edge.to_index].append(edge_index)
    return {
        "states": list(state_names),
        "events": list(event_names),
        "transitions": transitions,
        "matrix": adjacency_matrix,
    }


def _generate_paths(
    graph: _DiagnosticGraph,
    budget: _DiagnosticBudget,
    *,
    max_length: int = 10,
    max_paths: int = 50,
    max_expansions: int | None = None,
) -> tuple[tuple[tuple[str, str, str], ...], ...]:
    """Enumerate deterministic paths with iterative frames and bounded expansion."""
    for value in (max_length, max_paths):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ValueError("path limits must be non-negative integers")
    if max_expansions is not None and (
        isinstance(max_expansions, bool)
        or not isinstance(max_expansions, int)
        or max_expansions < 0
    ):
        raise ValueError("max_expansions must be a non-negative integer")
    if graph.initial_index is None or max_length == 0 or max_paths == 0:
        return ()

    paths: list[tuple[tuple[str, str, str], ...]] = []
    frames: list[tuple[int, int, tuple[tuple[str, str, str], ...]]] = [
        (graph.initial_index, 0, ())
    ]
    while frames and len(paths) < max_paths:
        state_index, edge_offset, path = frames.pop()
        outgoing = graph.forward[state_index]
        if len(path) >= max_length or edge_offset >= len(outgoing):
            continue

        frames.append((state_index, edge_offset + 1, path))
        edge = graph.edges[outgoing[edge_offset]]
        budget.reserve_path_expansion(stage="path.expand", maximum=max_expansions)
        budget.reserve_work(stage="path.expand")
        budget.reserve_result(stage="path.result")
        next_path = path + (
            (
                graph.state_names[edge.from_index],
                edge.trigger,
                graph.state_names[edge.to_index],
            ),
        )
        paths.append(next_path)
        if len(next_path) < max_length:
            frames.append((edge.to_index, 0, next_path))

    return tuple(paths)
