"""Shared build-mode selection for Fast FSM packaging commands."""

from __future__ import annotations

from enum import Enum
from typing import Mapping


class BuildMode(str, Enum):
    """The requested packaging intent for optional mypyc compilation."""

    AUTO = "auto"
    PURE = "pure"
    COMPILED = "compiled"


_BUILD_MODE_ENV = "FAST_FSM_BUILD_MODE"
_LEGACY_PURE_ENV = "FAST_FSM_PURE_PYTHON"


def _invalid_value(name: str, value: str, valid_values: str) -> ValueError:
    return ValueError(f"Invalid {name}={value!r}. Expected {valid_values}.")


def resolve_build_mode(environ: Mapping[str, str]) -> BuildMode:
    """Resolve explicit and legacy build selectors without silently guessing.

    ``FAST_FSM_BUILD_MODE`` accepts ``auto``, ``pure``, and ``compiled``
    case-insensitively. The legacy ``FAST_FSM_PURE_PYTHON`` selector accepts
    only ``0`` (no pure request) or ``1`` (pure request). A legacy value of
    ``1`` must agree with the new selector when both are present.
    """
    explicit_value = environ.get(_BUILD_MODE_ENV)
    legacy_value = environ.get(_LEGACY_PURE_ENV)

    explicit_mode: BuildMode | None = None
    if explicit_value is not None:
        normalized = explicit_value.strip().lower()
        try:
            explicit_mode = BuildMode(normalized)
        except ValueError as error:
            raise _invalid_value(
                _BUILD_MODE_ENV,
                explicit_value,
                "one of 'auto', 'pure', or 'compiled'",
            ) from error

    legacy_mode: BuildMode | None = None
    if legacy_value is not None:
        if legacy_value == "1":
            legacy_mode = BuildMode.PURE
        elif legacy_value == "0":
            legacy_mode = BuildMode.AUTO
        else:
            raise _invalid_value(_LEGACY_PURE_ENV, legacy_value, "'0' or '1'")

    if explicit_mode is None:
        return legacy_mode or BuildMode.AUTO

    if legacy_mode is BuildMode.PURE and explicit_mode is not BuildMode.PURE:
        raise ValueError(
            "Conflicting build selectors: "
            f"{_BUILD_MODE_ENV}={explicit_value!r} and "
            f"{_LEGACY_PURE_ENV}={legacy_value!r}."
        )
    if legacy_mode is BuildMode.AUTO and explicit_mode is BuildMode.PURE:
        raise ValueError(
            "Conflicting build selectors: "
            f"{_BUILD_MODE_ENV}={explicit_value!r} and "
            f"{_LEGACY_PURE_ENV}={legacy_value!r}."
        )

    return explicit_mode
