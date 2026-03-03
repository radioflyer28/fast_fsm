# 📚 Fast FSM Documentation Index

**Welcome to Fast FSM!** This guide helps you find the right documentation for your needs.

## 🚀 Getting Started (Choose Your Path)

### 🆕 **Brand New to Fast FSM?**
**Start here:** [Quick Start Guide](QUICK_START.md) ⏱️ *5 minutes*
- Get running immediately with copy-paste examples
- Covers 80% of common use cases
- Perfect for prototyping and MVP development

### 🎓 **Want to Learn Systematically?**
**Go here:** [Tutorial Mode](TUTORIAL.md) ⏱️ *20-60 minutes*
- Progressive learning from beginner to expert
- 4 difficulty levels with clear goals
- Hands-on examples for each concept
- Performance tips and best practices

### 📖 **Need Complete Reference?**
**Read this:** [Main README](README.md) ⏱️ *Complete reference*
- Full API documentation
- All features and examples
- Performance benchmarks
- Architecture details

## 🎯 Documentation by Use Case

### **I want to...**

| Goal | Documentation | Time | Performance Notes |
|------|---------------|------|-------------------|
| **Build my first FSM** | [Quick Start](QUICK_START.md) | 5 min | O(1) operations |
| **Learn step by step** | [Tutorial Mode](TUTORIAL.md) | 20-60 min | Progressive complexity |
| **See all features** | [Main README](README.md) | Reference | Complete API |
| **Advanced patterns** | [Usability Guide](USABILITY_IMPROVEMENTS.md) | 15 min | Production patterns |
| **Connect multiple FSMs** | [FSM Linking](FSM_LINKING_TECHNIQUES.md) | 10 min | Multi-FSM coordination |
| **Validate complex FSMs** | [Main README - Validation](README.md#validation-guide) | 5 min | Design-time analysis |
| **Optimize performance** | [Performance Demo](performance_demo.py) | 3 min | Live benchmarks |

## 🏃‍♂️ Quick Reference by Experience Level

### 🟢 **Beginner** (New to FSMs or Fast FSM)
1. **[Quick Start Guide](QUICK_START.md)** - Get running fast
2. **[Tutorial Level 1-2](TUTORIAL.md#-level-1-the-basics-5-minutes)** - Learn fundamentals
3. **Run examples:** `python verify_readme.py`

### 🟡 **Intermediate** (Know FSMs, new to Fast FSM)
1. **[Quick Start - Common Patterns](QUICK_START.md#-common-patterns-2-minutes)** - See the API
2. **[Tutorial Level 2-3](TUTORIAL.md#-level-2-adding-control-10-minutes)** - Advanced features
3. **[Usability Guide](USABILITY_IMPROVEMENTS.md)** - Production patterns

### 🟠 **Advanced** (Building production systems)
1. **[Tutorial Level 4](TUTORIAL.md#-level-4-expert-features-20-minutes)** - Expert features
2. **[FSM Linking Techniques](FSM_LINKING_TECHNIQUES.md)** - Multi-FSM patterns
3. **[Performance Demo](performance_demo.py)** - Optimization techniques
4. **[Main README - Architecture](README.md#%EF%B8%8F-architecture--design)** - Design principles

### 🔴 **Expert** (High-performance systems)
1. **[Performance characteristics](README.md#performance-characteristics-by-operation)** - O(n) complexity
2. **[Core source code](src/fast_fsm/core.py)** - Implementation details
3. **[Validation system](src/fast_fsm/validation.py)** - Design-time analysis
4. **Benchmarking:** `python benchmark.py`

## 📊 Performance Reference

### **Quick Performance Facts**
- **Throughput:** ~250,000 transitions/sec
- **Memory:** ~0.2KB base + 32 bytes/state + 64 bytes/transition
- **Complexity:** O(1) for all core operations
- **Efficiency:** 1000x better memory than dict-based alternatives

### **Performance by Operation**
| Operation | Complexity | Typical Speed | Memory Impact |
|-----------|------------|---------------|---------------|
| `StateMachine()` | O(1) | Instant | ~0.2KB base |
| `add_state()` | O(1) | Instant | +32 bytes |
| `add_transition()` | O(1) | Instant | +64 bytes |
| `trigger()` | O(1) | ~250K/sec | No allocation |
| `can_trigger()` | O(1) | ~500K/sec | No allocation |

**Verify these claims:** Run `python performance_demo.py`

## 🔧 Practical Examples

### **By Domain**
- **Web APIs:** [Tutorial Level 2](TUTORIAL.md#step-21-conditional-transitions) (validation patterns)
- **Game AI:** [Quick Start - Game Character](QUICK_START.md#game-character-ai) (state callbacks)
- **IoT Devices:** [Tutorial Level 4](TUTORIAL.md#step-41-async-state-machines) (async sensors)
- **Trading Systems:** [Performance Demo](performance_demo.py) (optimization focus)
- **Workflow Engines:** [Tutorial Level 3](TUTORIAL.md#step-32-builder-pattern-for-complex-fsms) (builder pattern)

### **By Pattern**
- **Simple State Machine:** [Quick Start - Traffic Light](QUICK_START.md#your-first-fsm-30-seconds)
- **Conditional Logic:** [Tutorial Level 2](TUTORIAL.md#step-21-conditional-transitions)
- **State Callbacks:** [Quick Start - State Callbacks](QUICK_START.md#pattern-3-state-callbacks)
- **Async Operations:** [Tutorial Level 4](TUTORIAL.md#step-41-async-state-machines)
- **Complex Construction:** [Tutorial Level 3](TUTORIAL.md#step-32-builder-pattern-for-complex-fsms)
- **Multiple FSMs:** [FSM Linking Guide](FSM_LINKING_TECHNIQUES.md)

## 🛠️ Development Workflow

### **Prototyping Phase**
1. Use [Quick Start](QUICK_START.md) patterns
2. `simple_fsm()` for basic needs
3. `StateMachine.quick_build()` for transitions

### **Development Phase**  
1. Switch to [Tutorial Level 3](TUTORIAL.md#-level-3-advanced-patterns-15-minutes) patterns
2. Use `FSMBuilder` for complex FSMs
3. Add conditions and callbacks

### **Production Phase**
1. Apply [Tutorial Level 4](TUTORIAL.md#-level-4-expert-features-20-minutes) optimizations
2. Use validation: `validate_fsm()`
3. Monitor performance: `python performance_demo.py`
4. Consider [FSM Linking](FSM_LINKING_TECHNIQUES.md) for scaling

## 🧪 Testing & Validation

### **During Development**
```bash
# Verify all examples work
python verify_readme.py

# Run comprehensive tests  
python -m pytest tests/

# Performance validation
python performance_demo.py
```

### **For Production**
```python
# Validate FSM design
from fast_fsm.validation import validate_fsm
validator = validate_fsm(your_fsm)
issues = validator.validate()

# Generate test scenarios
test_paths = validator.generate_test_paths()
```

## 📚 Complete File Index

| File | Purpose | Target Audience | Time |
|------|---------|-----------------|------|
| **[QUICK_START.md](QUICK_START.md)** | Get running fast | Everyone | 5 min |
| **[TUTORIAL.md](TUTORIAL.md)** | Systematic learning | Beginners-Experts | 20-60 min |
| **[README.md](README.md)** | Complete reference | Reference use | As needed |
| **[USABILITY_IMPROVEMENTS.md](USABILITY_IMPROVEMENTS.md)** | Advanced patterns | Production users | 15 min |
| **[FSM_LINKING_TECHNIQUES.md](FSM_LINKING_TECHNIQUES.md)** | Multi-FSM systems | Advanced users | 10 min |
| **[performance_demo.py](performance_demo.py)** | Live benchmarks | Performance focus | 3 min |
| **[src/fast_fsm/core.py](src/fast_fsm/core.py)** | Implementation | Library developers | Reference |

## 🎯 Next Steps

**Choose your starting point:**

- **🚀 Just want to try it?** → [Quick Start Guide](QUICK_START.md)
- **🎓 Want to learn properly?** → [Tutorial Mode](TUTORIAL.md)  
- **📖 Need specific info?** → [Main README](README.md)
- **⚡ Care about performance?** → `python performance_demo.py`

**Happy state machining!** 🚀

---

*This documentation index is designed to get you to the right information quickly. All documents include performance notes and complexity information where relevant.*