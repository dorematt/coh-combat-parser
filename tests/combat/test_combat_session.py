"""
Unit tests for the CombatSession class.

This module tests the CombatSession class which stores and manages
combat session data including characters, targets, duration, and rewards.
"""

import pytest
from PyQt5.QtWidgets import QApplication
from combat.CombatSession import CombatSession
from combat.Character import Character
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
def combat_session(qapp):
    """Create a basic CombatSession instance for testing."""
    return CombatSession(timestamp=1000, name="Test Session")


@pytest.mark.unit
@pytest.mark.data
class TestCombatSessionInitialization:
    """Test CombatSession initialization."""

    def test_init_with_timestamp_and_name(self, qapp):
        """Test initialization with timestamp and name."""
        session = CombatSession(timestamp=5000, name="Session 1")

        assert session.start_time == 5000
        assert session.end_time == 5000
        assert session.duration == 0
        assert session.name == "Session 1"
        assert session.chars_out == {}
        assert session.chars_in == {}
        assert session.targets_in == {}
        assert session.targets_out == {}
        assert session.exp_value == 0
        assert session.inf_value == 0

    def test_init_default_values(self, qapp):
        """Test initialization with default values."""
        session = CombatSession()

        assert session.start_time == 0
        assert session.end_time == 0
        assert session.name == ""


@pytest.mark.unit
@pytest.mark.data
class TestCombatSessionTimeManagement:
    """Test CombatSession time management."""

    def test_set_start_time(self, combat_session):
        """Test setting start time."""
        combat_session.set_start_time(2000)
        assert combat_session.start_time == 2000

    def test_set_end_time(self, combat_session):
        """Test setting end time."""
        combat_session.set_end_time(3000)
        assert combat_session.end_time == 3000

    def test_update_duration(self, qapp):
        """Test duration update calculation."""
        session = CombatSession(timestamp=1000)
        session.set_end_time(5000)
        session.update_duration()

        assert session.duration == 4000

    def test_get_duration(self, qapp):
        """Test get_duration method."""
        session = CombatSession(timestamp=1000)
        session.set_end_time(6000)

        duration = session.get_duration()
        assert duration == 5000

    def test_update_session_time_in_combat(self, qapp):
        """Test updating session time while in combat."""
        session = CombatSession(timestamp=1000)
        session.update_session_time(2000, in_combat=True)

        assert session.end_time == 2000
        assert session.duration == 1000

    def test_update_session_time_not_in_combat(self, qapp):
        """Test updating session time while not in combat."""
        session = CombatSession(timestamp=1000)
        session.update_session_time(2000, in_combat=False)

        # Should not update when not in combat
        assert session.end_time == 1000
        assert session.duration == 0


@pytest.mark.unit
@pytest.mark.data
class TestCombatSessionNameManagement:
    """Test CombatSession name management."""

    def test_set_name(self, combat_session):
        """Test setting session name."""
        combat_session.set_name("New Session Name")
        assert combat_session.name == "New Session Name"

    def test_get_name(self, combat_session):
        """Test getting session name."""
        assert combat_session.get_name() == "Test Session"


@pytest.mark.unit
@pytest.mark.data
class TestCombatSessionCharacterManagement:
    """Test CombatSession character management."""

    def test_add_character(self, qapp):
        """Test adding a character to session."""
        session = CombatSession()
        char = Character("Hero", "player_out")
        session.add_character(char, "chars_out")

        assert "Hero" in session.chars_out
        assert session.chars_out["Hero"] == char

    def test_check_in_char_new_player(self, qapp):
        """Test checking in a new player character."""
        session = CombatSession()
        result = session.check_in_char("Player1", "player_out")

        assert result is False  # New character
        assert "Player1" in session.chars_out
        assert session.chars_out["Player1"].get_type() == "player_out"

    def test_check_in_char_existing_player(self, qapp):
        """Test checking in an existing player character."""
        session = CombatSession()
        session.check_in_char("Player1", "player_out")
        result = session.check_in_char("Player1", "player_out")

        assert result is True  # Existing character
        assert len(session.chars_out) == 1

    def test_check_in_char_new_pet(self, qapp):
        """Test checking in a new pet character."""
        session = CombatSession()
        result = session.check_in_char("Pet1", "pet_out")

        assert result is False  # New character
        assert "Pet1" in session.chars_out
        assert session.chars_out["Pet1"].get_type() == "pet_out"

    def test_check_in_char_new_enemy(self, qapp):
        """Test checking in a new enemy character."""
        session = CombatSession()
        result = session.check_in_char("Enemy1", "target_in")

        assert result is False  # New enemy
        assert "Enemy1" in session.targets_in
        assert session.targets_in["Enemy1"].get_type() == "target_in"

    def test_check_in_char_existing_enemy(self, qapp):
        """Test checking in an existing enemy character."""
        session = CombatSession()
        session.check_in_char("Enemy1", "target_in")
        result = session.check_in_char("Enemy1", "target_in")

        assert result is True  # Existing enemy
        assert len(session.targets_in) == 1

    def test_check_in_char_invalid_type(self, qapp):
        """Test that invalid character type raises ValueError."""
        session = CombatSession()

        with pytest.raises(ValueError):
            session.check_in_char("Invalid", "invalid_type")

    def test_multiple_characters(self, qapp):
        """Test adding multiple characters."""
        session = CombatSession()

        session.check_in_char("Player1", "player_out")
        session.check_in_char("Pet1", "pet_out")
        session.check_in_char("Pet2", "pet_out")

        assert len(session.chars_out) == 3
        assert "Player1" in session.chars_out
        assert "Pet1" in session.chars_out
        assert "Pet2" in session.chars_out

    def test_multiple_targets(self, qapp):
        """Test adding multiple targets."""
        session = CombatSession()

        session.check_in_char("Enemy1", "target_in")
        session.check_in_char("Enemy2", "target_in")
        session.check_in_char("Enemy3", "target_in")

        assert len(session.targets_in) == 3
        assert "Enemy1" in session.targets_in
        assert "Enemy2" in session.targets_in
        assert "Enemy3" in session.targets_in


@pytest.mark.unit
@pytest.mark.data
class TestCombatSessionDamageCalculations:
    """Test CombatSession damage calculations."""

    def test_get_total_damage_empty(self, combat_session):
        """Test total damage with no characters."""
        assert combat_session.get_total_damage() == 0

    def test_get_total_damage_single_character(self, qapp):
        """Test total damage with single character."""
        session = CombatSession()
        char = Character("Player", "player_out")
        ability = Ability("Power1")
        ability.add_damage(DamageComponent("Fire"), 100.0)
        char.add_ability("Power1", ability)
        session.add_character(char, "chars_out")

        assert session.get_total_damage("chars_out") == 100.0

    def test_get_total_damage_multiple_characters(self, qapp):
        """Test total damage with multiple characters."""
        session = CombatSession()

        char1 = Character("Player", "player_out")
        ability1 = Ability("Power1")
        ability1.add_damage(DamageComponent("Fire"), 100.0)
        char1.add_ability("Power1", ability1)
        session.add_character(char1, "chars_out")

        char2 = Character("Pet", "pet_out")
        ability2 = Ability("Power2")
        ability2.add_damage(DamageComponent("Cold"), 50.0)
        char2.add_ability("Power2", ability2)
        session.add_character(char2, "chars_out")

        assert session.get_total_damage("chars_out") == 150.0

    def test_has_no_damage_true(self, combat_session):
        """Test has_no_damage returns True when no damage."""
        assert combat_session.has_no_damage() is True

    def test_has_no_damage_false(self, qapp):
        """Test has_no_damage returns False when damage exists."""
        session = CombatSession()
        char = Character("Player", "player_out")
        ability = Ability("Power1")
        ability.add_damage(DamageComponent("Fire"), 100.0)
        char.add_ability("Power1", ability)
        session.add_character(char, "chars_out")

        assert session.has_no_damage() is False

    def test_get_average_damage_no_damage(self, combat_session):
        """Test average damage with no damage."""
        # When total damage is 0, the method returns 0 without calling get_count()
        # Note: get_count method is not defined in CombatSession, but is only
        # called when damage > 0
        result = combat_session.get_average_damage()
        assert result == 0

    def test_get_dps_empty(self, qapp):
        """Test DPS with no characters."""
        session = CombatSession(timestamp=0)
        session.set_end_time(10)
        session.update_duration()

        assert session.get_dps() == 0

    def test_get_dps_with_characters(self, qapp):
        """Test DPS calculation with characters."""
        session = CombatSession(timestamp=0)
        session.set_end_time(10)
        session.update_duration()

        char = Character("Player", "player_out")
        ability = Ability("Power1")
        ability.add_damage(DamageComponent("Fire"), 100.0)
        char.add_ability("Power1", ability)
        session.add_character(char, "chars_out")

        dps = session.get_dps("chars_out")
        assert dps == 10.0  # 100 damage / 10 seconds


@pytest.mark.unit
@pytest.mark.data
class TestCombatSessionRewards:
    """Test CombatSession reward tracking."""

    def test_add_exp(self, combat_session):
        """Test adding experience."""
        combat_session.add_exp(1000)
        assert combat_session.exp_value == 1000

        combat_session.add_exp(500)
        assert combat_session.exp_value == 1500

    def test_add_inf(self, combat_session):
        """Test adding influence."""
        combat_session.add_inf(5000)
        assert combat_session.inf_value == 5000

        combat_session.add_inf(2500)
        assert combat_session.inf_value == 7500

    def test_get_exp(self, qapp):
        """Test getting experience value."""
        session = CombatSession()
        session.add_exp(12345)
        assert session.get_exp() == 12345

    def test_get_inf(self, qapp):
        """Test getting influence value."""
        session = CombatSession()
        session.add_inf(67890)
        assert session.get_inf() == 67890

    def test_rewards_independent(self, qapp):
        """Test that exp and inf are tracked independently."""
        session = CombatSession()
        session.add_exp(1000)
        session.add_inf(5000)

        assert session.get_exp() == 1000
        assert session.get_inf() == 5000


@pytest.mark.unit
@pytest.mark.data
class TestCombatSessionEdgeCases:
    """Test edge cases for CombatSession."""

    def test_zero_duration_session(self, qapp):
        """Test session with zero duration."""
        session = CombatSession(timestamp=1000)
        assert session.get_duration() == 0

    def test_very_long_session(self, qapp):
        """Test session with very long duration."""
        session = CombatSession(timestamp=0)
        session.set_end_time(3600)  # 1 hour
        session.update_duration()

        assert session.duration == 3600

    def test_negative_duration(self, qapp):
        """Test that end time before start time gives negative duration."""
        session = CombatSession(timestamp=5000)
        session.set_end_time(3000)
        session.update_duration()

        # This would be a bug, but the code doesn't prevent it
        assert session.duration == -2000

    def test_large_reward_values(self, qapp):
        """Test very large reward values."""
        session = CombatSession()
        session.add_exp(999999999)
        session.add_inf(999999999)

        assert session.get_exp() == 999999999
        assert session.get_inf() == 999999999

    def test_session_with_many_characters(self, qapp):
        """Test session with many characters."""
        session = CombatSession()

        for i in range(20):
            char = Character(f"Char{i}", "player_out" if i % 2 == 0 else "pet_out")
            ability = Ability(f"Power{i}")
            ability.add_damage(DamageComponent("Fire"), 10.0)
            char.add_ability(f"Power{i}", ability)
            session.add_character(char, "chars_out")

        assert len(session.chars_out) == 20
        assert session.get_total_damage("chars_out") == 200.0

    def test_session_with_many_targets(self, qapp):
        """Test session with many targets."""
        session = CombatSession()

        for i in range(50):
            session.check_in_char(f"Enemy{i}", "target_in")

        assert len(session.targets_in) == 50

    def test_multiple_session_time_updates(self, qapp):
        """Test multiple session time updates."""
        session = CombatSession(timestamp=1000)

        session.update_session_time(2000, in_combat=True)
        assert session.duration == 1000

        session.update_session_time(3000, in_combat=True)
        assert session.duration == 2000

        session.update_session_time(5000, in_combat=True)
        assert session.duration == 4000

    def test_rounding_precision(self, qapp):
        """Test damage calculation precision."""
        session = CombatSession()

        char = Character("Player", "player_out")
        ability = Ability("Precise")
        ability.add_damage(DamageComponent("Fire"), 10.123456)
        char.add_ability("Precise", ability)
        session.add_character(char, "chars_out")

        total = session.get_total_damage("chars_out")
        assert total == 10.12  # Should be rounded to 2 decimal places
