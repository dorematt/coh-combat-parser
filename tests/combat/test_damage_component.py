"""
Unit tests for the DamageComponent class.

This module tests the DamageComponent class which stores and manages
damage data including tracking damage values, counts, and statistics.
"""

import pytest
from PyQt5.QtWidgets import QApplication
from combat.DamageComponent import DamageComponent


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for Qt tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def damage_component(qapp):
    """Create a basic DamageComponent instance for testing."""
    return DamageComponent("Fire", 0)


@pytest.mark.unit
@pytest.mark.data
class TestDamageComponentInitialization:
    """Test DamageComponent initialization."""

    def test_init_with_type_and_value(self, qapp):
        """Test initialization with type and value."""
        dc = DamageComponent("Cold", 50.5)
        assert dc.type == "Cold"
        assert dc.name == "Cold"
        assert dc.total_damage == 50.5
        assert dc.count == 0
        assert dc.highest_damage == 0
        assert dc.lowest_damage == 0
        assert dc.last_damage == 0

    def test_init_default_value(self, qapp):
        """Test initialization with default value."""
        dc = DamageComponent("Energy")
        assert dc.type == "Energy"
        assert dc.total_damage == 0
        assert dc.count == 0


@pytest.mark.unit
@pytest.mark.data
class TestDamageComponentAddDamage:
    """Test adding damage to DamageComponent."""

    def test_add_single_damage(self, damage_component):
        """Test adding a single damage value."""
        damage_component.add_damage("Fire", 100.0)
        assert damage_component.total_damage == 100.0
        assert damage_component.count == 1
        assert damage_component.last_damage == 100.0
        assert damage_component.highest_damage == 100.0
        assert damage_component.lowest_damage == 100.0

    def test_add_multiple_damages(self, damage_component):
        """Test adding multiple damage values."""
        damage_component.add_damage("Fire", 50.0)
        damage_component.add_damage("Fire", 75.0)
        damage_component.add_damage("Fire", 25.0)

        assert damage_component.total_damage == 150.0
        assert damage_component.count == 3
        assert damage_component.last_damage == 25.0
        assert damage_component.highest_damage == 75.0
        assert damage_component.lowest_damage == 25.0

    def test_add_damage_rounding(self, damage_component):
        """Test that damage values are rounded to 2 decimal places."""
        damage_component.add_damage("Fire", 10.123456)
        damage_component.add_damage("Fire", 20.987654)

        # Total should be rounded
        assert damage_component.total_damage == 31.11
        assert damage_component.count == 2

    def test_add_zero_damage(self, damage_component):
        """Test adding zero damage."""
        damage_component.add_damage("Fire", 0)
        assert damage_component.total_damage == 0
        assert damage_component.count == 1
        assert damage_component.highest_damage == 0
        assert damage_component.lowest_damage == 0


@pytest.mark.unit
@pytest.mark.data
class TestDamageComponentStatistics:
    """Test DamageComponent statistical methods."""

    def test_get_average_damage_with_count(self, qapp):
        """Test average damage calculation."""
        dc = DamageComponent("Smashing")
        dc.add_damage("Smashing", 100.0)
        dc.add_damage("Smashing", 200.0)
        dc.add_damage("Smashing", 150.0)

        assert dc.get_average_damage() == 150.0

    def test_get_average_damage_no_count(self, qapp):
        """Test average damage when count is zero."""
        dc = DamageComponent("Lethal", 100.0)
        # Count is 0 because we didn't call add_damage
        assert dc.get_average_damage() == 100.0

    def test_get_dps_with_duration(self, qapp):
        """Test DPS calculation with duration."""
        dc = DamageComponent("Energy")
        dc.add_damage("Energy", 500.0)

        dps = dc.get_dps(10)  # 10 second duration
        assert dps == 50.0

    def test_get_dps_zero_duration(self, qapp):
        """Test DPS calculation with zero duration."""
        dc = DamageComponent("Toxic")
        dc.add_damage("Toxic", 250.0)

        dps = dc.get_dps(0)
        assert dps == 250.0  # Returns total damage when duration is 0

    def test_get_highest_damage(self, qapp):
        """Test getting highest damage value."""
        dc = DamageComponent("Negative")
        dc.add_damage("Negative", 50.0)
        dc.add_damage("Negative", 150.0)
        dc.add_damage("Negative", 100.0)

        assert dc.get_highest_damage() == 150.0

    def test_get_lowest_damage(self, qapp):
        """Test getting lowest damage value."""
        dc = DamageComponent("Psionic")
        dc.add_damage("Psionic", 100.0)
        dc.add_damage("Psionic", 25.0)
        dc.add_damage("Psionic", 75.0)

        assert dc.get_lowest_damage() == 25.0

    def test_get_damage(self, qapp):
        """Test getting total damage."""
        dc = DamageComponent("Fire")
        dc.add_damage("Fire", 111.11)
        dc.add_damage("Fire", 222.22)

        assert dc.get_damage() == 333.33

    def test_get_last_damage(self, qapp):
        """Test getting last damage value."""
        dc = DamageComponent("Cold")
        dc.add_damage("Cold", 50.0)
        dc.add_damage("Cold", 75.0)
        dc.add_damage("Cold", 100.0)

        assert dc.get_last_damage() == 100.0

    def test_get_count(self, qapp):
        """Test getting damage count."""
        dc = DamageComponent("Energy")
        dc.add_damage("Energy", 10.0)
        dc.add_damage("Energy", 20.0)
        dc.add_damage("Energy", 30.0)

        assert dc.get_count() == 3


@pytest.mark.unit
@pytest.mark.data
class TestDamageComponentMinMaxUpdate:
    """Test min/max damage update logic."""

    def test_update_highest_from_zero(self, qapp):
        """Test updating highest damage from initial zero."""
        dc = DamageComponent("Fire")
        dc.add_damage("Fire", 50.0)

        assert dc.highest_damage == 50.0

    def test_update_highest_with_larger_value(self, qapp):
        """Test updating highest damage with larger value."""
        dc = DamageComponent("Fire")
        dc.add_damage("Fire", 50.0)
        dc.add_damage("Fire", 100.0)

        assert dc.highest_damage == 100.0

    def test_update_highest_with_smaller_value(self, qapp):
        """Test that highest damage doesn't decrease."""
        dc = DamageComponent("Fire")
        dc.add_damage("Fire", 100.0)
        dc.add_damage("Fire", 50.0)

        assert dc.highest_damage == 100.0

    def test_update_lowest_from_zero(self, qapp):
        """Test updating lowest damage from initial zero."""
        dc = DamageComponent("Cold")
        dc.add_damage("Cold", 50.0)

        assert dc.lowest_damage == 50.0

    def test_update_lowest_with_smaller_value(self, qapp):
        """Test updating lowest damage with smaller value."""
        dc = DamageComponent("Cold")
        dc.add_damage("Cold", 50.0)
        dc.add_damage("Cold", 25.0)

        assert dc.lowest_damage == 25.0

    def test_update_lowest_with_larger_value(self, qapp):
        """Test that lowest damage doesn't increase."""
        dc = DamageComponent("Cold")
        dc.add_damage("Cold", 25.0)
        dc.add_damage("Cold", 50.0)

        assert dc.lowest_damage == 25.0


@pytest.mark.unit
@pytest.mark.data
class TestDamageComponentEdgeCases:
    """Test edge cases for DamageComponent."""

    def test_large_damage_values(self, qapp):
        """Test handling very large damage values."""
        dc = DamageComponent("Fire")
        dc.add_damage("Fire", 999999.99)

        assert dc.total_damage == 999999.99
        assert dc.get_average_damage() == 999999.99

    def test_very_small_damage_values(self, qapp):
        """Test handling very small damage values."""
        dc = DamageComponent("Toxic")
        dc.add_damage("Toxic", 0.01)
        dc.add_damage("Toxic", 0.01)

        assert dc.total_damage == 0.02
        assert dc.count == 2

    def test_negative_damage_handling(self, qapp):
        """Test that negative damage can be tracked (for healing)."""
        dc = DamageComponent("Healing")
        dc.add_damage("Healing", -50.0)

        assert dc.total_damage == -50.0
        assert dc.last_damage == -50.0

    def test_get_damage_component_method(self, qapp):
        """Test get_damage_component returns self."""
        dc = DamageComponent("Fire")
        assert dc.get_damage_component() is dc
