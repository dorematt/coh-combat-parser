"""
Unit tests for the Ability class.

This module tests the Ability class which stores and manages
ability data including damage tracking, hit/miss tracking, and statistics.
"""

import pytest
from PyQt5.QtWidgets import QApplication
from combat.Ability import Ability
from combat.DamageComponent import DamageComponent


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for Qt tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def basic_ability(qapp):
    """Create a basic Ability instance for testing."""
    return Ability("Fireball")


@pytest.fixture
def proc_ability(qapp):
    """Create a proc Ability instance for testing."""
    return Ability("Fire Proc", proc=True)


@pytest.mark.unit
@pytest.mark.data
class TestAbilityInitialization:
    """Test Ability initialization."""

    def test_init_basic(self, qapp):
        """Test basic initialization."""
        ability = Ability("Lightning Bolt")
        assert ability.name == "Lightning Bolt"
        assert ability.count == 0
        assert ability.tries == 0
        assert ability.hits == 0
        assert ability.damage == []
        assert ability.proc is False
        assert ability.pet is False
        assert ability.pet_name == ""

    def test_init_with_hit_true(self, qapp):
        """Test initialization with hit=True."""
        ability = Ability("Ice Blast", hit=True)
        assert ability.tries == 1
        assert ability.hits == 1
        assert ability.count == 0

    def test_init_with_hit_false(self, qapp):
        """Test initialization with hit=False."""
        ability = Ability("Stone Fist", hit=False)
        assert ability.tries == 1
        assert ability.hits == 0

    def test_init_with_proc_true(self, qapp):
        """Test initialization with proc=True."""
        ability = Ability("Damage Proc", proc=True)
        assert ability.proc is True


@pytest.mark.unit
@pytest.mark.data
class TestAbilityDamageTracking:
    """Test Ability damage tracking functionality."""

    def test_add_damage_new_type(self, basic_ability):
        """Test adding damage of a new type."""
        dc = DamageComponent("Fire")
        basic_ability.add_damage(dc, 100.0)

        assert len(basic_ability.damage) == 1
        assert basic_ability.damage[0].type == "Fire"
        assert basic_ability.damage[0].get_damage() == 100.0

    def test_add_damage_existing_type(self, basic_ability):
        """Test adding damage to existing type."""
        dc1 = DamageComponent("Cold")
        basic_ability.add_damage(dc1, 50.0)

        dc2 = DamageComponent("Cold")
        basic_ability.add_damage(dc2, 75.0)

        # Should only have one damage component
        assert len(basic_ability.damage) == 1
        assert basic_ability.damage[0].type == "Cold"
        assert basic_ability.damage[0].get_damage() == 125.0
        assert basic_ability.damage[0].get_count() == 2

    def test_add_damage_multiple_types(self, basic_ability):
        """Test adding damage of multiple types."""
        basic_ability.add_damage(DamageComponent("Fire"), 100.0)
        basic_ability.add_damage(DamageComponent("Cold"), 50.0)
        basic_ability.add_damage(DamageComponent("Energy"), 75.0)

        assert len(basic_ability.damage) == 3
        assert basic_ability.get_total_damage() == 225.0

    def test_add_damage_proc_increments_count(self, proc_ability):
        """Test that adding damage to a proc increments count."""
        initial_count = proc_ability.count
        proc_ability.add_damage(DamageComponent("Fire"), 50.0)

        assert proc_ability.count == initial_count + 1

    def test_add_damage_non_proc_no_increment(self, basic_ability):
        """Test that adding damage to non-proc doesn't increment count."""
        initial_count = basic_ability.count
        basic_ability.add_damage(DamageComponent("Fire"), 50.0)

        assert basic_ability.count == initial_count


@pytest.mark.unit
@pytest.mark.data
class TestAbilityUsageTracking:
    """Test Ability usage and hit tracking."""

    def test_ability_used(self, basic_ability):
        """Test ability_used increments count."""
        basic_ability.ability_used()
        assert basic_ability.count == 1

        basic_ability.ability_used()
        basic_ability.ability_used()
        assert basic_ability.count == 3

    def test_ability_hit_success(self, basic_ability):
        """Test ability_hit with successful hit."""
        basic_ability.ability_hit(True)

        assert basic_ability.tries == 1
        assert basic_ability.hits == 1

    def test_ability_hit_miss(self, basic_ability):
        """Test ability_hit with miss."""
        basic_ability.ability_hit(False)

        assert basic_ability.tries == 1
        assert basic_ability.hits == 0

    def test_ability_hit_multiple(self, basic_ability):
        """Test multiple ability_hit calls."""
        basic_ability.ability_hit(True)
        basic_ability.ability_hit(True)
        basic_ability.ability_hit(False)
        basic_ability.ability_hit(True)

        assert basic_ability.tries == 4
        assert basic_ability.hits == 3


@pytest.mark.unit
@pytest.mark.data
class TestAbilityStatistics:
    """Test Ability statistical calculations."""

    def test_get_total_damage(self, qapp):
        """Test total damage calculation."""
        ability = Ability("Multi-Damage")
        ability.add_damage(DamageComponent("Fire"), 100.0)
        ability.add_damage(DamageComponent("Cold"), 50.0)
        ability.add_damage(DamageComponent("Energy"), 75.0)

        assert ability.get_total_damage() == 225.0

    def test_get_total_damage_empty(self, basic_ability):
        """Test total damage with no damage components."""
        assert basic_ability.get_total_damage() == 0

    def test_get_max_damage(self, qapp):
        """Test max damage calculation."""
        ability = Ability("Variable Damage")
        dc = DamageComponent("Fire")
        dc.add_damage("Fire", 50.0)
        dc.add_damage("Fire", 150.0)
        dc.add_damage("Fire", 100.0)
        ability.damage.append(dc)

        assert ability.get_max_damage() == 150.0

    def test_get_min_damage(self, qapp):
        """Test min damage calculation."""
        ability = Ability("Variable Damage")
        dc = DamageComponent("Cold")
        dc.add_damage("Cold", 100.0)
        dc.add_damage("Cold", 25.0)
        dc.add_damage("Cold", 75.0)
        ability.damage.append(dc)

        # Note: get_min_damage only returns the last component's min
        assert ability.get_min_damage() == 25.0

    def test_get_average_damage_with_count(self, qapp):
        """Test average damage based on count."""
        ability = Ability("Test Power")
        ability.add_damage(DamageComponent("Fire"), 100.0)
        ability.add_damage(DamageComponent("Fire"), 50.0)
        ability.count = 2

        assert ability.get_average_damage() == 75.0

    def test_get_average_damage_with_hits(self, qapp):
        """Test average damage based on hits when count is 0."""
        ability = Ability("Test Power", hit=True)
        ability.add_damage(DamageComponent("Fire"), 200.0)
        ability.ability_hit(True)

        # count is 0, so it should use hits (2)
        assert ability.get_average_damage() == 100.0

    def test_get_average_damage_zero_count_zero_damage(self, basic_ability):
        """Test average damage when both count and damage are zero."""
        assert basic_ability.get_average_damage() == 0

    def test_get_accuracy_perfect(self, qapp):
        """Test accuracy calculation with all hits."""
        ability = Ability("Accurate Power")
        ability.ability_hit(True)
        ability.ability_hit(True)
        ability.ability_hit(True)

        assert ability.get_accuracy() == 100.0

    def test_get_accuracy_partial(self, qapp):
        """Test accuracy calculation with partial hits."""
        ability = Ability("Normal Power")
        ability.ability_hit(True)
        ability.ability_hit(False)
        ability.ability_hit(True)
        ability.ability_hit(False)

        assert ability.get_accuracy() == 50.0

    def test_get_accuracy_no_hits(self, qapp):
        """Test accuracy calculation with no hits."""
        ability = Ability("Miss Power")
        ability.ability_hit(False)
        ability.ability_hit(False)

        assert ability.get_accuracy() == 0

    def test_get_accuracy_no_tries(self, basic_ability):
        """Test accuracy with no tries."""
        assert basic_ability.get_accuracy() == 0

    def test_get_dps(self, qapp):
        """Test DPS calculation."""
        ability = Ability("DPS Test")
        dc = DamageComponent("Fire")
        dc.add_damage("Fire", 100.0)
        dc.add_damage("Fire", 200.0)
        ability.damage.append(dc)

        dps = ability.get_dps(10)  # 10 second duration
        assert dps == 30.0

    def test_get_dps_multiple_types(self, qapp):
        """Test DPS with multiple damage types."""
        ability = Ability("Multi DPS")

        dc1 = DamageComponent("Fire")
        dc1.add_damage("Fire", 100.0)
        ability.damage.append(dc1)

        dc2 = DamageComponent("Cold")
        dc2.add_damage("Cold", 50.0)
        ability.damage.append(dc2)

        dps = ability.get_dps(5)  # 5 second duration
        assert dps == 30.0  # (100 + 50) / 5


@pytest.mark.unit
@pytest.mark.data
class TestAbilityGetters:
    """Test Ability getter methods."""

    def test_get_name(self, qapp):
        """Test get_name method."""
        ability = Ability("Power Name")
        assert ability.get_name() == "Power Name"

    def test_get_count(self, basic_ability):
        """Test get_count method."""
        basic_ability.ability_used()
        basic_ability.ability_used()
        assert basic_ability.get_count() == 2

    def test_get_hits(self, qapp):
        """Test get_hits method."""
        ability = Ability("Hit Test")
        ability.ability_hit(True)
        ability.ability_hit(False)
        ability.ability_hit(True)
        assert ability.get_hits() == 2

    def test_get_tries(self, qapp):
        """Test get_tries method."""
        ability = Ability("Try Test")
        ability.ability_hit(True)
        ability.ability_hit(False)
        ability.ability_hit(True)
        assert ability.get_tries() == 3


@pytest.mark.unit
@pytest.mark.data
class TestAbilityEdgeCases:
    """Test edge cases for Ability."""

    def test_very_high_damage(self, qapp):
        """Test handling very high damage values."""
        ability = Ability("Nuke")
        ability.add_damage(DamageComponent("Energy"), 999999.99)

        assert ability.get_total_damage() == 999999.99

    def test_many_damage_components(self, qapp):
        """Test ability with many damage components."""
        ability = Ability("Complex Power")

        for i in range(10):
            ability.add_damage(DamageComponent(f"Type{i}"), 10.0)

        assert len(ability.damage) == 10
        assert ability.get_total_damage() == 100.0

    def test_damage_rounding(self, qapp):
        """Test that damage calculations are properly rounded."""
        ability = Ability("Precision Test")
        ability.add_damage(DamageComponent("Fire"), 10.123456)
        ability.add_damage(DamageComponent("Fire"), 20.987654)

        # Total should be rounded to 2 decimal places
        total = ability.get_total_damage()
        assert total == 31.11

    def test_zero_duration_dps(self, qapp):
        """Test DPS calculation with zero duration."""
        ability = Ability("Instant")
        ability.add_damage(DamageComponent("Fire"), 100.0)

        dps = ability.get_dps(0)
        # When duration is 0, DamageComponent returns total_damage
        assert dps == 100.0

    def test_proc_ability_damage_increments(self, qapp):
        """Test that proc abilities increment count on damage."""
        proc = Ability("Fire Proc", proc=True)

        proc.add_damage(DamageComponent("Fire"), 10.0)
        proc.add_damage(DamageComponent("Fire"), 10.0)
        proc.add_damage(DamageComponent("Fire"), 10.0)

        assert proc.count == 3
        assert proc.get_total_damage() == 30.0
