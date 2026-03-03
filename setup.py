from mypyc.build import mypycify
from setuptools import setup

# Compile core FSM logic while keeping condition base classes uncompiled
setup(
    name="fast_fsm",
    version="0.1.0",
    description="A high-performance FSM library with selective mypyc compilation",
    ext_modules=mypycify([
            # Compile core.py for performance but keep conditions.py uncompiled for inheritance
            "src/fast_fsm/core.py"
        ],
        opt_level="3",
        debug_level="1",
        separate=False,
        multi_file=False
    ),
    packages=["fast_fsm"],
    install_requires=["mypy>=1.11.2", "setuptools", "wheel"],
)