"""
FSM Validation Module for Fast FSM Library

Provides comprehensive validation capabilities for fast_fsm state machines
without adding overhead to the core FSM classes. Includes:
- Reachability analysis
- Dead state detection
- Completeness validation
- Test path generation
- Visualization support
- Interactive validation tools
- Smart validation recommendations
"""

from typing import Dict, Set, List, Tuple, Optional, Any, Callable
from collections import defaultdict, deque
import json
from .core import StateMachine


class FSMValidator:
    """
    Lightweight validator for fast_fsm StateMachine instances.
    Analyzes FSM structure without modifying the original FSM.
    """

    __slots__ = ("fsm", "states", "transitions", "events", "initial_state")

    def __init__(self, fsm: StateMachine):
        """
        Initialize validator with a fast_fsm StateMachine instance.

        Args:
            fsm: The StateMachine to validate
        """
        self.fsm = fsm
        self.states: Set[str] = set()
        self.transitions: Dict[str, Dict[str, Set[str]]] = defaultdict(
            lambda: defaultdict(set)
        )
        self.events: Set[str] = set()
        self.initial_state: str = fsm.current_state.name

        # Extract FSM structure
        self._extract_fsm_structure()

    def _extract_fsm_structure(self) -> None:
        """Extract states, transitions, and events from the FSM"""
        # Get all states
        self.states = set(self.fsm._states.keys())

        # Extract transitions from the FSM's internal structure
        for from_state, transitions in self.fsm._transitions.items():
            for trigger, entry in transitions.items():
                to_state = entry.to_state.name
                self.states.add(from_state)
                self.states.add(to_state)
                self.transitions[from_state][trigger].add(to_state)
                self.events.add(trigger)

    def get_reachable_states(self, start_state: Optional[str] = None) -> Set[str]:
        """
        Find all states reachable from the given start state.

        Args:
            start_state: Starting state (defaults to initial state)

        Returns:
            Set of reachable state names
        """
        if start_state is None:
            start_state = self.initial_state

        reachable = set()
        queue = deque([start_state])
        reachable.add(start_state)

        while queue:
            current_state = queue.popleft()
            for event in self.events:
                next_states = self.transitions[current_state].get(event, set())
                for next_state in next_states:
                    if next_state not in reachable:
                        reachable.add(next_state)
                        queue.append(next_state)

        return reachable

    def find_unreachable_states(self) -> Set[str]:
        """Find states that cannot be reached from the initial state"""
        reachable = self.get_reachable_states()
        return self.states - reachable

    def find_dead_states(self) -> Set[str]:
        """Find states with no outgoing transitions (potential dead ends)"""
        dead_states = set()
        for state in self.states:
            has_outgoing = any(
                self.transitions[state][event]
                for event in self.events
                if event in self.transitions[state]
            )
            if not has_outgoing:
                dead_states.add(state)
        return dead_states

    def find_missing_transitions(self) -> List[Tuple[str, str]]:
        """Find state-event combinations with no defined transitions"""
        missing = []
        for state in self.states:
            for event in self.events:
                if not self.transitions[state][event]:
                    missing.append((state, event))
        return missing

    def get_transition_matrix(self) -> Dict[str, Dict[str, List[str]]]:
        """
        Generate complete transition matrix showing all state-event combinations.

        Returns:
            Nested dict: {state: {event: [target_states]}}
        """
        matrix: Dict[str, Dict[str, List[str]]] = {}
        for state in self.states:
            matrix[state] = {}
            for event in self.events:
                matrix[state][event] = list(self.transitions[state][event])
        return matrix

    def validate_completeness(self) -> Dict[str, Any]:
        """
        Perform comprehensive FSM validation analysis.

        Returns:
            Dictionary containing validation results
        """
        total_transitions = sum(
            len(self.transitions[state][event])
            for state in self.states
            for event in self.events
            if event in self.transitions[state]
        )

        unreachable = self.find_unreachable_states()
        dead_states = self.find_dead_states()
        missing = self.find_missing_transitions()

        return {
            "fsm_name": f"{self.fsm.__class__.__name__}",
            "total_states": len(self.states),
            "total_events": len(self.events),
            "total_transitions": total_transitions,
            "initial_state": self.initial_state,
            "current_state": self.fsm.current_state.name,
            "unreachable_states": unreachable,
            "dead_states": dead_states,
            "missing_transitions": missing,
            "is_complete": len(missing) == 0,
            "is_reachable": len(unreachable) == 0,
            "has_dead_states": len(dead_states) > 0,
            "transition_matrix": self.get_transition_matrix(),
        }

    def generate_test_paths(
        self, max_length: int = 10, max_paths: int = 50
    ) -> List[List[Tuple[str, str, str]]]:
        """
        Generate test paths through the FSM for testing purposes.

        Args:
            max_length: Maximum length of each path
            max_paths: Maximum number of paths to generate

        Returns:
            List of paths, where each path is [(from_state, event, to_state), ...]
        """
        paths: List[List[Tuple[str, str, str]]] = []

        def dfs_paths(current_state: str, path: List[Tuple[str, str, str]], depth: int):
            if depth >= max_length or len(paths) >= max_paths:
                return

            for event in self.events:
                next_states = self.transitions[current_state].get(event, set())
                for next_state in next_states:
                    new_path = path + [(current_state, event, next_state)]
                    paths.append(new_path.copy())

                    # Continue exploring
                    if depth < max_length - 1:
                        dfs_paths(next_state, new_path, depth + 1)

        dfs_paths(self.initial_state, [], 0)
        return paths[:max_paths]

    def check_determinism(self) -> Dict[str, Any]:
        """
        Check if FSM is deterministic (at most one transition per state-event pair).

        Returns:
            Dictionary with determinism analysis results
        """
        non_deterministic = []
        for state in self.states:
            for event in self.events:
                next_states = self.transitions[state][event]
                if len(next_states) > 1:
                    non_deterministic.append((state, event))  # pragma: no cover

        return {
            "is_deterministic": len(non_deterministic) == 0,
            "non_deterministic_transitions": non_deterministic,
        }

    def find_cycles(self) -> List[List[str]]:
        """
        Find all cycles in the FSM.

        Returns:
            List of cycles, where each cycle is a list of states
        """
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs_cycles(state: str, path: List[str]):
            if state in rec_stack:
                # Found a cycle
                cycle_start = path.index(state)
                cycle = path[cycle_start:] + [state]
                cycles.append(cycle)
                return

            if state in visited:
                return

            visited.add(state)
            rec_stack.add(state)

            for event in self.events:
                next_states = self.transitions[state].get(event, set())
                for next_state in next_states:
                    dfs_cycles(next_state, path + [state])

            rec_stack.remove(state)

        for state in self.states:
            if state not in visited:
                dfs_cycles(state, [])

        return cycles

    def print_validation_report(self) -> None:
        """Print a comprehensive validation report"""
        validation = self.validate_completeness()
        determinism = self.check_determinism()
        cycles = self.find_cycles()

        print(f"🔍 FSM Validation Report: {validation['fsm_name']}")
        print("=" * 50)

        print("📊 Basic Statistics:")
        print(f"  States: {validation['total_states']}")
        print(f"  Events: {validation['total_events']}")
        print(f"  Transitions: {validation['total_transitions']}")
        print(f"  Initial State: {validation['initial_state']}")
        print(f"  Current State: {validation['current_state']}")

        print("\n✅ Completeness Analysis:")
        print(f"  Complete FSM: {'✅ Yes' if validation['is_complete'] else '❌ No'}")
        print(
            f"  All States Reachable: {'✅ Yes' if validation['is_reachable'] else '❌ No'}"
        )
        print(
            f"  Deterministic: {'✅ Yes' if determinism['is_deterministic'] else '❌ No'}"
        )
        print(
            f"  Has Dead States: {'⚠️ Yes' if validation['has_dead_states'] else '✅ No'}"
        )

        if validation["unreachable_states"]:
            print(f"\n⚠️ Unreachable States: {validation['unreachable_states']}")

        if validation["dead_states"]:
            print(f"\n⚠️ Dead States: {validation['dead_states']}")

        if validation["missing_transitions"]:
            print("\n❌ Missing Transitions:")
            for state, event in validation["missing_transitions"][:10]:  # Show first 10
                print(f"    {state} --[{event}]--> ?")
            if len(validation["missing_transitions"]) > 10:
                print(f"    ... and {len(validation['missing_transitions']) - 10} more")

        if not determinism["is_deterministic"]:  # pragma: no cover
            print("\n❌ Non-deterministic Transitions:")
            for state, event in determinism["non_deterministic_transitions"][:5]:
                targets = list(self.transitions[state][event])
                print(f"    {state} --[{event}]--> {targets}")

        if cycles:
            print(f"\n🔄 Cycles Found: {len(cycles)}")
            for i, cycle in enumerate(cycles[:3]):  # Show first 3
                print(f"    Cycle {i + 1}: {' -> '.join(cycle)}")

        print("\n" + "=" * 50)


class ValidationIssue:
    """Represents a validation issue with severity and recommendations"""

    __slots__ = (
        "severity",
        "category",
        "description",
        "location",
        "recommendation",
        "auto_fix",
    )

    def __init__(
        self,
        severity: str,
        category: str,
        description: str,
        location: Optional[str] = None,
        recommendation: str = "",
        auto_fix: Optional[Callable] = None,
    ):
        self.severity = severity  # 'error', 'warning', 'info'
        self.category = category  # 'reachability', 'completeness', 'determinism', etc.
        self.description = description
        self.location = location  # state, transition, etc.
        self.recommendation = recommendation
        self.auto_fix = auto_fix  # function to automatically fix the issue

    def __str__(self) -> str:
        severity_icons = {"error": "❌", "warning": "⚠️", "info": "ℹ️"}
        icon = severity_icons.get(self.severity, "•")
        location_str = f" ({self.location})" if self.location else ""
        return f"{icon} {self.severity.upper()}: {self.description}{location_str}"

    def __repr__(self) -> str:
        return f"ValidationIssue({self.severity}, {self.category}, {self.description})"


class EnhancedFSMValidator(FSMValidator):
    """Enhanced validator with usability improvements and smart recommendations"""

    __slots__ = ("issues", "recommendations", "metrics")

    def __init__(self, fsm: StateMachine):
        super().__init__(fsm)
        self.issues: List[ValidationIssue] = []
        self.recommendations: List[str] = []
        self.metrics: Dict[str, Any] = {}
        self._analyze_comprehensive()

    def _analyze_comprehensive(self) -> None:
        """Perform comprehensive analysis and collect issues"""
        self.issues.clear()
        self.recommendations.clear()

        # Basic structure analysis
        self._analyze_structure()
        self._analyze_reachability()
        self._analyze_completeness()
        self._analyze_determinism()
        self._analyze_complexity()
        self._generate_recommendations()

    def _analyze_structure(self) -> None:
        """Analyze basic FSM structure"""
        # Check for trivial FSMs
        if len(self.states) == 1:
            self.issues.append(
                ValidationIssue(
                    "warning",
                    "structure",
                    "FSM has only one state - consider if this is intentional",
                    recommendation="Add additional states if the system has multiple modes",
                )
            )

        # Check for isolated states
        if len(self.events) == 0:
            self.issues.append(
                ValidationIssue(
                    "error",
                    "structure",
                    "FSM has no events/triggers defined",
                    recommendation="Add transitions between states to enable state changes",
                )
            )

        # Calculate complexity metrics
        total_possible_transitions = len(self.states) * len(self.events)
        actual_transitions = sum(
            len(self.transitions[state][event])
            for state in self.states
            for event in self.events
            if event in self.transitions[state]
        )

        self.metrics.update(
            {
                "total_states": len(self.states),
                "total_events": len(self.events),
                "actual_transitions": actual_transitions,
                "possible_transitions": total_possible_transitions,
                "density": actual_transitions / max(total_possible_transitions, 1),
                "avg_transitions_per_state": actual_transitions
                / max(len(self.states), 1),
            }
        )

    def _analyze_reachability(self) -> None:
        """Enhanced reachability analysis"""
        reachable = self.get_reachable_states()
        unreachable = self.states - reachable

        for state in unreachable:
            self.issues.append(
                ValidationIssue(
                    "warning",
                    "reachability",
                    f'State "{state}" is unreachable from initial state',
                    location=state,
                    recommendation=f'Add transition path to "{state}" or remove if unnecessary',
                )
            )

        # Check for states that can reach initial state (cycles)
        can_return_to_initial = set()
        for state in reachable:
            if state != self.initial_state:
                state_reachable = self.get_reachable_states(state)
                if self.initial_state in state_reachable:
                    can_return_to_initial.add(state)

        if len(can_return_to_initial) < len(reachable) - 1:
            isolated_states = reachable - can_return_to_initial - {self.initial_state}
            for state in isolated_states:
                self.issues.append(
                    ValidationIssue(
                        "info",
                        "reachability",
                        f'State "{state}" cannot return to initial state',
                        location=state,
                        recommendation="Consider adding return path if the state should be reversible",
                    )
                )

    def _analyze_completeness(self) -> None:
        """Enhanced completeness analysis"""
        dead_states = self.find_dead_states()
        missing_transitions = self.find_missing_transitions()

        for state in dead_states:
            self.issues.append(
                ValidationIssue(
                    "warning",
                    "completeness",
                    f'State "{state}" is a dead end (no outgoing transitions)',
                    location=state,
                    recommendation="Add exit transitions or confirm this is intentional for terminal states",
                )
            )

        # Group missing transitions by type
        missing_by_state = defaultdict(list)
        for state, event in missing_transitions:
            missing_by_state[state].append(event)

        for state, events in missing_by_state.items():
            if len(events) == len(self.events):
                self.issues.append(
                    ValidationIssue(
                        "error",
                        "completeness",
                        f'State "{state}" has no defined transitions for any event',
                        location=state,
                        recommendation="Define at least one transition or remove the state",
                    )
                )
            elif len(events) > len(self.events) * 0.5:
                self.issues.append(
                    ValidationIssue(
                        "warning",
                        "completeness",
                        f'State "{state}" missing transitions for {len(events)} events: {events[:3]}...',
                        location=state,
                        recommendation="Consider adding missing transitions or using default/error transitions",
                    )
                )

    def _analyze_determinism(self) -> None:
        """Enhanced determinism analysis"""
        determinism = self.check_determinism()

        for state, event in determinism[
            "non_deterministic_transitions"
        ]:  # pragma: no cover
            targets = list(self.transitions[state][event])
            self.issues.append(
                ValidationIssue(
                    "info",
                    "determinism",
                    f"Non-deterministic transition: {state} --[{event}]--> {targets}",
                    location=f"{state}.{event}",
                    recommendation="Consider using conditions to make transitions deterministic",
                )
            )

    def _analyze_complexity(self) -> None:
        """Analyze FSM complexity and suggest improvements"""
        # High branching factor
        max_outgoing = (
            max(
                sum(1 for event in self.events if self.transitions[state][event])
                for state in self.states
            )
            if self.states
            else 0
        )

        if max_outgoing > 10:
            self.issues.append(
                ValidationIssue(
                    "info",
                    "complexity",
                    f"High branching factor detected (max {max_outgoing} transitions from one state)",
                    recommendation="Consider splitting complex states or grouping similar transitions",
                )
            )

        # Deep nesting (long paths)
        longest_path = self._find_longest_path()
        if longest_path > 20:
            self.issues.append(
                ValidationIssue(
                    "info",
                    "complexity",
                    f"Very deep FSM structure detected (longest path: {longest_path} steps)",
                    recommendation="Consider adding shortcuts or alternative paths",
                )
            )

        # Very sparse FSM
        if self.metrics["density"] < 0.1 and len(self.states) > 5:
            self.issues.append(
                ValidationIssue(
                    "info",
                    "complexity",
                    f"Sparse FSM (only {self.metrics['density']:.1%} of possible transitions defined)",
                    recommendation="Consider consolidating states or adding more transitions",
                )
            )

    def _find_longest_path(self) -> int:
        """Find the longest acyclic path in the FSM"""

        def dfs_longest(state: str, visited: Set[str]) -> int:
            if state in visited:
                return 0  # Cycle detected, stop here

            visited.add(state)
            max_depth = 0

            for event in self.events:
                next_states = self.transitions[state].get(event, set())
                for next_state in next_states:
                    depth = 1 + dfs_longest(next_state, visited.copy())
                    max_depth = max(max_depth, depth)

            return max_depth

        return dfs_longest(self.initial_state, set())

    def _generate_recommendations(self) -> None:
        """Generate smart recommendations based on analysis"""
        error_count = sum(1 for issue in self.issues if issue.severity == "error")
        warning_count = sum(1 for issue in self.issues if issue.severity == "warning")

        if error_count > 0:
            self.recommendations.append(
                f"🔴 Critical: Fix {error_count} error(s) before deploying this FSM"
            )

        if warning_count > warning_count // 2:
            self.recommendations.append(
                "🟡 Consider reviewing warning issues for better FSM design"
            )

        # Specific recommendations based on patterns
        reachability_issues = [i for i in self.issues if i.category == "reachability"]
        if len(reachability_issues) > len(self.states) * 0.3:
            self.recommendations.append(
                "🔄 Many reachability issues detected - consider redesigning state connectivity"
            )

        if self.metrics["density"] > 0.8:
            self.recommendations.append(
                "⚡ Very dense FSM - all states are highly connected. Consider if this complexity is necessary"
            )
        elif self.metrics["density"] < 0.2:
            self.recommendations.append(
                "🔗 Sparse FSM - consider adding more transitions for better state connectivity"
            )

    def get_issues_by_severity(self, severity: str) -> List[ValidationIssue]:
        """Get all issues of a specific severity level"""
        return [issue for issue in self.issues if issue.severity == severity]

    def get_issues_by_category(self, category: str) -> List[ValidationIssue]:
        """Get all issues of a specific category"""
        return [issue for issue in self.issues if issue.category == category]

    def has_critical_issues(self) -> bool:
        """Check if there are any critical (error-level) issues"""
        return any(issue.severity == "error" for issue in self.issues)

    def get_validation_score(self) -> Dict[str, Any]:
        """Calculate an overall validation score"""
        total_issues = len(self.issues)
        error_weight = sum(3 for issue in self.issues if issue.severity == "error")
        warning_weight = sum(2 for issue in self.issues if issue.severity == "warning")
        info_weight = sum(1 for issue in self.issues if issue.severity == "info")

        total_weight = error_weight + warning_weight + info_weight

        # Score from 0-100 (higher is better)
        max_possible_weight = len(self.states) * 3  # Assume worst case
        score = max(0, 100 - (total_weight / max(max_possible_weight, 1)) * 100)

        return {
            "overall_score": round(score, 1),
            "total_issues": total_issues,
            "error_count": sum(1 for issue in self.issues if issue.severity == "error"),
            "warning_count": sum(
                1 for issue in self.issues if issue.severity == "warning"
            ),
            "info_count": sum(1 for issue in self.issues if issue.severity == "info"),
            "grade": "A"
            if score >= 90
            else "B"
            if score >= 70
            else "C"
            if score >= 50
            else "D",
        }

    def export_report(self, format: str = "text") -> str:
        """Export validation report in different formats"""
        if format == "json":
            return self._export_json()
        elif format == "markdown":
            return self._export_markdown()
        else:
            return self._export_text()

    def _export_json(self) -> str:
        """Export as JSON"""
        return json.dumps(
            {
                "fsm_name": self.fsm.name,
                "validation_score": self.get_validation_score(),
                "metrics": self.metrics,
                "issues": [
                    {
                        "severity": issue.severity,
                        "category": issue.category,
                        "description": issue.description,
                        "location": issue.location,
                        "recommendation": issue.recommendation,
                    }
                    for issue in self.issues
                ],
                "recommendations": self.recommendations,
            },
            indent=2,
        )

    def _export_markdown(self) -> str:
        """Export as Markdown"""
        score = self.get_validation_score()
        lines = [
            f"# FSM Validation Report: {self.fsm.name}",
            "",
            f"**Overall Score:** {score['overall_score']}/100 (Grade: {score['grade']})",
            f"**Total Issues:** {score['total_issues']} (Errors: {score['error_count']}, Warnings: {score['warning_count']}, Info: {score['info_count']})",
            "",
            "## Metrics",
            f"- States: {self.metrics['total_states']}",
            f"- Events: {self.metrics['total_events']}",
            f"- Transitions: {self.metrics['actual_transitions']}/{self.metrics['possible_transitions']}",
            f"- Density: {self.metrics['density']:.1%}",
            "",
            "## Issues",
        ]

        for issue in self.issues:
            lines.append(f"- {issue}")
            if issue.recommendation:
                lines.append(f"  - **Fix:** {issue.recommendation}")

        if self.recommendations:
            lines.extend(["", "## Recommendations"])
            lines.extend(f"- {rec}" for rec in self.recommendations)

        return "\n".join(lines)

    def _export_text(self) -> str:
        """Export as plain text"""
        result = self.print_enhanced_report(return_string=True)
        return result if result is not None else ""

    def print_enhanced_report(
        self, show_details: bool = True, return_string: bool = False
    ) -> Optional[str]:
        """Print an enhanced validation report with recommendations"""
        score = self.get_validation_score()

        lines = []
        lines.append(f"🔍 Enhanced FSM Validation Report: {self.fsm.name}")
        lines.append("=" * 60)

        # Overall score
        grade_colors = {"A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴"}
        grade_icon = grade_colors.get(score["grade"], "⚪")
        lines.append(
            f"{grade_icon} Overall Score: {score['overall_score']}/100 (Grade: {score['grade']})"
        )

        # Quick stats
        lines.append(
            f"📊 Issues: {score['total_issues']} total "
            f"(❌ {score['error_count']} errors, ⚠️ {score['warning_count']} warnings, "
            f"ℹ️ {score['info_count']} info)"
        )

        # Metrics
        lines.append(
            f"📈 Metrics: {self.metrics['total_states']} states, "
            f"{self.metrics['total_events']} events, "
            f"{self.metrics['actual_transitions']} transitions "
            f"({self.metrics['density']:.1%} density)"
        )

        if show_details and self.issues:
            lines.append("\n🔍 Issues Found:")

            # Group by severity
            for severity in ["error", "warning", "info"]:
                severity_issues = self.get_issues_by_severity(severity)
                if severity_issues:
                    lines.append(f"\n  {severity.upper()}S:")
                    for issue in severity_issues:
                        lines.append(f"    {issue}")
                        if issue.recommendation:
                            lines.append(f"      💡 {issue.recommendation}")

        if self.recommendations:
            lines.append("\n🎯 Smart Recommendations:")
            for rec in self.recommendations:
                lines.append(f"  {rec}")

        lines.append("\n" + "=" * 60)

        report = "\n".join(lines)
        if return_string:
            return report
        else:
            print(report)
            return None

    def interactive_fix_wizard(self) -> None:  # pragma: no cover
        """Interactive wizard to help fix validation issues"""
        if not self.issues:
            print("🎉 No issues found! Your FSM is in great shape.")
            return

        print("🧙‍♂️ FSM Fix Wizard")
        print("=" * 30)

        fixable_issues = [issue for issue in self.issues if issue.auto_fix]
        if fixable_issues:
            print(f"Found {len(fixable_issues)} auto-fixable issues:")
            for i, issue in enumerate(fixable_issues):
                print(f"  {i + 1}. {issue}")

            response = input("\nWould you like me to auto-fix these issues? (y/n): ")
            if response.lower() in ["y", "yes"]:
                for issue in fixable_issues:
                    try:
                        if issue.auto_fix is not None:
                            issue.auto_fix()
                            print(f"✅ Fixed: {issue.description}")
                    except Exception as e:
                        print(f"❌ Failed to fix: {issue.description} - {e}")

        # Show manual fixes needed
        manual_issues = [issue for issue in self.issues if not issue.auto_fix]
        if manual_issues:
            print(f"\n{len(manual_issues)} issues require manual attention:")
            for issue in manual_issues[:5]:  # Show first 5
                print(f"  • {issue}")
                if issue.recommendation:
                    print(f"    💡 {issue.recommendation}")


# Enhanced convenience functions with new features


def enhanced_validate_fsm(fsm: StateMachine) -> EnhancedFSMValidator:
    """
    Create an enhanced validator with smart recommendations.

    Args:
        fsm: StateMachine instance to validate

    Returns:
        EnhancedFSMValidator instance with comprehensive analysis
    """
    return EnhancedFSMValidator(fsm)


def quick_health_check(fsm: StateMachine) -> str:
    """
    Quick health check returning a simple status.

    Args:
        fsm: StateMachine to check

    Returns:
        Health status: 'healthy', 'issues', 'critical'
    """
    validator = EnhancedFSMValidator(fsm)

    if validator.has_critical_issues():
        return "critical"
    elif len(validator.issues) > 0:
        return "issues"
    else:
        return "healthy"


def validate_and_score(fsm: StateMachine) -> Dict[str, Any]:
    """
    Validate FSM and return score with summary.

    Args:
        fsm: StateMachine to validate

    Returns:
        Dictionary with score and summary information
    """
    validator = EnhancedFSMValidator(fsm)
    score = validator.get_validation_score()

    return {
        **score,
        "status": "critical"
        if validator.has_critical_issues()
        else "needs_attention"
        if score["warning_count"] > 0
        else "good",
        "top_recommendations": validator.recommendations[:3],
    }


def compare_fsms(*fsms: StateMachine) -> Dict[str, Any]:
    """
    Compare multiple FSMs and provide analysis.

    Args:
        *fsms: Multiple StateMachine instances to compare

    Returns:
        Comparison results with rankings and insights
    """
    results: Dict[str, Any] = {}
    validators: Dict[str, Any] = {}

    for fsm in fsms:
        validator = EnhancedFSMValidator(fsm)
        validators[fsm.name] = validator
        results[fsm.name] = {
            "score": validator.get_validation_score(),
            "metrics": validator.metrics,
            "issue_count": len(validator.issues),
        }

    # Rank by score
    ranked = sorted(
        results.items(), key=lambda x: x[1]["score"]["overall_score"], reverse=True
    )

    return {
        "rankings": [(name, data["score"]["overall_score"]) for name, data in ranked],
        "best_fsm": ranked[0][0] if ranked else None,
        "comparison_metrics": {
            "avg_score": sum(
                data["score"]["overall_score"] for data in results.values()
            )
            / len(results),
            "score_range": (
                min(data["score"]["overall_score"] for data in results.values()),
                max(data["score"]["overall_score"] for data in results.values()),
            ),
            "total_issues": sum(data["issue_count"] for data in results.values()),
        },
        "detailed_results": results,
    }


# Legacy support - keep original functions but enhance them


def validate_fsm(fsm: StateMachine) -> "EnhancedFSMValidator":
    """
    Original function - now returns enhanced validator for backward compatibility.

    Args:
        fsm: StateMachine instance to validate

    Returns:
        EnhancedFSMValidator instance (backward compatible)
    """
    return EnhancedFSMValidator(fsm)


def quick_validation_report(fsm: StateMachine) -> None:
    """
    Enhanced version of the original quick report.

    Args:
        fsm: StateMachine instance to validate
    """
    validator = EnhancedFSMValidator(fsm)
    validator.print_enhanced_report()


# Additional utility functions


def batch_validate(
    *fsms: StateMachine, show_summary: bool = True
) -> Dict[str, EnhancedFSMValidator]:
    """
    Validate multiple FSMs in batch.

    Args:
        *fsms: Multiple StateMachine instances
        show_summary: Whether to print summary report

    Returns:
        Dictionary mapping FSM names to their validators
    """
    validators = {}

    for fsm in fsms:
        validators[fsm.name] = EnhancedFSMValidator(fsm)

    if show_summary:
        print("📊 Batch Validation Summary")
        print("=" * 40)

        for name, validator in validators.items():
            score = validator.get_validation_score()
            status_icon = (
                "✅"
                if score["overall_score"] >= 80
                else "⚠️"
                if score["overall_score"] >= 60
                else "❌"
            )
            print(
                f"{status_icon} {name}: {score['overall_score']}/100 ({score['total_issues']} issues)"
            )

    return validators


def fsm_lint(fsm: StateMachine, fix_mode: bool = False) -> None:
    """
    Lint-style validation with optional auto-fixing.

    Args:
        fsm: StateMachine to lint
        fix_mode: Whether to attempt auto-fixes
    """
    validator = EnhancedFSMValidator(fsm)

    print(f"🔍 Linting FSM: {fsm.name}")

    if validator.has_critical_issues():
        print("❌ Critical issues found!")
    elif len(validator.issues) == 0:
        print("✅ No issues found!")
    else:
        print(f"⚠️ {len(validator.issues)} issues found")

    # Show issues in lint format
    for issue in validator.issues:
        location = f":{issue.location}" if issue.location else ""
        print(f"  {issue.severity}{location} - {issue.description}")

    if fix_mode:
        validator.interactive_fix_wizard()


# Export the enhanced classes and functions
__all__ = [
    # Original classes
    "FSMValidator",
    # Enhanced classes
    "EnhancedFSMValidator",
    "ValidationIssue",
    # Original functions (enhanced)
    "validate_fsm",
    "quick_validation_report",
    # New convenience functions
    "enhanced_validate_fsm",
    "quick_health_check",
    "validate_and_score",
    "compare_fsms",
    "batch_validate",
    "fsm_lint",
]

# Example usage
if __name__ == "__main__":  # pragma: no cover
    from .core import State, FSMBuilder

    print("🧪 FSM Validation Module Demo")

    # Create a simple test FSM
    class TestState(State):
        pass

    idle = TestState("Idle")
    processing = TestState("Processing")
    error = TestState("Error")

    # Build a simple FSM with some issues for demonstration
    fsm = (
        FSMBuilder(idle)
        .add_state(processing)
        .add_state(error)
        .add_transition("start", "Idle", "Processing")
        .add_transition("error", "Processing", "Error")
        .add_transition("complete", "Processing", "Idle")
        # Intentionally missing: error recovery transition
        .build()
    )

    print("\nValidating test FSM...")
    quick_validation_report(fsm)

    print("\n🔧 Generating test paths...")
    validator = validate_fsm(fsm)
    test_paths = validator.generate_test_paths(max_length=4, max_paths=5)

    print("Sample test paths:")
    for i, path in enumerate(test_paths):
        print(f"  Path {i + 1}: ", end="")
        for j, (from_state, event, to_state) in enumerate(path):
            if j == 0:
                print(f"{from_state} --[{event}]--> {to_state}", end="")
            else:
                print(f" --[{event}]--> {to_state}", end="")
        print()
