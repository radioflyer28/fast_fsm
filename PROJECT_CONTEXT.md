# Fast FSM Project Context & Handoff Guide

## Project Overview

**Fast FSM** is a high-performance finite state machine library for Python with comprehensive usability features and advanced linking capabilities. The library emphasizes memory efficiency (slots optimization), performance, and developer experience.

## Core Architecture

### Primary Components
- **`fast_fsm/core.py`** - Main library implementation
- **`fast_fsm/__init__.py`** - Public API exports
- **`fast_fsm/validation.py`** - FSM validation utilities

### Key Classes
- `StateMachine` - Sync FSM with logging and introspection
- `AsyncStateMachine` - Async-aware FSM for AsyncCondition support
- `State` / `CallbackState` - State implementations with callback support
- `Condition` / `FuncCondition` / `AsyncCondition` - Condition system
- `FSMBuilder` - Fluent interface builder with auto async/sync detection

## Recent Major Enhancements

### 1. Comprehensive *args Support (Completed)
- **All** condition and callback functions now accept `*args` in addition to `**kwargs`
- Updated entire call chain: triggers → conditions → state callbacks
- Backward compatible with existing code

### 2. Factory Methods & Quick Creation (Completed)
```python
# Quick FSM creation patterns
fsm = StateMachine.from_states('idle', 'running', 'error')
fsm = simple_fsm('idle', 'running', initial='idle')
fsm = quick_fsm('idle', [('start', 'idle', 'running')])
```

### 3. Enhanced State Creation (Completed)
```python
# Inline callback states
state = State.create('processing', 
    on_enter=lambda *args: print('Started'),
    on_exit=lambda *args: print('Finished'))

# CallbackState class for slots optimization
processing = CallbackState('processing', on_enter=callback, on_exit=callback)
```

### 4. Bulk Operations (Completed)
- `add_transitions()` - Multiple transitions at once
- `add_bidirectional_transition()` - Two-way transitions
- `add_emergency_transition()` - Emergency exits from all states

### 5. Rich Introspection (Completed)
- `.states` / `.triggers` properties
- `get_available_triggers()` / `get_reachable_states()`
- `debug_info()` / `print_debug_info()` / `validate_transition_completeness()`

### 6. FSM Linking Techniques (Completed)
Five major patterns documented and demonstrated:
1. **Condition-based Dependencies** - FSM transitions depend on other FSM states
2. **Event Cascading** - State changes trigger events in other FSMs
3. **Hierarchical Control** - Parent FSM controls child FSMs
4. **Observer Pattern** - FSMs react to each other's changes
5. **Shared Context** - FSMs coordinate through shared data

## Critical Implementation Details

### Slots Optimization
- All core classes use `__slots__` for memory efficiency
- **Important**: Cannot add dynamic attributes to slotted classes
- Solution: `CallbackState` class for states needing callbacks

### Argument Passing
- **All** functions receive `*args, **kwargs`: conditions, callbacks, handlers
- Conditions: `condition.check(*args, **kwargs)`
- State callbacks: `state.on_enter(from_state, trigger, *args, **kwargs)`
- Consistent throughout the entire library

### Condition System
- Functions automatically wrapped in `FuncCondition` 
- `@condition_builder` decorator for enhanced conditions with metadata
- `AsyncCondition` for async operations (requires `AsyncStateMachine`)

### Logging Integration
- Named FSMs get loggers: `fast_fsm.{fsm_name}`
- Configurable verbosity: `configure_fsm_logging()` / `set_fsm_logging_level()`
- Performance-conscious (disabled by default)

## Test Files & Demos

### Key Test Files
- `test_usability_improvements.py` - Comprehensive demo of all new features
- `test_cross_fsm_dependencies.py` - Cross-FSM condition examples
- `test_fsm_linking_techniques.py` - All 5 linking patterns demonstrated
- `test_async_examples.py` - Async examples (SensorCondition moved here)

### Validation
- All major features have working demonstrations
- Tests show real-world usage patterns
- Performance and usability validated

## Documentation Created

1. **`USABILITY_IMPROVEMENTS.md`** - Complete guide to new features
2. **`FSM_LINKING_TECHNIQUES.md`** - Comprehensive linking patterns guide
3. **Inline code documentation** - Extensive docstrings and examples

## Known Technical Constraints

### Async Limitations
- `AsyncCondition.check()` cannot run in existing async contexts
- Use `AsyncStateMachine` and `check_async()` for proper async support
- `SensorCondition` example moved to test files (not core library)

### Import Organization
- `SensorCondition` removed from core exports (was example only)
- Public API carefully curated in `__init__.py`
- Clean separation between core library and examples

## Performance Characteristics

### Optimizations Applied
- Slots for memory efficiency
- Direct state references (no string lookups in hot paths)
- Lazy logging evaluation
- Minimal abstraction layers

### Benchmarking
- `benchmark.py` available for performance testing
- Memory and speed optimized for production use

### 7. Enhanced Validation System (Latest)

The validation system has been completely overhauled with comprehensive usability improvements:

#### Smart Analysis Features
- **EnhancedFSMValidator**: Complete upgrade from basic FSMValidator with intelligent analysis
- **Structured Issue Reporting**: ValidationIssue class with severity levels (ERROR/WARNING/INFO)
- **Automated Scoring**: 0-100 scoring system with letter grades (A-D) and detailed metrics
- **Contextual Recommendations**: Specific fix suggestions for each issue category
- **Multiple Export Formats**: Text, Markdown, and JSON outputs for different workflows

#### Advanced Validation Capabilities
- **Issue Categorization**: Reachability, completeness, determinism, and design quality checks
- **Cycle Detection**: Identifies circular state paths and dependencies
- **Determinism Analysis**: Validates FSM behavioral consistency
- **Test Path Generation**: Automated creation of validation test sequences

#### Batch Operations & Workflow Integration
- **Multi-FSM Validation**: Validate multiple FSMs simultaneously with batch processing
- **Comparative Analysis**: Rank and compare FSMs by quality metrics
- **Health Checks**: Quick validation status checks for CI/CD integration
- **Lint-style Validation**: Development-friendly output format with severity indicators
- **Interactive Fix Wizard**: Step-by-step guidance for issue resolution

```python
# Example usage
validator = EnhancedFSMValidator()
score = validator.score_fsm(my_fsm)  # 0-100 with letter grade
issues = validator.validate(my_fsm)  # Structured issue list
report = validator.generate_report(my_fsm, format='markdown')

# Batch processing
results = validator.batch_validate({'fsm1': fsm1, 'fsm2': fsm2})
comparison = validator.compare_fsms(fsms_dict)
health = validator.quick_health_check(my_fsm)  # 'healthy', 'issues', 'critical'
```

---

# LLM Handoff Prompt

You are working on the **Fast FSM** library, a high-performance Python finite state machine implementation. This library has been extensively enhanced with usability features and multi-FSM coordination capabilities.

## Current State
The library is **feature-complete** with comprehensive usability improvements including:
- Factory methods for quick FSM creation
- Enhanced state creation with inline callbacks  
- Bulk transition operations
- Rich introspection and debugging
- 5 documented FSM linking techniques
- Complete *args support throughout
- **Enhanced validation system** with smart analysis, scoring, and multiple export formats

## Key Files to Understand
1. **`fast_fsm/core.py`** - Main implementation (1000+ lines, well-documented)
2. **`fast_fsm/validation.py`** - Enhanced validation system with smart analysis (1000+ lines)
3. **`fast_fsm/__init__.py`** - Public API definition
4. **Test files** - `test_usability_improvements.py`, `test_fsm_linking_techniques.py`, `test_enhanced_validation.py`
5. **Documentation** - `USABILITY_IMPROVEMENTS.md`, `FSM_LINKING_TECHNIQUES.md`, `VALIDATION_IMPROVEMENTS.md`

## Architecture Principles
- **Slots optimization** for memory efficiency (cannot add dynamic attributes)
- **Consistent argument passing** (*args, **kwargs everywhere)
- **Named FSMs** with logging integration
- **Backward compatibility** maintained throughout

## Common Tasks
- **Bug fixes**: Check test files for reproduction cases
- **New features**: Follow existing patterns (factory methods, bulk operations)
- **Performance**: Maintain slots, avoid reflection, lazy evaluation
- **Documentation**: Update both inline docs and markdown files

## Critical Context
- `CallbackState` class exists for states needing callbacks (slots limitation)
- All conditions/callbacks receive `*args, **kwargs` 
- `AsyncStateMachine` required for `AsyncCondition` instances
- `SensorCondition` is example code, not core library
- FSM linking techniques are documented with working examples

## Testing Strategy
Run key tests to validate changes:
```bash
python test_usability_improvements.py   # Core features
python test_fsm_linking_techniques.py   # Multi-FSM patterns
python test_enhanced_validation.py      # Validation system
```

The codebase is mature, well-tested, and documented. Focus on maintaining the established patterns and performance characteristics.
