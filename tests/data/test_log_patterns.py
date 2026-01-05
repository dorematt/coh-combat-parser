"""
Unit tests for the LogPatterns module.

This module tests the regex patterns used to parse City of Heroes combat logs.
"""

import pytest
import re
from data.LogPatterns import PATTERNS, PATTERN_DATETIME


@pytest.mark.unit
@pytest.mark.data
class TestPatternStructure:
    """Test the structure of pattern dictionaries."""

    def test_patterns_is_dict(self):
        """Test that PATTERNS is a dictionary."""
        assert isinstance(PATTERNS, dict)

    def test_patterns_not_empty(self):
        """Test that PATTERNS is not empty."""
        assert len(PATTERNS) > 0

    def test_all_patterns_are_regex(self):
        """Test that all PATTERNS values are compiled regex patterns."""
        for key, pattern in PATTERNS.items():
            assert isinstance(pattern, re.Pattern), f"{key} should be a compiled regex"

    def test_pattern_datetime_is_dict(self):
        """Test that PATTERN_DATETIME is a dictionary."""
        assert isinstance(PATTERN_DATETIME, dict)

    def test_expected_patterns_exist(self):
        """Test that expected pattern keys exist."""
        expected_keys = [
            "player_ability_activate",
            "player_hit_roll",
            "player_pet_hit_roll",
            "player_damage",
            "player_pet_damage",
            "reward_gain_both",
            "reward_gain_exp",
            "reward_gain_inf",
            "player_name",
            "player_name_backup",
            "command",
        ]

        for key in expected_keys:
            assert key in PATTERNS, f"{key} should be in PATTERNS"


@pytest.mark.unit
@pytest.mark.data
class TestPlayerAbilityActivatePattern:
    """Test the player_ability_activate pattern."""

    def test_match_basic_ability_activate(self):
        """Test matching a basic ability activation."""
        log_line = "2024-08-10 15:30:45 You activated the Fire Blast power."
        match = PATTERNS["player_ability_activate"].match(log_line)

        assert match is not None
        assert match.group("date") == "2024-08-10"
        assert match.group("time") == "15:30:45"
        assert match.group("ability") == "Fire Blast"

    def test_match_ability_with_spaces(self):
        """Test matching an ability with spaces in the name."""
        log_line = "2024-08-10 15:30:45 You activated the Healing Aura power."
        match = PATTERNS["player_ability_activate"].match(log_line)

        assert match is not None
        assert match.group("ability") == "Healing Aura"

    def test_match_long_ability_name(self):
        """Test matching an ability with a long name."""
        log_line = "2024-08-10 15:30:45 You activated the Superior Might of the Tanker power."
        match = PATTERNS["player_ability_activate"].match(log_line)

        assert match is not None
        assert match.group("ability") == "Superior Might of the Tanker"

    def test_no_match_incorrect_format(self):
        """Test that incorrect format doesn't match."""
        log_line = "2024-08-10 15:30:45 Fire Blast activated."
        match = PATTERNS["player_ability_activate"].match(log_line)

        assert match is None


@pytest.mark.unit
@pytest.mark.data
class TestPlayerHitRollPattern:
    """Test the player_hit_roll pattern."""

    def test_match_hit(self):
        """Test matching a successful hit."""
        log_line = "2024-08-10 15:30:45 HIT Target Enemy! Your Fire Blast power had a 95.00% chance to hit, you rolled a 50.00."
        match = PATTERNS["player_hit_roll"].match(log_line)

        assert match is not None
        assert match.group("date") == "2024-08-10"
        assert match.group("time") == "15:30:45"
        assert match.group("outcome") == "HIT"
        assert match.group("target") == "Target Enemy"
        assert match.group("ability") == "Fire Blast"

    def test_match_miss(self):
        """Test matching a miss."""
        log_line = "2024-08-10 15:30:45 MISSED Target Enemy! Your Ice Bolt power had a 50.00% chance to hit, you rolled a 75.00."
        match = PATTERNS["player_hit_roll"].match(log_line)

        assert match is not None
        assert match.group("outcome") == "MISSED"
        assert match.group("target") == "Target Enemy"
        assert match.group("ability") == "Ice Bolt"

    def test_match_streakbreaker(self):
        """Test matching a streakbreaker forced hit."""
        log_line = "2024-08-10 15:30:45 HIT Enemy Name! Your Power Name power was forced to hit by streakbreaker."
        match = PATTERNS["player_hit_roll"].match(log_line)

        assert match is not None
        assert match.group("outcome") == "HIT"
        assert match.group("target") == "Enemy Name"
        assert match.group("ability") == "Power Name"

    def test_match_exclamation_mark(self):
        """Test matching with exclamation mark."""
        log_line = "2024-08-10 15:30:45 HIT Boss!! Your Smash power had a 95.00% chance to hit, you rolled a 10.00."
        match = PATTERNS["player_hit_roll"].match(log_line)

        assert match is not None
        assert match.group("target") == "Boss"


@pytest.mark.unit
@pytest.mark.data
class TestPlayerPetHitRollPattern:
    """Test the player_pet_hit_roll pattern."""

    def test_match_pet_hit(self):
        """Test matching a pet hit roll."""
        log_line = "2024-08-10 15:30:45 Fire Imp: HIT Enemy! Your Fire Blast power had a 95.00% chance to hit, you rolled a 50.00."
        match = PATTERNS["player_pet_hit_roll"].match(log_line)

        assert match is not None
        assert match.group("pet_name") == "Fire Imp"
        assert match.group("outcome") == "HIT"
        assert match.group("target") == "Enemy"
        assert match.group("ability") == "Fire Blast"

    def test_match_pet_miss(self):
        """Test matching a pet miss."""
        log_line = "2024-08-10 15:30:45 Battle Drone: MISSED Target! Your Laser power had a 75.00% chance to hit, you rolled a 90.00."
        match = PATTERNS["player_pet_hit_roll"].match(log_line)

        assert match is not None
        assert match.group("pet_name") == "Battle Drone"
        assert match.group("outcome") == "MISSED"

    def test_match_pet_with_colon(self):
        """Test matching a pet name that might have special characters."""
        log_line = "2024-08-10 15:30:45 Demon Prince: HIT Villain! Your Hellfire power had a 95.00% chance to hit, you rolled a 20.00."
        match = PATTERNS["player_pet_hit_roll"].match(log_line)

        assert match is not None
        assert match.group("pet_name") == "Demon Prince"


@pytest.mark.unit
@pytest.mark.data
class TestPlayerDamagePattern:
    """Test the player_damage pattern."""

    def test_match_basic_damage(self):
        """Test matching basic damage."""
        log_line = "2024-08-10 15:30:45 You hit Enemy with your Fire Blast for 100.50 points of Fire damage."
        match = PATTERNS["player_damage"].match(log_line)

        assert match is not None
        assert match.group("target") == "Enemy"
        assert match.group("ability") == "Fire Blast"
        assert match.group("damage_value") == "100.50"
        # damage_type includes trailing space before 'damage'
        assert "Fire" in match.group("damage_type")

    def test_match_damage_with_flair(self):
        """Test matching damage with flair (crit, etc)."""
        log_line = "2024-08-10 15:30:45 You hit Enemy with your Smashing Blow for 200.00 points of Smashing damage (CRITICAL)."
        match = PATTERNS["player_damage"].match(log_line)

        assert match is not None
        assert match.group("damage_value") == "200.00"
        # damage_type includes trailing space before 'damage'
        assert "Smashing" in match.group("damage_type")
        assert match.group("damage_flair") == "CRITICAL"

    def test_match_damage_over_time(self):
        """Test matching damage over time."""
        log_line = "2024-08-10 15:30:45 You hit Enemy with your Burn for 50.00 points of Fire damage over time."
        match = PATTERNS["player_damage"].match(log_line)

        assert match is not None
        assert match.group("ability") == "Burn"
        assert match.group("damage_value") == "50.00"

    def test_match_proc_damage(self):
        """Test matching proc damage."""
        log_line = "2024-08-10 15:30:45 You hit Enemy with your Fire Blast: Recharge/Chance for Fire Damage for 75.00 points of Fire damage."
        match = PATTERNS["player_damage"].match(log_line)

        assert match is not None
        assert match.group("ability") == "Fire Blast"
        assert match.group("ability_desc") == "Recharge/Chance for Fire Damage"

    def test_match_player_name_prefix(self):
        """Test matching with PLAYER_NAME prefix."""
        log_line = "2024-08-10 15:30:45 PLAYER_NAME:  You hit Enemy with your Power for 100.00 points of Energy damage."
        match = PATTERNS["player_damage"].match(log_line)

        assert match is not None
        assert match.group("ability") == "Power"


@pytest.mark.unit
@pytest.mark.data
class TestPlayerPetDamagePattern:
    """Test the player_pet_damage pattern."""

    def test_match_pet_damage(self):
        """Test matching pet damage."""
        log_line = "2024-08-10 15:30:45 Fire Imp: You hit Enemy with your Fire Blast for 80.00 points of Fire damage."
        match = PATTERNS["player_pet_damage"].match(log_line)

        assert match is not None
        assert match.group("pet_name") == "Fire Imp"
        assert match.group("target") == "Enemy"
        assert match.group("ability") == "Fire Blast"
        assert match.group("damage_value") == "80.00"

    def test_match_pet_damage_with_flair(self):
        """Test matching pet damage with flair."""
        log_line = "2024-08-10 15:30:45 Battle Drone: You hit Boss with your Laser for 150.00 points of Energy damage (CRITICAL)."
        match = PATTERNS["player_pet_damage"].match(log_line)

        assert match is not None
        assert match.group("pet_name") == "Battle Drone"
        assert match.group("damage_flair") == "CRITICAL"


@pytest.mark.unit
@pytest.mark.data
class TestRewardPatterns:
    """Test reward gain patterns."""

    def test_match_reward_both(self):
        """Test matching exp and inf together."""
        log_line = "2024-08-10 15:30:45 You gain 1,234 experience and 5,678 influence."
        match = PATTERNS["reward_gain_both"].match(log_line)

        assert match is not None
        assert match.group("exp_value") == "1,234"
        assert match.group("inf_value") == "5,678"

    def test_match_reward_both_large_numbers(self):
        """Test matching large reward numbers."""
        log_line = "2024-08-10 15:30:45 You gain 123,456 experience and 987,654 infamy."
        match = PATTERNS["reward_gain_both"].match(log_line)

        assert match is not None
        assert match.group("exp_value") == "123,456"
        assert match.group("inf_value") == "987,654"

    def test_match_reward_exp_only(self):
        """Test matching experience only."""
        log_line = "2024-08-10 15:30:45 You gain 500 experience."
        match = PATTERNS["reward_gain_exp"].match(log_line)

        assert match is not None
        assert match.group("exp_value") == "500"

    def test_match_reward_inf_only(self):
        """Test matching influence only."""
        log_line = "2024-08-10 15:30:45 You gain 1,000 influence."
        match = PATTERNS["reward_gain_inf"].match(log_line)

        assert match is not None
        assert match.group("inf_value") == "1,000"

    def test_match_information(self):
        """Test matching information (villain currency)."""
        log_line = "2024-08-10 15:30:45 You gain 2,000 information."
        match = PATTERNS["reward_gain_inf"].match(log_line)

        assert match is not None
        assert match.group("inf_value") == "2,000"


@pytest.mark.unit
@pytest.mark.data
class TestPlayerNamePatterns:
    """Test player name detection patterns."""

    def test_match_player_name_hero(self):
        """Test matching player name from hero welcome message."""
        log_line = "2024-08-10 15:30:45 Welcome to City of Heroes, SuperHero!"
        match = PATTERNS["player_name"].match(log_line)

        assert match is not None
        assert match.group("player_name") == "SuperHero"

    def test_match_player_name_villain(self):
        """Test matching player name from villain welcome message."""
        log_line = "2024-08-10 15:30:45 Now entering the Rogue Isles, DarkVillain!"
        match = PATTERNS["player_name"].match(log_line)

        assert match is not None
        assert match.group("player_name") == "DarkVillain"

    def test_match_player_name_backup_stamina(self):
        """Test matching player name from Stamina autohit."""
        log_line = "2024-08-10 15:30:45 HIT PlayerName! Your Stamina power is autohit."
        match = PATTERNS["player_name_backup"].match(log_line)

        assert match is not None
        assert match.group("player_name") == "PlayerName"

    def test_match_player_name_backup_health(self):
        """Test matching player name from Health autohit."""
        log_line = "2024-08-10 15:30:45 HIT HeroName! Your Health power is autohit."
        match = PATTERNS["player_name_backup"].match(log_line)

        assert match is not None
        assert match.group("player_name") == "HeroName"


@pytest.mark.unit
@pytest.mark.data
class TestCommandPattern:
    """Test command pattern for chat commands."""

    def test_match_command_local(self):
        """Test matching a command in local chat."""
        log_line = "2024-08-10 15:30:45 [Local] PlayerName: some text ##SET_NAME My Session"
        match = PATTERNS["command"].match(log_line)

        assert match is not None
        assert match.group("player") == "PlayerName"
        assert match.group("command") == "SET_NAME"
        assert match.group("value") == "My Session"

    def test_match_command_supergroup(self):
        """Test matching a command in supergroup chat."""
        log_line = "2024-08-10 15:30:45 [SuperGroup] Hero: ##START_SESSION Boss Fight"
        match = PATTERNS["command"].match(log_line)

        assert match is not None
        assert match.group("player") == "Hero"
        assert match.group("command") == "START_SESSION"
        assert match.group("value") == "Boss Fight"

    def test_match_command_no_value(self):
        """Test matching a command with no value."""
        log_line = "2024-08-10 15:30:45 [Local] Player: ##RESET "
        match = PATTERNS["command"].match(log_line)

        assert match is not None
        assert match.group("command") == "RESET"


@pytest.mark.unit
@pytest.mark.data
class TestDateTimePattern:
    """Test the datetime pattern."""

    def test_match_datetime(self):
        """Test matching date and time."""
        log_line = "2024-08-10 15:30:45 Some log content"
        match = PATTERN_DATETIME["date_time"].match(log_line)

        assert match is not None
        assert match.group("date") == "2024-08-10"
        assert match.group("time") == "15:30:45"

    def test_match_different_dates(self):
        """Test matching different date formats."""
        log_lines = [
            "2024-01-01 00:00:00 Content",
            "2024-12-31 23:59:59 Content",
            "2024-06-15 12:30:45 Content",
        ]

        for log_line in log_lines:
            match = PATTERN_DATETIME["date_time"].match(log_line)
            assert match is not None


@pytest.mark.unit
@pytest.mark.data
class TestPatternEdgeCases:
    """Test edge cases for patterns."""

    def test_damage_with_decimal(self):
        """Test damage values with decimals."""
        log_line = "2024-08-10 15:30:45 You hit Enemy with your Power for 123.45 points of Fire damage."
        match = PATTERNS["player_damage"].match(log_line)

        assert match is not None
        assert match.group("damage_value") == "123.45"

    def test_target_with_special_characters(self):
        """Test target names with spaces and special characters."""
        # The pattern requires specific format, matching actual log format
        log_line = "2024-08-10 15:30:45 HIT Rikti Drone! Your Fire Blast power had a 95.00% chance to hit, you rolled a 50.00."
        match = PATTERNS["player_hit_roll"].match(log_line)

        assert match is not None
        assert match.group("target") == "Rikti Drone"
        assert match.group("ability") == "Fire Blast"

    def test_ability_with_parentheses(self):
        """Test abilities that might contain special characters."""
        log_line = "2024-08-10 15:30:45 You activated the Power (Special) power."
        match = PATTERNS["player_ability_activate"].match(log_line)

        assert match is not None
        assert match.group("ability") == "Power (Special)"

    def test_large_damage_value(self):
        """Test very large damage values."""
        log_line = "2024-08-10 15:30:45 You hit Enemy with your Nuke for 99999.99 points of Energy damage."
        match = PATTERNS["player_damage"].match(log_line)

        assert match is not None
        assert match.group("damage_value") == "99999.99"

    def test_zero_damage(self):
        """Test zero damage value."""
        log_line = "2024-08-10 15:30:45 You hit Enemy with your Power for 0.00 points of Fire damage."
        match = PATTERNS["player_damage"].match(log_line)

        assert match is not None
        assert match.group("damage_value") == "0.00"
