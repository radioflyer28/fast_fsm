import os

from setuptools import setup

# mypyc selective compilation — only core.py is compiled.
# conditions.py and condition_templates.py stay uncompiled so users can
# subclass Condition from interpreted Python.
#
# All other package metadata (name, version, deps, package discovery) lives
# in pyproject.toml — this file exists solely for ext_modules.
#
# The C extension is OPTIONAL. Set FAST_FSM_PURE_PYTHON=1 to skip compilation
# explicitly, or the build will fall back to pure Python automatically if
# mypyc or a C compiler is unavailable (e.g. when installed as a dependency).
ext_modules = []
if os.environ.get("FAST_FSM_PURE_PYTHON", "0") != "1":
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