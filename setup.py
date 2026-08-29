import os
from pathlib import Path
import sys

from setuptools import setup

# PEP 517 can execute setup.py without first adding the source archive root to
# sys.path, so make the bundled setup-time tools importable from an unpacked
# sdist as well as from a repository checkout.
_SETUP_ROOT = Path(__file__).resolve().parent
if str(_SETUP_ROOT) not in sys.path:
    sys.path.insert(0, str(_SETUP_ROOT))

from tools.build_modes import BuildMode, resolve_build_mode  # noqa: E402

# mypyc selective compilation — only core.py is compiled.
# conditions.py and condition_templates.py stay uncompiled so users can
# subclass Condition from interpreted Python.
#
# All other package metadata (name, version, deps, package discovery) lives
# in pyproject.toml — this file exists solely for ext_modules.
#
# The C extension is OPTIONAL. FAST_FSM_BUILD_MODE accepts auto, pure, and
# compiled intent; FAST_FSM_PURE_PYTHON=1 remains a compatibility alias for
# pure. Auto and compiled retain the existing optional fallback in this phase.
# Invalid selector values are resolved before this fallback so they fail closed.
build_mode = resolve_build_mode(os.environ)
ext_modules = []
if build_mode is not BuildMode.PURE:
    try:
        from mypyc.build import mypycify

        ext_modules = mypycify(
            ["src/fast_fsm/core.py"],
            opt_level="3",
            debug_level="1",
            separate=False,
            multi_file=False,
        )
    except Exception as exc:
        import warnings

        warnings.warn(
            f"mypyc compilation unavailable ({exc}); "
            "installing fast_fsm as pure Python (slower but fully functional).",
            stacklevel=1,
        )

setup(ext_modules=ext_modules)
