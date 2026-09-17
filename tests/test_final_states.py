"""Behavioral contract for explicit final-state semantics."""

import pytest

from fast_fsm.core import (
    AsyncDeclarativeState,
    AsyncStateMachine,
    CallbackState,
    DeclarativeState,
    quick_fsm,
    State,
    StateMachine,
)


class _TruthyObject:
    """Fail if a final-state validator tries to coerce this instance."""

    def __bool__(self) -> bool:
        raise AssertionError("final validation must not coerce caller input")


class TestStateFinalMetadata:
    """Explicit state metadata is immutable, exact, and slotted."""

    def test_state_final_defaults_to_false_and_accepts_true_by_keyword(self) -> None:
        assert State("pending").final is False
        assert State("done", final=True).final is True

    def test_state_final_is_keyword_only(self) -> None:
        with pytest.raises(TypeError):
            State("done", True)

    @pytest.mark.parametrize("value", [1, 0, "true", _TruthyObject()])
    def test_state_final_rejects_non_bool_without_coercion(self, value: object) -> None:
        with pytest.raises(TypeError, match="final must be an exact built-in bool"):
            State("done", final=value)  # type: ignore[arg-type]

    def test_state_final_is_read_only_and_state_stays_slotted(self) -> None:
        state = State("done", final=True)

        with pytest.raises(AttributeError):
            state.final = False  # type: ignore[misc]
        with pytest.raises(AttributeError):
            _ = state.__dict__


class TestTerminationQuery:
    """Termination derives solely from the canonical current State."""

    def test_initial_final_state_is_terminated(self) -> None:
        done = State("done", final=True)
        machine = StateMachine(done)

        assert machine.current_state is done
        assert machine.is_terminated is True

    def test_async_machine_inherits_the_same_termination_query(self) -> None:
        machine = AsyncStateMachine(State("done", final=True))

        assert machine.is_terminated is True
        assert "is_terminated" not in AsyncStateMachine.__dict__

    def test_incoming_transition_to_final_state_is_terminated(self) -> None:
        idle = State("idle")
        done = State("done", final=True)
        machine = StateMachine(idle)
        machine.add_state(done)
        machine.add_transition("finish", idle, done)

        result = machine.trigger("finish")

        assert result.success is True
        assert machine.current_state is done
        assert machine.is_terminated is True


class TestFinalConstructionSurfaces:
    """Every public State constructor preserves exact immutable finality."""

    def test_state_create_preserves_callbacks_and_final_metadata(self) -> None:
        events: list[tuple[str, str, int, str]] = []

        def on_enter(
            _from_state: State | None, trigger: str, value: int, *, tag: str
        ) -> None:
            events.append(("enter", trigger, value, tag))

        def on_exit(
            _to_state: State | None, trigger: str, value: int, *, tag: str
        ) -> None:
            events.append(("exit", trigger, value, tag))

        state = State.create("done", on_enter, on_exit, final=True)

        state.on_enter(None, "finish", 1, tag="entry")
        state.on_exit(None, "reset", 2, tag="exit")

        assert state.final is True
        assert events == [
            ("enter", "finish", 1, "entry"),
            ("exit", "reset", 2, "exit"),
        ]

    def test_callback_state_preserves_callbacks_and_final_metadata(self) -> None:
        events: list[tuple[str, str]] = []
        state = CallbackState(
            "done",
            lambda _from_state, trigger, *args, **kwargs: events.append(
                ("enter", trigger)
            ),
            lambda _to_state, trigger, *args, **kwargs: events.append(
                ("exit", trigger)
            ),
            final=True,
        )

        state.on_enter(None, "finish")
        state.on_exit(None, "reset")

        assert state.final is True
        assert events == [("enter", "finish"), ("exit", "reset")]

    def test_declarative_state_surfaces_forward_final_metadata(self) -> None:
        declarative = DeclarativeState("done", "test.final", final=True)
        async_declarative = AsyncDeclarativeState(
            "async-done", "test.final", final=True
        )

        assert declarative.final is True
        assert async_declarative.final is True

    def test_all_explicit_construction_surfaces_reject_non_bool_final(self) -> None:
        with pytest.raises(TypeError, match="final must be an exact built-in bool"):
            State.create("done", final=1)  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="final must be an exact built-in bool"):
            CallbackState("done", final=1)  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="final must be an exact built-in bool"):
            DeclarativeState("done", final=1)  # type: ignore[arg-type]
        with pytest.raises(TypeError, match="final must be an exact built-in bool"):
            AsyncDeclarativeState("done", final=1)  # type: ignore[arg-type]

    def test_all_explicit_construction_surfaces_keep_final_keyword_only(self) -> None:
        with pytest.raises(TypeError):
            State.create("done", None, None, True)
        with pytest.raises(TypeError):
            CallbackState("done", None, None, True)
        with pytest.raises(TypeError):
            DeclarativeState("done", "test.final", True)
        with pytest.raises(TypeError):
            AsyncDeclarativeState("done", "test.final", True)

    def test_interpreted_subclass_can_forward_final_to_base_state(self) -> None:
        class UserState(State):
            def __init__(self, name: str, *, final: bool = False) -> None:
                super().__init__(name, final=final)

        assert UserState("done", final=True).final is True

    def test_non_final_sink_is_not_terminated(self) -> None:
        sink = State("sink")
        machine = StateMachine(sink)

        assert machine.get_available_triggers() == []
        assert machine.is_terminated is False

    def test_trigger_from_final_uses_ordinary_missing_transition_result(self) -> None:
        done = State("done", final=True)
        machine = StateMachine(done)

        result = machine.trigger("finish")

        assert result.success is False
        assert result.error is not None
        assert "No transition" in result.error
        assert result.stage == "resolution"
        assert machine.current_state is done
        assert machine.is_terminated is True


class TestFinalSourceConstructionInvariant:
    """Outgoing final-state topology is rejected at construction time."""

    @staticmethod
    def _machine_with_final_source() -> tuple[StateMachine, State, State]:
        done = State("done", final=True)
        idle = State("idle")
        machine = StateMachine(done)
        machine.add_state(idle)
        return machine, done, idle

    @pytest.mark.parametrize("target_name", ["idle", "done"])
    def test_final_source_and_self_transition_fail_with_a_fixed_error(
        self, target_name: str
    ) -> None:
        machine, done, idle = self._machine_with_final_source()
        target = done if target_name == "done" else idle
        before_version = machine._graph_version
        before_current = machine.current_state
        before_snapshot = machine._graph_snapshot()

        with pytest.raises(
            ValueError, match="^final state cannot be a transition source$"
        ):
            machine.add_transition("finish", done, target)

        assert machine._graph_version == before_version
        assert machine.current_state is before_current
        assert machine._graph_snapshot() == before_snapshot
        assert "finish" not in machine._transitions[done.name]

    def test_registered_final_source_wins_over_same_name_input_forms(self) -> None:
        machine, done, idle = self._machine_with_final_source()
        foreign_non_final = State("done")

        with pytest.raises(
            ValueError, match="^final state cannot be a transition source$"
        ):
            machine.add_transition("finish", "done", idle)
        with pytest.raises(ValueError, match="canonical registered object"):
            machine.add_transition("finish", foreign_non_final, idle)

        assert done.final is True
        assert "finish" not in machine._transitions[done.name]

    def test_batch_row_preserves_final_source_rejection_and_atomicity(self) -> None:
        """Batch mode rows reach the same final-source normalization boundary."""
        machine, done, idle = self._machine_with_final_source()
        before_version = machine._graph_version
        before_snapshot = machine._graph_snapshot()

        with pytest.raises(
            ValueError, match="^final state cannot be a transition source$"
        ):
            machine.add_transitions(
                [("finish", done, idle, None, 0, None, None, False)]
            )

        assert machine._graph_version == before_version
        assert machine._graph_snapshot() == before_snapshot

    def test_quick_factories_reject_supplied_final_sources_but_names_stay_non_final(
        self,
    ) -> None:
        done = State("done", final=True)
        idle = State("idle")
        rows = [("leave", done, idle)]

        with pytest.warns(DeprecationWarning):
            with pytest.raises(
                ValueError, match="^final state cannot be a transition source$"
            ):
                StateMachine.quick_build("done", rows)
        with pytest.warns(DeprecationWarning):
            with pytest.raises(
                ValueError, match="^final state cannot be a transition source$"
            ):
                quick_fsm("done", rows)  # type: ignore[arg-type]

        with pytest.warns(DeprecationWarning):
            by_name = StateMachine.quick_build("idle", [("finish", "idle", "done")])
        with pytest.warns(DeprecationWarning):
            from_names = StateMachine.from_states("idle", "done")

        assert by_name._states["done"].final is False
        assert from_names._states["done"].final is False


class TestFinalControlCloneAndPersistence:
    """Final metadata survives controls and strict topology persistence."""

    def test_controls_and_snapshot_v1_derive_termination_from_current_state(
        self,
    ) -> None:
        done = State("done", final=True)
        idle = State("idle")
        machine = StateMachine(done)
        machine.add_state(idle)

        assert machine.snapshot() == {"state": "done", "version": 1}
        assert machine.is_terminated is True

        machine.force_state("idle")
        assert machine.current_state is idle
        assert machine.is_terminated is False

        machine.restore({"state": "done", "version": 1})
        assert machine.current_state is done
        assert machine.is_terminated is True

        machine.reset()
        assert machine.current_state is done
        assert machine.is_terminated is True

    def test_clone_reuses_final_states_but_resets_to_its_final_initial_state(
        self,
    ) -> None:
        done = State("done", final=True)
        idle = State("idle")
        machine = StateMachine(done)
        machine.add_state(idle)
        machine.add_transition("restart", idle, done)
        machine.force_state("idle")

        clone = machine.clone()

        assert clone is not machine
        assert clone.current_state is done
        assert clone.is_terminated is True
        assert clone._states["done"] is done
        assert clone._states["idle"] is idle
        assert clone._transitions is not machine._transitions
        assert clone._transitions["idle"] is not machine._transitions["idle"]

    def test_clone_resets_to_non_final_initial_after_source_reaches_final(self) -> None:
        idle = State("idle")
        done = State("done", final=True)
        machine = StateMachine(idle)
        machine.add_state(done)
        machine.add_transition("finish", idle, done)
        assert machine.trigger("finish").success
        assert machine.is_terminated is True

        clone = machine.clone()

        assert clone.current_state is idle
        assert clone.is_terminated is False
        assert clone._states["done"] is done
        assert clone._states["done"].final is True

    def test_to_dict_emits_sorted_explicit_final_names_and_round_trips(self) -> None:
        idle = State("idle")
        zulu = State("zulu", final=True)
        alpha = State("alpha", final=True)
        machine = StateMachine(idle, name="persisted")
        machine.add_state(zulu)
        machine.add_state(alpha)
        machine.add_transition("finish", idle, alpha)

        config = machine.to_dict()
        restored = StateMachine.from_dict(config)

        assert config["final_states"] == ["alpha", "zulu"]
        assert restored._states["alpha"].final is True
        assert restored._states["zulu"].final is True
        assert restored._states["idle"].final is False
        assert restored.to_dict() == config

    def test_legacy_dictionary_omission_defaults_every_state_to_non_final(self) -> None:
        machine = StateMachine.from_dict(
            {
                "initial": "idle",
                "states": ["idle", "done"],
                "transitions": [{"trigger": "finish", "from": "idle", "to": "done"}],
            }
        )

        assert all(not state.final for state in machine._states.values())
        assert machine.to_dict()["final_states"] == []

    @pytest.mark.parametrize(
        ("final_states", "error"),
        [
            ("done", "final_states.*list"),
            (["done", "done"], "final_states.*duplicate"),
            (["missing"], "final_states.*unknown"),
            ([""], "final_states.*non-empty"),
            ([1], "final_states.*non-empty"),
            (["idle", "done", "extra"], "final_states.*too many"),
        ],
    )
    def test_from_dict_rejects_invalid_final_states_before_publication(
        self, final_states: object, error: str
    ) -> None:
        config = {
            "initial": "idle",
            "states": ["idle", "done"],
            "final_states": final_states,
            "transitions": [],
        }

        with pytest.raises((TypeError, ValueError), match=error):
            StateMachine.from_dict(config)  # type: ignore[arg-type]

    def test_from_dict_reports_the_final_source_row_without_a_candidate_escape(
        self,
    ) -> None:
        config = {
            "initial": "idle",
            "states": ["idle", "done"],
            "final_states": ["done"],
            "transitions": [{"trigger": "restart", "from": "done", "to": "idle"}],
        }

        with pytest.raises(
            ValueError,
            match="^from_dict: transition\\[0\\] final state cannot be a transition source$",
        ):
            StateMachine.from_dict(config)

    def test_async_from_dict_and_clone_preserve_type_and_final_markers(self) -> None:
        config = {
            "initial": "idle",
            "states": ["idle", "done"],
            "final_states": ["done"],
            "transitions": [{"trigger": "finish", "from": "idle", "to": "done"}],
        }
        machine = AsyncStateMachine.from_dict(config)
        clone = machine.clone()

        assert isinstance(machine, AsyncStateMachine)
        assert isinstance(clone, AsyncStateMachine)
        assert machine._states["done"].final is True
        assert clone._states["done"] is machine._states["done"]
        assert clone.is_terminated is False
