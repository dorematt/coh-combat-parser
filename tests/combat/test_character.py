"""
Unit tests for the Character class.

This module tests the Character class which stores and manages
character data including abilities, damage tracking, and statistics.
"""

import pytest
from PyQt5.QtWidgets import QApplication
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
def player_character(qapp):
    """Create a player Character instance for testing."""
    return Character("TestHero", "player")


@pytest.fixture
def pet_character(qapp):
    """Create a pet Character instance for testing."""
    return Character("TestPet", "pet")


@pytest.fixture
def enemy_character(qapp):
    """Create an enemy Character instance for testing."""
    return Character("TestEnemy", "enemy")


@pytest.mark.unit
@pytest.mark.data
class TestCharacterInitialization:
    """Test Character initialization."""

    def test_init_with_name_and_type(self, qapp):
        """Test initialization with name and type."""
        char = Character("Hero", "player")
        assert char.name == "Hero"
        assert char.type == "player"
        assert char.abilities == {}
        assert char.is_pet is False
        assert char.last_ability is None

    def test_init_empty(self, qapp):
        """Test initialization with empty parameters."""
        char = Character()
        assert char.name == ""
        assert char.type == ""
        assert char.abilities == {}

    def test_init_different_types(self, qapp):
        """Test initialization with different character types."""
        player = Character("Player1", "player")
        pet = Character("Pet1", "pet")
        enemy = Character("Enemy1", "enemy")

        assert player.type == "player"
        assert pet.type == "pet"
        assert enemy.type == "enemy"


@pytest.mark.unit
@pytest.mark.data
class TestCharacterAbilityManagement:
    """Test Character ability management."""

    def test_add_ability(self, player_character):
        """Test adding an ability to character."""
        ability = Ability("Fireball")
        player_character.add_ability("Fireball", ability)

        assert "Fireball" in player_character.abilities
        assert player_character.abilities["Fireball"] == ability

    def test_add_multiple_abilities(self, player_character):
        """Test adding multiple abilities."""
        ability1 = Ability("Power1")
        ability2 = Ability("Power2")
        ability3 = Ability("Power3")

        player_character.add_ability("Power1", ability1)
        player_character.add_ability("Power2", ability2)
        player_character.add_ability("Power3", ability3)

        assert len(player_character.abilities) == 3
        assert "Power1" in player_character.abilities
        assert "Power2" in player_character.abilities
        assert "Power3" in player_character.abilities

    def test_get_ability_exists(self, player_character):
        """Test getting an existing ability."""
        ability = Ability("Ice Blast")
        player_character.add_ability("Ice Blast", ability)

        retrieved = player_character.get_ability("Ice Blast")
        assert retrieved == ability

    def test_get_ability_not_exists(self, player_character):
        """Test getting a non-existent ability."""
        result = player_character.get_ability("NonExistent")
        assert result == ""

    def test_overwrite_ability(self, player_character):
        """Test that adding an ability with same name overwrites."""
        ability1 = Ability("Power")
        ability2 = Ability("Power")

        player_character.add_ability("Power", ability1)
        player_character.add_ability("Power", ability2)

        assert player_character.abilities["Power"] == ability2
        assert len(player_character.abilities) == 1


@pytest.mark.unit
@pytest.mark.data
class TestCharacterTypeManagement:
    """Test Character type management."""

    def test_set_type(self, qapp):
        """Test setting character type."""
        char = Character("Test", "player")
        char.set_type("pet")

        assert char.type == "pet"

    def test_get_type(self, player_character):
        """Test getting character type."""
        assert player_character.get_type() == "player"

    def test_get_name(self, player_character):
        """Test getting character name."""
        assert player_character.get_name() == "TestHero"


@pytest.mark.unit
@pytest.mark.data
class TestCharacterDamageCalculations:
    """Test Character damage-related calculations."""

    def test_get_total_damage_empty(self, player_character):
        """Test total damage with no abilities."""
        assert player_character.get_total_damage() == 0

    def test_get_total_damage_single_ability(self, qapp):
        """Test total damage with single ability."""
        char = Character("Test", "player")
        ability = Ability("Power1")
        ability.add_damage(DamageComponent("Fire"), 100.0)
        char.add_ability("Power1", ability)

        assert char.get_total_damage() == 100.0

    def test_get_total_damage_multiple_abilities(self, qapp):
        """Test total damage with multiple abilities."""
        char = Character("Test", "player")

        ability1 = Ability("Power1")
        ability1.add_damage(DamageComponent("Fire"), 100.0)
        char.add_ability("Power1", ability1)

        ability2 = Ability("Power2")
        ability2.add_damage(DamageComponent("Cold"), 150.0)
        char.add_ability("Power2", ability2)

        ability3 = Ability("Power3")
        ability3.add_damage(DamageComponent("Energy"), 50.0)
        char.add_ability("Power3", ability3)

        assert char.get_total_damage() == 300.0

    def test_get_average_damage_empty(self, player_character):
        """Test average damage with no abilities."""
        assert player_character.get_average_damage() == 0

    def test_get_average_damage_single_ability(self, qapp):
        """Test average damage with single ability."""
        char = Character("Test", "player")
        ability = Ability("Power1")
        ability.add_damage(DamageComponent("Fire"), 100.0)
        ability.count = 2
        char.add_ability("Power1", ability)

        # Average of ability is 50.0, and with one ability, character average is 50.0
        assert char.get_average_damage() == 50.0

    def test_get_average_damage_multiple_abilities(self, qapp):
        """Test average damage with multiple abilities."""
        char = Character("Test", "player")

        ability1 = Ability("Power1")
        ability1.add_damage(DamageComponent("Fire"), 100.0)
        ability1.count = 2  # Average = 50.0
        char.add_ability("Power1", ability1)

        ability2 = Ability("Power2")
        ability2.add_damage(DamageComponent("Cold"), 200.0)
        ability2.count = 4  # Average = 50.0
        char.add_ability("Power2", ability2)

        # Character average = (50.0 + 50.0) / 2 = 50.0
        assert char.get_average_damage() == 50.0

    def test_get_dps(self, qapp):
        """Test DPS calculation."""
        char = Character("Test", "player")

        ability1 = Ability("Power1")
        ability1.add_damage(DamageComponent("Fire"), 100.0)
        char.add_ability("Power1", ability1)

        ability2 = Ability("Power2")
        ability2.add_damage(DamageComponent("Cold"), 200.0)
        char.add_ability("Power2", ability2)

        dps = char.get_dps(10)  # 10 second duration
        assert dps == 30.0  # (100 + 200) / 10

    def test_get_dps_empty(self, player_character):
        """Test DPS with no abilities."""
        assert player_character.get_dps(10) == 0


@pytest.mark.unit
@pytest.mark.data
class TestCharacterAccuracyCalculations:
    """Test Character accuracy-related calculations."""

    def test_get_accuracy_empty(self, player_character):
        """Test accuracy with no abilities."""
        assert player_character.get_accuracy() == 0

    def test_get_accuracy_perfect(self, qapp):
        """Test accuracy with all hits."""
        char = Character("Test", "player")

        ability1 = Ability("Power1")
        ability1.ability_hit(True)
        ability1.ability_hit(True)
        char.add_ability("Power1", ability1)

        ability2 = Ability("Power2")
        ability2.ability_hit(True)
        char.add_ability("Power2", ability2)

        # 3 hits out of 3 tries = 100%
        assert char.get_accuracy() == 100.0

    def test_get_accuracy_partial(self, qapp):
        """Test accuracy with partial hits."""
        char = Character("Test", "player")

        ability1 = Ability("Power1")
        ability1.ability_hit(True)
        ability1.ability_hit(False)
        char.add_ability("Power1", ability1)

        ability2 = Ability("Power2")
        ability2.ability_hit(True)
        ability2.ability_hit(False)
        char.add_ability("Power2", ability2)

        # 2 hits out of 4 tries = 50%
        assert char.get_accuracy() == 50.0

    def test_get_accuracy_no_tries(self, player_character):
        """Test accuracy with no tries."""
        ability = Ability("Power1")
        player_character.add_ability("Power1", ability)

        assert player_character.get_accuracy() == 0


@pytest.mark.unit
@pytest.mark.data
class TestCharacterCounters:
    """Test Character counter methods."""

    def test_get_hits_empty(self, player_character):
        """Test hits count with no abilities."""
        assert player_character.get_hits() == 0

    def test_get_hits_single_ability(self, qapp):
        """Test hits count with single ability."""
        char = Character("Test", "player")
        ability = Ability("Power1")
        ability.ability_hit(True)
        ability.ability_hit(True)
        ability.ability_hit(False)
        char.add_ability("Power1", ability)

        assert char.get_hits() == 2

    def test_get_hits_multiple_abilities(self, qapp):
        """Test hits count with multiple abilities."""
        char = Character("Test", "player")

        ability1 = Ability("Power1")
        ability1.ability_hit(True)
        ability1.ability_hit(True)
        char.add_ability("Power1", ability1)

        ability2 = Ability("Power2")
        ability2.ability_hit(True)
        char.add_ability("Power2", ability2)

        assert char.get_hits() == 3

    def test_get_tries_empty(self, player_character):
        """Test tries count with no abilities."""
        assert player_character.get_tries() == 0

    def test_get_tries_single_ability(self, qapp):
        """Test tries count with single ability."""
        char = Character("Test", "player")
        ability = Ability("Power1")
        ability.ability_hit(True)
        ability.ability_hit(False)
        ability.ability_hit(True)
        char.add_ability("Power1", ability)

        assert char.get_tries() == 3

    def test_get_tries_multiple_abilities(self, qapp):
        """Test tries count with multiple abilities."""
        char = Character("Test", "player")

        ability1 = Ability("Power1")
        ability1.ability_hit(True)
        ability1.ability_hit(False)
        char.add_ability("Power1", ability1)

        ability2 = Ability("Power2")
        ability2.ability_hit(True)
        ability2.ability_hit(True)
        ability2.ability_hit(False)
        char.add_ability("Power2", ability2)

        assert char.get_tries() == 5

    def test_get_count_empty(self, player_character):
        """Test activation count with no abilities."""
        assert player_character.get_count() == 0

    def test_get_count_single_ability(self, qapp):
        """Test activation count with single ability."""
        char = Character("Test", "player")
        ability = Ability("Power1")
        ability.ability_used()
        ability.ability_used()
        ability.ability_used()
        char.add_ability("Power1", ability)

        assert char.get_count() == 3

    def test_get_count_multiple_abilities(self, qapp):
        """Test activation count with multiple abilities."""
        char = Character("Test", "player")

        ability1 = Ability("Power1")
        ability1.ability_used()
        ability1.ability_used()
        char.add_ability("Power1", ability1)

        ability2 = Ability("Power2")
        ability2.ability_used()
        ability2.ability_used()
        ability2.ability_used()
        char.add_ability("Power2", ability2)

        assert char.get_count() == 5


@pytest.mark.unit
@pytest.mark.data
class TestCharacterEdgeCases:
    """Test edge cases for Character."""

    def test_last_ability_tracking(self, qapp):
        """Test last_ability field updates."""
        char = Character("Test", "player")
        ability1 = Ability("Power1")
        ability2 = Ability("Power2")

        char.add_ability("Power1", ability1)
        char.last_ability = ability1
        assert char.last_ability == ability1

        char.add_ability("Power2", ability2)
        char.last_ability = ability2
        assert char.last_ability == ability2

    def test_is_pet_field(self, qapp):
        """Test is_pet field."""
        char = Character("Test", "pet")
        assert char.is_pet is False  # Default is False

        char.is_pet = True
        assert char.is_pet is True

    def test_very_large_ability_count(self, qapp):
        """Test character with many abilities."""
        char = Character("Test", "player")

        for i in range(50):
            ability = Ability(f"Power{i}")
            ability.add_damage(DamageComponent("Fire"), 10.0)
            char.add_ability(f"Power{i}", ability)

        assert len(char.abilities) == 50
        assert char.get_total_damage() == 500.0

    def test_rounding_precision(self, qapp):
        """Test that damage calculations maintain precision."""
        char = Character("Test", "player")

        ability = Ability("Precise")
        ability.add_damage(DamageComponent("Fire"), 10.123)
        ability.add_damage(DamageComponent("Cold"), 20.456)
        char.add_ability("Precise", ability)

        total = char.get_total_damage()
        assert isinstance(total, float)
        assert total == 30.58  # Should be rounded to 2 decimal places
