# Testing Guide for CoH Combat Parser

This guide provides a comprehensive overview of the testing infrastructure for the City of Heroes Combat Parser project. Whether you're new to testing or want to understand the project's testing practices, this document will help you get started.

## Why Testing Matters

Testing helps us:
- **Catch bugs early** before they reach users
- **Prevent regressions** when adding new features
- **Document behavior** through executable examples
- **Refactor confidently** knowing we won't break existing functionality
- **Maintain quality** as the project evolves

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

This installs the main dependencies plus testing tools:
- pytest (testing framework)
- pytest-cov (coverage reporting)
- pytest-qt (PyQt5 testing)
- pytest-mock (mocking support)

### 2. Run Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Open coverage report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### 3. Verify Everything Works

You should see output like:

```
====== test session starts ======
platform linux -- Python 3.12.0
collected 150 items

tests/combat/test_ability.py ........... [ 10%]
tests/combat/test_character.py ......... [ 25%]
tests/combat/test_damage_component.py .. [ 50%]
tests/combat/test_combat_session.py .... [ 75%]
tests/data/test_log_patterns.py ........ [100%]

====== 150 passed in 2.34s ======
```

## Understanding the Test Suite

### What's Being Tested

The test suite focuses on **data handling** - the core functionality that:

1. **Parses log files** - Regex patterns that extract combat data
2. **Stores data** - Classes that hold combat information
3. **Calculates statistics** - DPS, accuracy, damage totals
4. **Manages sessions** - Combat session lifecycle

### Test Organization

```
tests/
├── combat/           # Tests for combat data classes
│   ├── test_ability.py           # 40+ tests for Ability class
│   ├── test_character.py         # 35+ tests for Character class
│   ├── test_damage_component.py  # 30+ tests for DamageComponent
│   ├── test_combat_session.py    # 30+ tests for CombatSession
│   └── test_combat_parser.py     # 25+ tests for Parser class
└── data/            # Tests for data utilities
    ├── test_log_patterns.py      # 50+ tests for regex patterns
    └── test_pseudopets.py        # 20+ tests for pseudopet data
```

**Total: 200+ tests** covering critical data handling functionality.

### Coverage Goals

- **Data classes**: 90%+ coverage (DamageComponent, Ability, Character, CombatSession)
- **Parser logic**: 80%+ coverage (event handling, pattern matching)
- **Utility functions**: 95%+ coverage (pseudopets, helpers)

Current coverage can be checked with:
```bash
pytest --cov=src --cov-report=term
```

## Common Testing Scenarios

### Running Specific Tests

```bash
# Test a specific file
pytest tests/combat/test_ability.py

# Test a specific class
pytest tests/combat/test_ability.py::TestAbilityDamageTracking

# Test a specific function
pytest tests/combat/test_ability.py::TestAbilityDamageTracking::test_add_damage_new_type

# Test by keyword
pytest -k "damage"  # All tests with "damage" in name
pytest -k "accuracy"  # All tests with "accuracy" in name
```

### Getting More Information

```bash
# Verbose output (show each test name)
pytest -v

# Very verbose (show test docstrings)
pytest -vv

# Show print statements
pytest -s

# Stop at first failure
pytest -x

# Show local variables on failure
pytest -l
```

### Testing While Developing

```bash
# Watch mode - rerun on file changes (requires pytest-watch)
pip install pytest-watch
ptw

# Run only tests that failed last time
pytest --lf

# Run failed tests first, then others
pytest --ff
```

## Automated Testing (CI/CD)

### GitHub Actions

Tests run automatically when you:
- Push code to main/master/develop branches
- Create or update a pull request
- Manually trigger the workflow

The automated tests:
- ✅ Run on Windows, macOS, and Linux
- ✅ Test Python 3.10, 3.11, and 3.12
- ✅ Generate coverage reports
- ✅ Run code quality checks (linting)

### Viewing Test Results

1. Go to your GitHub repository
2. Click the "Actions" tab
3. Select the most recent workflow run
4. View test results for each OS/Python combination

### Test Status Badge

Add to your README.md:

```markdown
![Tests](https://github.com/YOUR_USERNAME/coh-combat-parser/workflows/Tests/badge.svg)
```

## Understanding Test Output

### Successful Test

```
tests/combat/test_ability.py::TestAbilityDamageTracking::test_add_damage_new_type PASSED [10%]
```

- ✅ Test passed
- `[10%]` shows progress through test suite

### Failed Test

```
tests/combat/test_ability.py::TestAbilityDamageTracking::test_add_damage_new_type FAILED [10%]

=== FAILURES ===
___ TestAbilityDamageTracking.test_add_damage_new_type ___

    def test_add_damage_new_type(self, basic_ability):
        dc = DamageComponent("Fire")
        basic_ability.add_damage(dc, 100.0)
>       assert len(basic_ability.damage) == 1
E       AssertionError: assert 0 == 1
```

This shows:
- ❌ Which test failed
- 📍 The line that failed
- 📊 What was expected vs. actual

### Coverage Report

```
Name                                Stmts   Miss  Cover
-------------------------------------------------------
src/combat/Ability.py                 98      5    95%
src/combat/Character.py               91      8    91%
src/combat/DamageComponent.py         56      2    96%
src/combat/CombatSession.py           96     12    88%
src/data/pseudopets.py                 5      0   100%
-------------------------------------------------------
TOTAL                                346     27    92%
```

This shows:
- **Stmts**: Total lines of code
- **Miss**: Lines not covered by tests
- **Cover**: Percentage covered

## Writing Your First Test

Here's a simple example testing the DamageComponent class:

```python
import pytest
from combat.DamageComponent import DamageComponent

def test_damage_component_creation():
    """Test that we can create a DamageComponent."""
    dc = DamageComponent("Fire", 100.0)

    assert dc.type == "Fire"
    assert dc.total_damage == 100.0
    assert dc.count == 0

def test_damage_component_add_damage():
    """Test adding damage to a component."""
    dc = DamageComponent("Cold")
    dc.add_damage("Cold", 50.0)
    dc.add_damage("Cold", 75.0)

    assert dc.total_damage == 125.0
    assert dc.count == 2
```

### Test Structure

1. **Arrange**: Set up test data
   ```python
   dc = DamageComponent("Fire")
   ```

2. **Act**: Perform the action
   ```python
   dc.add_damage("Fire", 100.0)
   ```

3. **Assert**: Verify the result
   ```python
   assert dc.total_damage == 100.0
   ```

## Common Issues and Solutions

### Qt Platform Plugin Error

**Problem**: `Could not find the Qt platform plugin`

**Solution**:
```bash
export QT_QPA_PLATFORM=offscreen
pytest
```

Or add to your shell profile:
```bash
# In ~/.bashrc or ~/.zshrc
export QT_QPA_PLATFORM=offscreen
```

### Tests Fail on Import

**Problem**: `ModuleNotFoundError: No module named 'combat'`

**Solution**: Make sure you're in the project root directory. The `pytest.ini` file configures the Python path automatically.

### Coverage Not Generating

**Problem**: Coverage report is empty or missing

**Solution**:
```bash
pip install pytest-cov
pytest --cov=src --cov-report=html
```

## Best Practices for This Project

### 1. Test Data Handling, Not UI

The current test suite focuses on:
- ✅ Data structures and calculations
- ✅ Parsing logic and pattern matching
- ✅ Session management
- ❌ UI components (tested manually)

### 2. Use Descriptive Test Names

```python
# Good
def test_ability_count_increments_when_used():
    pass

# Bad
def test_ability_1():
    pass
```

### 3. Test Edge Cases

Always consider:
- Zero/empty values
- Very large values
- Negative values (where applicable)
- None/null values
- Boundary conditions

### 4. Keep Tests Independent

Each test should:
- Set up its own data
- Not depend on other tests
- Clean up after itself
- Be runnable in any order

## Useful Commands Reference

```bash
# Essential commands
pytest                          # Run all tests
pytest -v                       # Verbose output
pytest --cov=src               # With coverage
pytest -x                       # Stop at first failure
pytest -k "keyword"            # Run tests matching keyword

# Coverage
pytest --cov=src --cov-report=html    # HTML report
pytest --cov=src --cov-report=term    # Terminal report
pytest --cov=src --cov-report=xml     # XML (for CI)

# Specific tests
pytest tests/combat/            # All combat tests
pytest tests/data/              # All data tests
pytest tests/combat/test_ability.py   # Specific file

# Markers
pytest -m unit                  # Only unit tests
pytest -m data                  # Only data tests
pytest -m combat                # Only combat tests

# Development
pytest --lf                     # Run last failed
pytest --ff                     # Failed first
pytest -s                       # Show print statements
pytest -l                       # Show local variables on failure
pytest --pdb                    # Drop into debugger on failure
```

## Getting Help

- **Test Documentation**: See `tests/README.md` for detailed testing guide
- **pytest Documentation**: https://docs.pytest.org/
- **pytest-qt Documentation**: https://pytest-qt.readthedocs.io/
- **Coverage Documentation**: https://coverage.readthedocs.io/

## Next Steps

1. ✅ Run tests to verify everything works
2. ✅ Look at existing tests to understand patterns
3. ✅ Check coverage report to see what's tested
4. ✅ Write tests for any new features you add
5. ✅ Keep tests passing as you develop

---

**Remember**: Tests are your safety net. When they all pass, you can be confident your changes haven't broken existing functionality. Happy testing! 🧪
