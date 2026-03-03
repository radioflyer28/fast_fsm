#!/usr/bin/env python3
"""
Comprehensive test of enhanced FSM validation features
"""

from fast_fsm import (
    StateMachine, simple_fsm,
    # Enhanced validation features
    enhanced_validate_fsm, quick_health_check, validate_and_score,
    compare_fsms, batch_validate, fsm_lint
)


def create_test_fsms():
    """Create various FSMs with different quality levels for testing"""
    
    # 1. Well-designed FSM - use StateMachine.quick_build for complex transitions
    good_fsm = StateMachine.quick_build('idle', [
        ('start', 'idle', 'running'),
        ('pause', 'running', 'paused'),
        ('resume', 'paused', 'running'), 
        ('stop', 'running', 'idle'),
        ('stop', 'paused', 'idle'),
        ('error', 'running', 'error'),
        ('reset', 'error', 'idle')
    ], name='GoodFSM')
    
    # 2. FSM with issues
    problematic_fsm = simple_fsm('idle', 'running', 'error', 'orphaned', 
                                initial='idle', name='ProblematicFSM')
    problematic_fsm.add_transitions([
        ('start', 'idle', 'running'),
        ('error', 'running', 'error'),
        # Missing: error recovery, orphaned state never reached
    ])
    
    # 3. Overly complex FSM
    complex_fsm = StateMachine.from_states(
        'state1', 'state2', 'state3', 'state4', 'state5', 
        'state6', 'state7', 'state8', 'state9', 'state10',
        initial='state1', name='ComplexFSM'
    )
    # Add many transitions
    for i in range(1, 10):
        for j in range(i+1, 11):
            complex_fsm.add_transition(f'event_{i}_{j}', f'state{i}', f'state{j}')
    
    # 4. Minimal FSM
    minimal_fsm = StateMachine.from_states('only_state', name='MinimalFSM')
    
    return good_fsm, problematic_fsm, complex_fsm, minimal_fsm


def test_enhanced_validation():
    """Test enhanced validation features"""
    print("🚀 Enhanced FSM Validation Features Demo")
    print("=" * 60)
    
    good_fsm, problematic_fsm, complex_fsm, minimal_fsm = create_test_fsms()
    
    # Test 1: Enhanced individual validation
    print("1️⃣ Enhanced Individual Validation")
    print("-" * 40)
    
    validator = enhanced_validate_fsm(problematic_fsm)
    validator.print_enhanced_report(show_details=True)
    
    # Test 2: Quick health checks
    print("\n2️⃣ Quick Health Checks")
    print("-" * 40)
    
    fsms = [good_fsm, problematic_fsm, complex_fsm, minimal_fsm]
    for fsm in fsms:
        health = quick_health_check(fsm)
        health_icon = {"healthy": "✅", "issues": "⚠️", "critical": "❌"}[health]
        print(f"{health_icon} {fsm.name}: {health}")
    
    # Test 3: Validation scores
    print("\n3️⃣ Validation Scores")
    print("-" * 40)
    
    for fsm in fsms:
        score = validate_and_score(fsm)
        print(f"📊 {fsm.name}: {score['overall_score']}/100 "
              f"(Grade: {score['grade']}, Status: {score['status']})")
        if score['top_recommendations']:
            print(f"   💡 Top fix: {score['top_recommendations'][0]}")
    
    # Test 4: FSM Comparison
    print("\n4️⃣ FSM Comparison")
    print("-" * 40)
    
    comparison = compare_fsms(*fsms)
    print(f"🏆 Best FSM: {comparison['best_fsm']}")
    print(f"📈 Average Score: {comparison['comparison_metrics']['avg_score']:.1f}")
    print(f"📊 Score Range: {comparison['comparison_metrics']['score_range'][0]:.1f} - {comparison['comparison_metrics']['score_range'][1]:.1f}")
    
    print("\n🏅 Rankings:")
    for i, (name, score) in enumerate(comparison['rankings'], 1):
        medal = ["🥇", "🥈", "🥉", "🏅"][min(i-1, 3)]
        print(f"  {medal} {i}. {name}: {score:.1f}/100")
    
    # Test 5: Batch validation
    print("\n5️⃣ Batch Validation")
    print("-" * 40)
    
    validators = batch_validate(*fsms, show_summary=True)
    
    # Test 6: Export capabilities
    print("\n6️⃣ Export Capabilities")
    print("-" * 40)
    
    validator = enhanced_validate_fsm(problematic_fsm)
    
    print("📄 Markdown Export Preview:")
    markdown_report = validator.export_report('markdown')
    print(markdown_report[:300] + "..." if len(markdown_report) > 300 else markdown_report)
    
    print("\n📄 JSON Export Preview:")
    json_report = validator.export_report('json')
    print(json_report[:200] + "..." if len(json_report) > 200 else json_report)
    
    # Test 7: FSM Linting
    print("\n7️⃣ FSM Linting")
    print("-" * 40)
    
    print("Linting problematic FSM:")
    fsm_lint(problematic_fsm, fix_mode=False)
    
    return validators


def test_validation_issue_analysis():
    """Test detailed issue analysis"""
    print("\n🔍 Detailed Issue Analysis")
    print("=" * 60)
    
    _, problematic_fsm, _, _ = create_test_fsms()
    validator = enhanced_validate_fsm(problematic_fsm)
    
    # Show issues by category
    print("📂 Issues by Category:")
    categories = set(issue.category for issue in validator.issues)
    for category in categories:
        issues = validator.get_issues_by_category(category)
        print(f"  {category.title()}: {len(issues)} issues")
        for issue in issues[:2]:  # Show first 2
            print(f"    • {issue.description}")
    
    # Show issues by severity
    print("\n⚡ Issues by Severity:")
    for severity in ['error', 'warning', 'info']:
        issues = validator.get_issues_by_severity(severity)
        if issues:
            print(f"  {severity.upper()}: {len(issues)} issues")
            for issue in issues[:2]:  # Show first 2
                print(f"    • {issue.description}")
    
    # Show validation metrics
    print("\n📊 Validation Metrics:")
    for key, value in validator.metrics.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.3f}")
        else:
            print(f"  {key}: {value}")


def test_advanced_features():
    """Test advanced validation features"""
    print("\n🎯 Advanced Features")
    print("=" * 60)
    
    good_fsm, problematic_fsm, _, _ = create_test_fsms()
    
    # Test cycle detection
    print("🔄 Cycle Detection:")
    validator = enhanced_validate_fsm(good_fsm)
    cycles = validator.find_cycles()
    if cycles:
        print(f"  Found {len(cycles)} cycles:")
        for i, cycle in enumerate(cycles[:3]):  # Show first 3
            print(f"    Cycle {i+1}: {' -> '.join(cycle)}")
    else:
        print("  No cycles found")
    
    # Test determinism analysis
    print("\n🎲 Determinism Analysis:")
    determinism = validator.check_determinism()
    print(f"  Deterministic: {'Yes' if determinism['is_deterministic'] else 'No'}")
    if not determinism['is_deterministic']:
        print(f"  Non-deterministic transitions: {len(determinism['non_deterministic_transitions'])}")
    
    # Test path generation
    print("\n🛤️ Test Path Generation:")
    paths = validator.generate_test_paths(max_length=3, max_paths=3)
    print(f"  Generated {len(paths)} test paths:")
    for i, path in enumerate(paths):
        path_str = " → ".join([f"{from_state}[{event}]" for from_state, event, _ in path])
        print(f"    Path {i+1}: {path_str}")


def main():
    """Run all validation enhancement tests"""
    print("🧪 Enhanced Validation Features Test Suite")
    print("=" * 70)
    
    # Run all tests
    test_enhanced_validation()
    test_validation_issue_analysis()
    test_advanced_features()
    
    print("\n" + "=" * 70)
    print("✅ All enhanced validation features demonstrated!")
    
    print("\n🎯 Key Usability Improvements:")
    print("   ✅ Smart issue detection with severity levels")
    print("   ✅ Automated recommendations and scoring")  
    print("   ✅ Multiple export formats (text, markdown, JSON)")
    print("   ✅ Batch validation and FSM comparison")
    print("   ✅ Interactive fix wizard (when applicable)")
    print("   ✅ Lint-style validation for development workflow")
    print("   ✅ Comprehensive metrics and analysis")
    print("   ✅ Quick health checks for CI/CD integration")


if __name__ == '__main__':
    main()
