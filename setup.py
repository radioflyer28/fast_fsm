from mypyc.build import mypycify
from setuptools import setup

# mypyc selective compilation — only core.py is compiled.
# conditions.py and condition_templates.py stay uncompiled so users can
# subclass Condition from interpreted Python.
#
# All other package metadata (name, version, deps, package discovery) lives
# in pyproject.toml — this file exists solely for ext_modules.
setup(
    ext_modules=mypycify(
        ["src/fast_fsm/core.py"],
        opt_level="3",
        debug_level="1",
        separate=False,
        multi_file=False,
    ),
)