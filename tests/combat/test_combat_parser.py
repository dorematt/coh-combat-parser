"""
Unit tests for the CombatParser class.

This module tests critical data handling methods in the Parser class
including timestamp conversion, pattern extraction, and session management.
"""

import pytest
import tempfile
import os
from PyQt5.QtWidgets import QApplication
from combat.CombatParser import Parser
from combat.CombatSession import CombatSession


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for Qt tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def parser(qapp):
    """Create a Parser instance for testing."""
    return Parser()


@pytest.fixture
def temp_log_file():
    """Create a temporary log file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8') as f:
        f.write("2024-08-10 15:30:45 Welcome to City of Heroes, TestHero!\n")
        f.write("2024-08-10 15:30:50 You activated the Fire Blast power.\n")
        f.write("2024-08-10 15:30:51 HIT Enemy! Your Fire Blast power had a 95.00% chance to hit, you rolled a 50.00.\n")
        f.write("2024-08-10 15:30:52 You hit Enemy with your Fire Blast for 100.00 points of Fire damage.\n")
        temp_file = f.name

    yield temp_file

    # Cleanup
    if os.path.exists(temp_file):
        os.unlink(temp_file)


@pytest.mark.unit
@pytest.mark.data
class TestParserInitialization:
    """Test Parser initialization."""

    def test_parser_init(self, parser):
        """Test that Parser initializes correctly."""
        assert parser is not None
        assert parser.LOG_FILE_PATH == ""
        assert parser.PLAYER_NAME == ""
        assert parser.combat_session_data == []
        assert parser.session_count == 0

    def test_clean_variables(self, parser):
        """Test that clean_variables resets state."""
        # Set some values
        parser.line_count = 100
        parser.session_count = 5
        parser.EXP_VALUE = 1000
        parser.INF_VALUE = 5000

        # Clean variables
        parser.clean_variables()

        # Check reset
        assert parser.line_count == 0
        assert parser.session_count == 0
        assert parser.EXP_VALUE == 0
        assert parser.INF_VALUE == 0
        assert parser.combat_session_data == []


@pytest.mark.unit
@pytest.mark.data
class TestTimestampConversion:
    """Test timestamp conversion methods."""

    def test_convert_timestamp_midnight(self, parser):
        """Test converting midnight timestamp."""
        timestamp = parser.convert_timestamp("2024-08-10", "00:00:00")
        assert timestamp == 0

    def test_convert_timestamp_one_hour(self, parser):
        """Test converting one hour timestamp."""
        timestamp = parser.convert_timestamp("2024-08-10", "01:00:00")
        assert timestamp == 3600  # 1 hour = 3600 seconds

    def test_convert_timestamp_noon(self, parser):
        """Test converting noon timestamp."""
        timestamp = parser.convert_timestamp("2024-08-10", "12:00:00")
        assert timestamp == 43200  # 12 hours = 43200 seconds

    def test_convert_timestamp_complex(self, parser):
        """Test converting complex timestamp."""
        timestamp = parser.convert_timestamp("2024-08-10", "15:30:45")
        # 15*3600 + 30*60 + 45 = 54000 + 1800 + 45 = 55845
        assert timestamp == 55845

    def test_convert_timestamp_end_of_day(self, parser):
        """Test converting end of day timestamp."""
        timestamp = parser.convert_timestamp("2024-08-10", "23:59:59")
        assert timestamp == 86399  # Almost 24 hours


@pytest.mark.unit
@pytest.mark.data
class TestLogLineExtraction:
    """Test log line data extraction."""

    def test_extract_player_ability_activate(self, parser):
        """Test extracting player ability activation."""
        log_line = "2024-08-10 15:30:45 You activated the Fire Blast power."
        event, data = parser.extract_from_line(log_line)

        assert event == "player_ability_activate"
        assert data["date"] == "2024-08-10"
        assert data["time"] == "15:30:45"
        assert data["ability"] == "Fire Blast"

    def test_extract_player_damage(self, parser):
        """Test extracting player damage."""
        log_line = "2024-08-10 15:30:45 You hit Enemy with your Fire Blast for 100.00 points of Fire damage."
        event, data = parser.extract_from_line(log_line)

        assert event == "player_damage"
        assert data["target"] == "Enemy"
        assert data["ability"] == "Fire Blast"
        assert data["damage_value"] == "100.00"
        assert "Fire" in data["damage_type"]

    def test_extract_player_hit_roll(self, parser):
        """Test extracting player hit roll."""
        log_line = "2024-08-10 15:30:45 HIT Enemy! Your Fire Blast power had a 95.00% chance to hit, you rolled a 50.00."
        event, data = parser.extract_from_line(log_line)

        assert event == "player_hit_roll"
        assert data["outcome"] == "HIT"
        assert data["target"] == "Enemy"
        assert data["ability"] == "Fire Blast"

    def test_extract_reward_gain(self, parser):
        """Test extracting reward gain."""
        log_line = "2024-08-10 15:30:45 You gain 1,234 experience and 5,678 influence."
        event, data = parser.extract_from_line(log_line)

        assert event == "reward_gain_both"
        assert data["exp_value"] == "1,234"
        assert data["inf_value"] == "5,678"

    def test_extract_player_name(self, parser):
        """Test extracting player name."""
        log_line = "2024-08-10 15:30:45 Welcome to City of Heroes, TestHero!"
        event, data = parser.extract_from_line(log_line)

        assert event == "player_name"
        assert data["player_name"] == "TestHero"

    def test_extract_no_match(self, parser):
        """Test extracting from non-matching line."""
        log_line = "2024-08-10 15:30:45 Random text that doesn't match."
        event, data = parser.extract_from_line(log_line)

        assert event == ""
        assert data == []


@pytest.mark.unit
@pytest.mark.data
class TestPlayerNameHandling:
    """Test player name handling."""

    def test_set_player_name(self, parser):
        """Test setting player name."""
        parser.set_player_name("TestHero")

        assert parser.PLAYER_NAME == "TestHero"
        assert parser.PATTERNS is not None

    def test_find_player_name(self, parser, temp_log_file):
        """Test finding player name from log file."""
        parser.set_log_file(temp_log_file)
        player_name = parser.find_player_name()

        assert player_name == "TestHero"

    def test_find_player_name_no_file(self, parser):
        """Test finding player name with no file set."""
        parser.LOG_FILE_PATH = ""
        # This should handle gracefully and return default
        # The actual method will print an error and return None


@pytest.mark.unit
@pytest.mark.data
class TestFilePathValidation:
    """Test file path validation."""

    def test_is_valid_file_path_valid(self, parser, temp_log_file):
        """Test validating a valid file path."""
        assert parser.is_valid_file_path(temp_log_file) is True

    def test_is_valid_file_path_invalid(self, parser):
        """Test validating an invalid file path."""
        assert parser.is_valid_file_path("/nonexistent/path/file.txt") is False

    def test_is_valid_file_path_with_spaces(self, parser, temp_log_file):
        """Test validating a file path with extra spaces."""
        # The method strips spaces
        assert parser.is_valid_file_path(f"  {temp_log_file}  ") is True

    def test_has_log_file_false(self, parser):
        """Test has_log_file when no file is set."""
        parser.LOG_FILE_PATH = ""
        assert parser.has_log_file() is False

    def test_has_log_file_true(self, parser, temp_log_file):
        """Test has_log_file when file is set."""
        parser.set_log_file(temp_log_file)
        assert parser.has_log_file() is True


@pytest.mark.unit
@pytest.mark.data
class TestSessionManagement:
    """Test session management methods."""

    def test_new_session(self, parser):
        """Test creating a new session."""
        parser.clean_variables()
        session = parser.new_session(1000)

        assert isinstance(session, CombatSession)
        assert parser.session_count == 1
        assert parser.combat_session_live is True
        assert len(parser.combat_session_data) == 1

    def test_new_session_auto_name(self, parser):
        """Test new session gets auto-generated name."""
        parser.clean_variables()
        parser.COMBAT_SESSION_NAME = "Session"
        session = parser.new_session(1000)

        assert "Session" in session.name
        assert "1" in session.name

    def test_new_session_user_name(self, parser):
        """Test new session with user-specified name."""
        parser.clean_variables()
        parser.user_session_name = "Boss Fight"
        session = parser.new_session(1000)

        assert "Boss Fight" in session.name

    def test_check_session_no_active(self, parser):
        """Test checking session when none active."""
        parser.clean_variables()
        status = parser.check_session(1000)

        assert status == 0  # No active session

    def test_check_session_active_valid(self, parser):
        """Test checking session that is still valid."""
        parser.clean_variables()
        parser.COMBAT_SESSION_TIMEOUT = 15
        parser.new_session(1000)

        # Within timeout
        status = parser.check_session(1010)
        assert status == 1  # Active and valid

    def test_check_session_timed_out(self, parser):
        """Test checking session that has timed out."""
        parser.clean_variables()
        parser.COMBAT_SESSION_TIMEOUT = 15
        parser.new_session(1000)

        # Beyond timeout (15 seconds)
        status = parser.check_session(1020)
        assert status == -1  # Timed out

    def test_end_current_session(self, parser):
        """Test ending current session."""
        parser.clean_variables()
        parser.new_session(1000)
        parser.combat_session_data[-1].set_end_time(2000)
        parser.end_current_session()

        assert parser.combat_session_live is False
        assert parser.combat_session_data[-1].duration == 1000

    def test_remove_last_session(self, parser):
        """Test removing last session."""
        parser.clean_variables()
        parser.new_session(1000)
        initial_count = parser.session_count

        parser.remove_last_session()

        assert parser.session_count == initial_count - 1
        assert len(parser.combat_session_data) == 0
        assert parser.combat_session_live is False


@pytest.mark.unit
@pytest.mark.data
class TestRewardTracking:
    """Test reward tracking methods."""

    def test_add_exp(self, parser):
        """Test adding experience."""
        parser.clean_variables()
        parser.add_exp(1000)

        assert parser.EXP_VALUE == 1000

    def test_add_inf(self, parser):
        """Test adding influence."""
        parser.clean_variables()
        parser.add_inf(5000)

        assert parser.INF_VALUE == 5000

    def test_get_exp(self, parser):
        """Test getting experience."""
        parser.clean_variables()
        parser.add_exp(1234)

        assert parser.get_exp() == 1234

    def test_get_inf(self, parser):
        """Test getting influence."""
        parser.clean_variables()
        parser.add_inf(5678)

        assert parser.get_inf() == 5678

    def test_accumulate_exp(self, parser):
        """Test accumulating experience."""
        parser.clean_variables()
        parser.add_exp(100)
        parser.add_exp(200)
        parser.add_exp(300)

        assert parser.get_exp() == 600

    def test_accumulate_inf(self, parser):
        """Test accumulating influence."""
        parser.clean_variables()
        parser.add_inf(1000)
        parser.add_inf(2000)
        parser.add_inf(3000)

        assert parser.get_inf() == 6000


@pytest.mark.unit
@pytest.mark.data
class TestGlobalTimeTracking:
    """Test global time tracking."""

    def test_update_global_time_first(self, parser):
        """Test updating global time for first time."""
        parser.clean_variables()
        parser.update_global_time(5000)

        assert parser.GOBAL_START_TIME == 5000
        assert parser.GLOBAL_CURRENT_TIME == 5000

    def test_update_global_time_subsequent(self, parser):
        """Test updating global time after initial."""
        parser.clean_variables()
        parser.update_global_time(5000)
        parser.update_global_time(6000)

        assert parser.GOBAL_START_TIME == 5000  # Unchanged
        assert parser.GLOBAL_CURRENT_TIME == 6000  # Updated

    def test_get_log_duration(self, parser):
        """Test calculating log duration."""
        parser.clean_variables()
        parser.update_global_time(1000)
        parser.update_global_time(5000)

        duration = parser.get_log_duration()
        assert duration == 4000

    def test_add_global_combat_duration(self, parser):
        """Test adding to global combat duration."""
        parser.clean_variables()
        parser.add_global_combat_duration(100)
        parser.add_global_combat_duration(200)

        assert parser.global_combat_duration == 300


@pytest.mark.unit
@pytest.mark.data
class TestRegexPatternUpdate:
    """Test regex pattern updating with player name."""

    def test_update_regex_player_name(self, parser):
        """Test updating regex patterns with player name."""
        updated = parser.update_regex_player_name("TestHero")

        assert isinstance(updated, dict)
        assert len(updated) > 0

        # Check that PLAYER_NAME is replaced
        for key, pattern in updated.items():
            assert "PLAYER_NAME" not in pattern.pattern
