"""
Unit tests for the pseudopets module.

This module tests the pseudopets data and the is_pseudopet function
which identifies pseudo-pets in City of Heroes.
"""

import pytest
from data.pseudopets import PSEUDOPETS, is_pseudopet


@pytest.mark.unit
@pytest.mark.data
class TestPseudopetsList:
    """Test the PSEUDOPETS list."""

    def test_pseudopets_is_list(self):
        """Test that PSEUDOPETS is a list."""
        assert isinstance(PSEUDOPETS, list)

    def test_pseudopets_not_empty(self):
        """Test that PSEUDOPETS list is not empty."""
        assert len(PSEUDOPETS) > 0

    def test_pseudopets_contains_expected_entries(self):
        """Test that PSEUDOPETS contains known pseudo-pets."""
        expected_pseudopets = [
            "Caltrops",
            "Lightning Rod",
            "Oil Slick",
            "Trip Mine",
            "Rain of Fire",
            "Burn",
        ]

        for pet in expected_pseudopets:
            assert pet in PSEUDOPETS, f"{pet} should be in PSEUDOPETS"

    def test_pseudopets_contains_judgement_powers(self):
        """Test that PSEUDOPETS contains Judgement incarnate powers."""
        judgement_powers = [
            "Ion Core Final Judgement",
            "Ion Judgement",
            "Ion Radial Judgement",
        ]

        for power in judgement_powers:
            assert power in PSEUDOPETS, f"{power} should be in PSEUDOPETS"

    def test_pseudopets_contains_chain_induction(self):
        """Test that PSEUDOPETS contains Chain Induction variations."""
        assert "Chain Induction" in PSEUDOPETS
        assert "Chain Induction Jump 1" in PSEUDOPETS
        assert "Chain Induction Jump 10" in PSEUDOPETS

    def test_pseudopets_all_strings(self):
        """Test that all entries in PSEUDOPETS are strings."""
        for pet in PSEUDOPETS:
            assert isinstance(pet, str), f"Entry {pet} should be a string"

    def test_pseudopets_no_duplicates(self):
        """Test that PSEUDOPETS contains no duplicate entries."""
        assert len(PSEUDOPETS) == len(set(PSEUDOPETS)), "PSEUDOPETS should not contain duplicates"


@pytest.mark.unit
@pytest.mark.data
class TestIsPseudopetFunction:
    """Test the is_pseudopet function."""

    def test_is_pseudopet_caltrops(self):
        """Test that Caltrops is identified as a pseudopet."""
        assert is_pseudopet("Caltrops") is True

    def test_is_pseudopet_lightning_rod(self):
        """Test that Lightning Rod is identified as a pseudopet."""
        assert is_pseudopet("Lightning Rod") is True

    def test_is_pseudopet_oil_slick(self):
        """Test that Oil Slick is identified as a pseudopet."""
        assert is_pseudopet("Oil Slick") is True

    def test_is_pseudopet_trip_mine(self):
        """Test that Trip Mine is identified as a pseudopet."""
        assert is_pseudopet("Trip Mine") is True

    def test_is_pseudopet_judgement(self):
        """Test that Judgement powers are identified as pseudopets."""
        assert is_pseudopet("Ion Core Final Judgement") is True
        assert is_pseudopet("Ion Judgement") is True
        assert is_pseudopet("Ion Radial Judgement") is True

    def test_is_pseudopet_chain_induction(self):
        """Test that Chain Induction is identified as a pseudopet."""
        assert is_pseudopet("Chain Induction") is True
        assert is_pseudopet("Chain Induction Jump 1") is True
        assert is_pseudopet("Chain Induction Jump 5") is True

    def test_is_not_pseudopet_normal_power(self):
        """Test that normal powers are not identified as pseudopets."""
        assert is_pseudopet("Fire Blast") is False
        assert is_pseudopet("Ice Bolt") is False
        assert is_pseudopet("Healing Aura") is False

    def test_is_not_pseudopet_real_pet(self):
        """Test that real pet names are not identified as pseudopets."""
        assert is_pseudopet("Phantom") is False
        assert is_pseudopet("Demon Prince") is False
        assert is_pseudopet("Battle Drone") is False

    def test_is_pseudopet_case_sensitive(self):
        """Test that is_pseudopet is case-sensitive."""
        assert is_pseudopet("Caltrops") is True
        assert is_pseudopet("caltrops") is False
        assert is_pseudopet("CALTROPS") is False

    def test_is_pseudopet_empty_string(self):
        """Test that empty string is not a pseudopet."""
        assert is_pseudopet("") is False

    def test_is_pseudopet_partial_match(self):
        """Test that partial matches are not identified as pseudopets."""
        assert is_pseudopet("Caltrop") is False
        assert is_pseudopet("Lightning") is False
        assert is_pseudopet("Oil") is False

    def test_is_pseudopet_with_spaces(self):
        """Test pseudopets with spaces in their names."""
        assert is_pseudopet("Oil Slick Arrow") is False  # Note: space before Oil in list
        assert is_pseudopet(" Oil Slick Arrow") is True  # Has leading space in PSEUDOPETS

    def test_is_pseudopet_all_listed_entries(self):
        """Test that all entries in PSEUDOPETS return True."""
        for pet in PSEUDOPETS:
            assert is_pseudopet(pet) is True, f"{pet} should be identified as a pseudopet"


@pytest.mark.unit
@pytest.mark.data
class TestPseudopetsEdgeCases:
    """Test edge cases for pseudopets."""

    def test_pseudopet_with_leading_space(self):
        """Test that the entry with leading space is handled correctly."""
        # There's " Oil Slick Arrow" in the list with a leading space
        assert is_pseudopet(" Oil Slick Arrow") is True

    def test_pseudopet_variations(self):
        """Test various pseudopet variations."""
        # Test Faraday Cage
        assert is_pseudopet("Faraday Cage") is True

        # Test Enflame
        assert is_pseudopet("Enflame") is True

        # Test Incandescence
        assert is_pseudopet("Incandescence") is True

        # Test Tar Patch
        assert is_pseudopet("Tar Patch") is True

    def test_weather_pseudopets(self):
        """Test weather-based pseudopets."""
        assert is_pseudopet("Freezing Rain") is True
        assert is_pseudopet("Sleet") is True
        assert is_pseudopet("Water Spout") is True

    def test_fire_pseudopets(self):
        """Test fire-based pseudopets."""
        assert is_pseudopet("Rain of Fire") is True
        assert is_pseudopet("Burn") is True

    def test_poison_pseudopets(self):
        """Test poison-based pseudopets."""
        assert is_pseudopet("Poison Trap") is True
        assert is_pseudopet("Poison Gas") is True

    def test_device_pseudopets(self):
        """Test device/gadget pseudopets."""
        assert is_pseudopet("Detonator") is True
        assert is_pseudopet("Triage Beacon") is True

    def test_all_ion_judgement_variants(self):
        """Test all Ion Judgement variants in the list."""
        ion_variants = [
            "Ion Core Final Judgement",
            "Ion Core Judgement",
            "Ion Judgement",
            "Ion Partial Core Judgement",
            "Ion Partial Radial Judgement",
            "Ion Radial Final Judgement",
            "Ion Radial Judgement",
            "Ion Total Core Judgement",
            "Ion Total Radial Judgement",
        ]

        for variant in ion_variants:
            assert is_pseudopet(variant) is True, f"{variant} should be a pseudopet"

    def test_all_chain_induction_jumps(self):
        """Test all Chain Induction jump numbers."""
        for i in range(1, 11):
            assert is_pseudopet(f"Chain Induction Jump {i}") is True


@pytest.mark.unit
@pytest.mark.data
class TestPseudopetsDataQuality:
    """Test data quality of the PSEUDOPETS list."""

    def test_no_none_values(self):
        """Test that PSEUDOPETS contains no None values."""
        assert None not in PSEUDOPETS

    def test_no_empty_strings(self):
        """Test that PSEUDOPETS contains no empty strings."""
        assert "" not in PSEUDOPETS

    def test_consistent_formatting(self):
        """Test that entries follow consistent formatting."""
        for pet in PSEUDOPETS:
            # Should not start or end with spaces (except the one known case)
            if pet != " Oil Slick Arrow":
                assert pet == pet.strip(), f"{pet} has leading/trailing spaces"
