"""
No Hit Roll Abilities

This module contains a list of abilities that are known to be auto-hit or otherwise
do not have hit roll events recorded in the combat log file, but should still be
treated as regular damaging powers for accuracy and hit calculation purposes.

These abilities typically include:
- Auto-hit powers (like some DoT auras)
- Powers with special mechanics that bypass hit rolls
- Interface damage procs
- Certain toggles and auras

When the parser encounters damage from these abilities without a corresponding hit roll,
it knows to treat them specially in hit/miss statistics.
"""

NO_HIT_ABILITIES = [
    "Interface",
    "Shifting Tides"
]


def is_no_hit_ability(ability_name):
    """
    Check if an ability is known to not have hit roll events in the log.

    :param ability_name: The name of the ability to check
    :return: True if the ability is in the no-hit list, False otherwise
    """
    return any(no_hit in ability_name for no_hit in NO_HIT_ABILITIES)
