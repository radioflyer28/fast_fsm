# Fast FSM Testing Guide

## Overview

This project uses **pytest** for modern, comprehensive testing of the fast_fsm library. The test suite is designed to work with the mypyc-compiled version of the library.

## Test Structure

```
tests/
├── test_safety_kwargs.py      # Safety features for kwargs handling
├── test_basic_functionality.py # Core FSM functionality tests  
├── test_examples.py           # Legacy tests (mypyc incompatible)
├── test_performance.py        # Legacy performance tests
└── test_verify_readme.py      # Legacy README verification
```

## Running Tests

### All Modern Tests
```bash
uv run python run_tests.py
```

### Safety Tests Only
```bash
uv run python run_tests.py --safety-only
```

### Performance Tests Only  
```bash
uv run python run_tests.py --performance
```

### Direct pytest Commands
```bash
# Run all modern tests
uv run pytest tests/test_safety_kwargs.py tests/test_basic_functionality.py -v

# Run with specific markers
uv run pytest -m "unit" -v           # Unit tests only
uv run pytest -m "integration" -v    # Integration tests only  
uv run pytest -m "not slow" -v       # Skip slow tests
```

## Test Categories

### 🛡️ Safety Tests (`test_safety_kwargs.py`)

Tests the safety improvements for kwargs handling:

- **TestKwargsSanitization**: Input validation and filtering
  - Private attribute filtering (`_attr`, `__attr`) 
  - Excessive kwargs limiting (max 50)
  - Invalid key filtering (length validation)
  - Custom sanitization patterns

- **TestConditionExceptionHandling**: Exception safety
  - Condition exceptions caught and logged
  - Different exception types handled
  - FSM stability maintained during failures

- **TestSafetyIntegration**: Integration testing
  - `can_trigger()` method safety
  - Performance impact verification
  - Logging integration

- **TestRealWorldScenarios**: Real-world usage patterns
  - Aircraft scenario from benchmarks
  - Complex object handling in kwargs

### ⚙️ Basic Functionality Tests (`test_basic_functionality.py`)

Tests core FSM functionality:

- **TestBasicFunctionality**: Basic operations
  - State creation and management
  - State machine initialization
  - Simple transitions

- **TestConditionalTransitions**: Condition logic
  - Successful condition evaluation
  - Failed condition handling
  - Context data usage

- **TestErrorHandling**: Error scenarios
  - Invalid trigger handling
  - Wrong source state detection
  - `can_trigger()` validation

- **TestComplexScenarios**: Real-world examples
  - Traffic light state machine
  - Order processing workflow
  - Multiple transition targets

- **TestPerformance**: Performance characteristics
  - Large state machine handling
  - Repeated transition performance

## Test Markers

- `@pytest.mark.unit`: Unit tests (fast, isolated)
- `@pytest.mark.integration`: Integration tests (may be slower)
- `@pytest.mark.slow`: Slow tests (can be skipped for fast runs)

## Configuration

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short --strict-markers
```

### pyproject.toml
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = ["-v", "--tb=short", "--strict-markers"]
```

## mypyc Compatibility

⚠️ **Important**: Some legacy tests fail with mypyc compilation due to:
- `TypeError: interpreted classes cannot inherit from compiled`
- Inability to subclass compiled `State` and `StateMachine` classes

**Solution**: The new pytest-based tests use composition over inheritance and work perfectly with the compiled library.

## Test Coverage

Current test coverage includes:

✅ **Safety Features**
- Kwargs sanitization and validation
- Exception handling and isolation
- Security filtering (private attributes, size limits)

✅ **Core Functionality** 
- State creation and management
- Transition logic with/without conditions
- Error handling and validation

✅ **Performance**
- Large state machine operations
- Repeated transition performance
- Memory usage patterns

✅ **Real-world Scenarios**
- Aircraft collision avoidance systems
- Traffic control systems
- Order processing workflows

## Adding New Tests

When adding new tests:

1. **Use composition over inheritance** to avoid mypyc conflicts
2. **Follow the pytest class structure**: `TestFeatureName`
3. **Add appropriate markers**: `@pytest.mark.unit` or `@pytest.mark.integration`
4. **Test both success and failure paths**
5. **Include performance considerations for integration tests**

Example:
```python
class TestNewFeature:
    """Test new FSM feature"""
    
    @pytest.mark.unit
    def test_basic_functionality(self, basic_fsm):
        """Test basic feature operation"""
        fsm, initial_state, target_state = basic_fsm
        # Test implementation
        
    @pytest.mark.integration
    def test_complex_scenario(self):
        """Test feature in complex real-world scenario"""
        # Integration test implementation
```

## Continuous Integration

For CI/CD pipelines:

```bash
# Fast test run (skip slow tests)
uv run pytest -m "not slow" --tb=short

# Full test suite
uv run python run_tests.py

# Coverage report (if coverage tools added)
uv run pytest --cov=fast_fsm --cov-report=html
```