# CoH Combat Parser - Test Suite

This directory contains comprehensive tests for the City of Heroes Combat Parser. The test suite ensures data integrity, validates parsing logic, and helps prevent regressions.

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
- [Running Tests](#running-tests)
- [Test Structure](#test-structure)
- [Writing Tests](#writing-tests)
- [Continuous Integration](#continuous-integration)
- [Code Coverage](#code-coverage)
- [Best Practices](#best-practices)

## Overview

The test suite covers:

- **Data Handling**: Tests for all data structures (Ability, Character, DamageComponent, CombatSession)
- **Pattern Matching**: Validation of regex patterns used to parse log files
- **Combat Parser**: Core parsing logic and event interpretation
- **Data Utilities**: Helper functions and data validation

### Test Framework

- **pytest**: Primary testing framework
- **pytest-cov**: Code coverage reporting
- **pytest-qt**: PyQt5 testing support
- **pytest-mock**: Mocking and fixture support

## Getting Started

### Install Test Dependencies

```bash
pip install -r requirements.txt
```

This installs all necessary testing dependencies including:
- pytest>=7.4.0
- pytest-cov>=4.1.0
- pytest-mock>=3.11.1
- pytest-qt>=4.2.0

### Verify Installation

```bash
pytest --version
```

## Running Tests

### Run All Tests

```bash
pytest
```

### Run Tests with Verbose Output

```bash
pytest -v
```

### Run Tests with Coverage Report

```bash
pytest --cov=src --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`.

### Run Specific Test Files

```bash
# Test only DamageComponent
pytest tests/combat/test_damage_component.py

# Test only LogPatterns
pytest tests/data/test_log_patterns.py
```

### Run Tests by Category

```bash
# Run only unit tests
pytest -m unit

# Run only data handling tests
pytest -m data

# Run only combat module tests
pytest -m combat
```

### Run Tests Matching a Pattern

```bash
# Run all tests with "damage" in the name
pytest -k damage

# Run all tests with "accuracy" in the name
pytest -k accuracy
```

### Run Tests and Stop at First Failure

```bash
pytest -x
```

### Run Tests with Print Statements

```bash
pytest -s
```

## Test Structure

```
tests/
├── __init__.py
├── README.md                      # This file
├── combat/                        # Combat module tests
│   ├── __init__.py
│   ├── test_ability.py           # Ability class tests
│   ├── test_character.py         # Character class tests
│   ├── test_damage_component.py  # DamageComponent class tests
│   ├── test_combat_session.py    # CombatSession class tests
│   └── test_combat_parser.py     # CombatParser class tests
└── data/                          # Data module tests
    ├── __init__.py
    ├── test_pseudopets.py         # Pseudopets module tests
    └── test_log_patterns.py       # LogPatterns regex tests
```

### Test Organization

Each test file is organized into classes that group related tests:

```python
@pytest.mark.unit
@pytest.mark.data
class TestDamageComponentInitialization:
    """Test DamageComponent initialization."""

    def test_init_with_type_and_value(self):
        # Test code here
        pass
```

## Writing Tests

### Basic Test Example

```python
import pytest
from combat.Ability import Ability

def test_ability_creation():
    """Test that an ability can be created."""
    ability = Ability("Fireball")
    assert ability.name == "Fireball"
    assert ability.count == 0
```

### Using Fixtures

Fixtures provide reusable test data:

```python
@pytest.fixture
def sample_ability():
    """Provide a sample ability for testing."""
    return Ability("Test Power")

def test_ability_usage(sample_ability):
    """Test using the fixture."""
    sample_ability.ability_used()
    assert sample_ability.count == 1
```

### Testing with PyQt5

For tests involving Qt objects, use the `qapp` fixture:

```python
@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance."""
    from PyQt5.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

def test_qt_object(qapp):
    """Test a Qt-based object."""
    from combat.Ability import Ability
    ability = Ability("Power")
    assert ability is not None
```

### Test Markers

Use markers to categorize tests:

```python
@pytest.mark.unit          # Unit test
@pytest.mark.integration   # Integration test
@pytest.mark.slow          # Slow-running test
@pytest.mark.data          # Data handling test
@pytest.mark.combat        # Combat module test
```

### Parameterized Tests

Test multiple inputs efficiently:

```python
@pytest.mark.parametrize("damage,expected", [
    (100.0, 100.0),
    (50.5, 50.5),
    (0.0, 0.0),
])
def test_damage_values(damage, expected):
    dc = DamageComponent("Fire")
    dc.add_damage("Fire", damage)
    assert dc.total_damage == expected
```

## Continuous Integration

### GitHub Actions

Tests run automatically on:
- Push to `main`, `master`, or `develop` branches
- Pull requests to these branches
- Manual workflow dispatch

The CI pipeline:
1. Tests on multiple OS (Ubuntu, Windows, macOS)
2. Tests on multiple Python versions (3.10, 3.11, 3.12)
3. Runs linting checks
4. Generates coverage reports
5. Uploads coverage to Codecov (optional)

### Viewing CI Results

Check the "Actions" tab in GitHub to see test results.

## Code Coverage

### Generate Coverage Report

```bash
pytest --cov=src --cov-report=term --cov-report=html
```

### View Coverage Report

Open `htmlcov/index.html` in a browser to see detailed coverage.

### Coverage Goals

- **Target**: 80%+ coverage for data handling modules
- **Critical Paths**: 90%+ coverage for core parsing logic
- **Documentation**: Update when adding new features

### Check Coverage for Specific Module

```bash
pytest --cov=src/combat --cov-report=term
pytest --cov=src/data --cov-report=term
```

## Best Practices

### 1. Test Naming

- Use descriptive names: `test_ability_increments_count_when_used()`
- Follow pattern: `test_<what>_<condition>_<expected_result>()`

### 2. Test Independence

- Each test should be independent
- Don't rely on test execution order
- Use fixtures for setup/teardown

### 3. Test One Thing

- Each test should verify one specific behavior
- Makes debugging easier when tests fail

### 4. Use Assertions Wisely

```python
# Good - specific assertion
assert ability.count == 1

# Better - with message
assert ability.count == 1, "Count should increment after use"
```

### 5. Test Edge Cases

Always test:
- Empty/zero values
- Negative values
- Very large values
- Boundary conditions
- Error conditions

### 6. Keep Tests Fast

- Use mocks for expensive operations
- Mark slow tests with `@pytest.mark.slow`
- Consider test execution time

### 7. Document Complex Tests

```python
def test_complex_scenario():
    """
    Test that proc damage is correctly associated with abilities
    when associating_procs setting is enabled.

    This verifies the fix for issue #123 where procs were being
    counted as separate abilities.
    """
    # Test implementation
```

## Troubleshooting

### Qt Platform Plugin Error

If you see "Could not find the Qt platform plugin":

```bash
export QT_QPA_PLATFORM=offscreen
pytest
```

### Import Errors

Ensure you're in the project root and Python path is set:

```bash
export PYTHONPATH="${PYTHONPATH}:${PWD}/src"
pytest
```

Or use pytest's built-in path handling (configured in `pytest.ini`).

### Coverage Not Working

Make sure pytest-cov is installed:

```bash
pip install pytest-cov
```

## Getting Help

- Check test output for detailed error messages
- Use `pytest --pdb` to drop into debugger on failure
- Review similar tests for examples
- Consult pytest documentation: https://docs.pytest.org/

## Contributing Tests

When contributing:

1. Write tests for new features
2. Ensure tests pass locally
3. Maintain or improve coverage
4. Follow existing patterns
5. Document complex test scenarios

## Quick Reference

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run specific file
pytest tests/combat/test_ability.py

# Run specific test
pytest tests/combat/test_ability.py::TestAbilityDamageTracking::test_add_damage_new_type

# Run tests matching pattern
pytest -k "damage"

# Run with verbose output
pytest -v

# Stop at first failure
pytest -x

# Show print statements
pytest -s

# Run marked tests
pytest -m unit
pytest -m data
pytest -m combat

# Generate HTML coverage report
pytest --cov=src --cov-report=html

# Run in parallel (requires pytest-xdist)
pytest -n auto
```
