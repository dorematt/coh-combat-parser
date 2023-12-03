import re

# Define the regular expressions for each type of log entry
regex_patterns = {
    "player_hit_roll": re.compile(
       r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<outcome>HIT|MISS(?:ED)?) (?P<target>.+?)(?:!!|!) Your (?P<ability>.+?) power (had a .*?chance to hit|was forced to hit by streakbreaker)\."
    ),
    "damage_component": re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?:Emet Selch:  )?(?:You hit|hits you with their) (?P<target>.+?) with your (?P<ability>.+?) for (?P<damage_value>[\d.]+) points of (?P<damage_type>\w+) damage(?: over time)?\.*"
    ),
    #"foe_hit_roll": re.compile(
    #    r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<enemy>.+?) (?P<outcome>?:HIT|MISSES you!|HIT |MISS(?:ED)?) (?:(?P<ability>.+?) power had a .* to hit and rolled a .*\.?)?"
    #),
    "foe_damage": re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<enemy>.+?) hits you with their (?P<ability>.+?) for (?P<damage_value>[\d.]+) points of (?P<damage_type>\w+) damage\.*"
    ),
    "exp_gain": re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) You gain (?P<exp_value>\d+) experience\.*"
    ),
    "influence_gain": re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) .*? and (?P<inf_value>\d+) (influence|infamy|information)\.*"
    ),
    "healing": re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<healer>.+?) (?:heals|heal) (?:you|Emet Selch) with their (?P<ability>.+?) for (?P<healing_value>[\d.]+) health points(?: over time)?\.*"
    ),
    # This pattern should capture endurance recovery. An example line for endurance recovery is needed to refine this pattern.
    "endurance_recovery": re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<restorer>.+?) (?:restores|restore) (?:your|Emet Selch's) endurance by (?P<endurance_value>[\d.]+) points\.*"
    ),
}


# Test regex extraction with provided log lines
def test_regex_extraction(log_lines, patterns):
    extracted_data = []
    for line in log_lines:
        #print('Checking Line:', line)
        for key, regex in patterns.items():
            match = regex.match(line)
            if match:
                # Add the matched data along with the log entry type
                print('Extracted:',key, match.groupdict())
                extracted_data.append((key, match.groupdict()))
                continue
    return extracted_data

# Using the initial snippet as test data
sample_log_lines = [
    '2023-11-18 14:49:48 Readying Void Total Radial Judgement.\n',
    '2023-11-18 14:49:48 Sweet Radiation heals you with their Ground Zero for 9.37 health points over time.\n',
    '2023-11-18 14:49:49 You hit Lattice with your Degenerative Interface for 12.03 points of Toxic damage over time.\n',
    '2023-11-18 14:49:49 Thorn has defeated Jack Frost\n',
    '2023-11-18 14:49:49 You Stun Lattice with your Inky Aspect.\n',
    '2023-11-18 14:49:49 Emet Selch hits you with their Inky Aspect for 4.72 points of unresistable Special damage.\n',
    '2023-11-18 14:49:49 MISSED Lattice!! Your Inky Aspect power had a 95.00% chance to hit, you rolled a 95.27.\n',
    '2023-11-18 14:49:49 Sweet Radiation heals you with their Ground Zero for 9.37 health points over time.\n',
    '2023-11-18 14:49:51 You hit Lattice with your Void Total Radial Judgement for 641.12 points of Negative Energy damage.\n',
    '2023-11-18 14:49:51 You hit Lattice with your Doublehit for 38.91 points of Energy damage.\n',
    '2023-11-18 14:49:53 HIT Lattice! Your Black Dwarf Mire power had a 95.00% chance to hit, you rolled a 68.99.\n',
    '2023-11-18 14:50:03 Lattice MISSES! Crystal Shards power had a 11.25% chance to hit, but rolled a 62.66.\n',
    '2023-11-18 14:49:57 You hit Lattice with your Dark Nova Bolt for 264.55 points of Negative Energy damage.\n',
    '2023-11-18 14:49:58 Thorn HITS you! Thorn power had a 95.00% chance to hit and rolled a 22.43.\n',
    '2023-11-18 14:49:57 You are healed by your Power Transfer: Chance to Heal Self for 91.03 health points.\n',
    '2023-11-18 14:50:04 Emet Selch hits you with their Performance Shifter: Chance for +Endurance granting you 11 points of endurance.\n',
    '2023-11-18 14:50:07 HIT Lattice! Your Dark Detonation power was forced to hit by streakbreaker.'
]


# Perform the test extraction
test_regex_extraction(sample_log_lines, regex_patterns)