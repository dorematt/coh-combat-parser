import re

'''The following patterns are used to parse the combat log line data. The patterns are matched to a particular event occuring within that line '''
PATTERNS = {
    "player_ability_activate": re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) You activated the (?P<ability>.+?) power\."
    ),
    "player_hit_roll": re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<outcome>HIT|MISS(?:ED)?) (?P<target>[^.!]+)(?:!!|!) Your (?P<ability>[^.]+) power (?:had a .*?chance to hit, you rolled a (\d+\.\d+)|was forced to hit by streakbreaker)\."
    ),
    "player_pet_hit_roll": re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<pet_name>[^:]+?):? * (?P<outcome>HIT|MISS(?:ED)?) (?P<target>[^.!]+)(?:!!|!) Your (?P<ability>[^.]+) power (?:had a .*?chance to hit, you rolled a (\d+\.\d+)|was forced to hit by streakbreaker)\."
    ),
    "player_damage": re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?:PLAYER_NAME:  )?(?:You (?:hit|hits you with their)|HIT) (?P<target>[^:]+) with your (?P<ability>[^:]+)(?:: (?P<ability_desc>(?:Recharge/Chance [\w\s]+|[\w\s]+)))? for (?P<damage_value>[\d.]+) points of (?P<damage_type>[^\d]+) damage(?: \((?P<damage_flair>[^\)]+)\))?(?: over time)?\.*"
    ),
    "player_pet_damage": re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<pet_name>[^:]+?):? * You hit (?P<target>[^:]+) with your (?P<ability>[^:]+)(?:: (?P<ability_desc>(?:Recharge/Chance [\w\s]+|[\w\s]+)))? for (?P<damage_value>[\d.]+) points of (?P<damage_type>[^\d]+) damage(?: \((?P<damage_flair>[^\)]+)\))?(?: over time)?\.*"
    ),
    "foe_pet_hit_roll": re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2})\s"
        r"(?P<time>\d{2}:\d{2}:\d{2})\s"
        r"(?P<pet_name>.+?):\s+"
        r"(?P<enemy>.+?)\s"
        r"(?:HITS|MISSES)!?\s"
        r"(?:their\s)?"
        r"(?P<ability>.+?)\s"
        r"power had a\s"
        r"(?P<chance>\d{1,3}(?:\.\d{2})?)%\s"
        r"chance to hit(?:, but| and) rolled a\s"
        r"(?P<roll>\d{1,3}\.\d{2})\."
    ),
    "foe_hit_roll": re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2})\s"
        r"(?P<time>\d{2}:\d{2}:\d{2})\s"
        r"(?P<enemy>.+?)\s"
        r"(?:HITS|MISSES)!?\s"
        r"(?:you!\s)?"
        r"(?:their\s)?"
        r"(?P<ability>.+?)\s"
        r"power had a\s"
        r"(?P<chance>\d{1,3}(?:\.\d{2})?)%\s"
        r"chance to hit(?:, but| and) rolled a\s"
        r"(?P<roll>\d{1,3}\.\d{2})\."
    ),
    "foe_autohit": re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2})\s"
        r"(?P<time>\d{2}:\d{2}:\d{2})\s"
        r"(?P<enemy>.+?)\s"
        # Specifically match 'HITS you!' for these events.
        r"HITS\syou!\s"
        r"(?:their\s)?"
        r"(?P<ability>.+?)\s"
        r"power was autohit\."
    ),
    "foe_damage": re.compile(
         r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<enemy>.+?) hits you with their (?P<ability>[^:]+)(?:: (?P<ability_desc>(?:Recharge/Chance [\w\s]+|[\w\s]+)))? for (?P<damage_value>[\d.]+) points of (?P<damage_type>[^\d]+) damage(?: \((?P<damage_flair>[^\)]+)\))?(?: over time)?\.*"
    ),
    "foe_damage_pet": re.compile(
         r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<pet_name>[^:]+?):? * (?P<enemy>.+?) hits you with their (?P<ability>[^:]+)(?:: (?P<ability_desc>(?:Recharge/Chance [\w\s]+|[\w\s]+)))? for (?P<damage_value>[\d.]+) points of (?P<damage_type>[^\d]+) damage(?: \((?P<damage_flair>[^\)]+)\))?(?: over time)?\.*"
    ),
    "reward_gain_both": re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) You gain (?P<exp_value>\d{1,3}(,\d{3})*(\.\d+)?) experience and (?P<inf_value>\d{1,3}(,\d{3})*(\.\d+)?) (?:influence|information|infamy)\.*"
    ),
    "reward_gain_exp": re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) You gain (?P<exp_value>\d+(,\d{3})*|\d+) experience\."
    ),
    "reward_gain_inf": re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) You gain (?P<inf_value>\d+(,\d{3})*|\d+) (?:influence|information|infamy)\."
    ),
    #"reward_gain_item": re.compile(
    #    r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) You recieve (?P<item_name>\d+(,\d{3})*|\d+) (?:influence|information|infamy)\."
    #),
    # "player_healing_recieved": re.compile(
    #     r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<healer>.+?) (?:heals|heal) (?:you|PLAYER_NAME) with their (?P<ability>.+?) for (?P<healing_value>[\d.]+) health points(?: over time)?\.*"
    # ),
    # This pattern should capture endurance recovery. An example line for endurance recovery is needed to refine this pattern.
    # "endurance_recovery": re.compile(
    #     r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<restorer>.+?) (?:restores|restore) (?:your|PLAYER_NAME's) endurance by (?P<endurance_value>[\d.]+) points\.*"
    # ),
    "player_name": re.compile( # Matches a welcome message that includes the player name
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (Welcome to City of |Now entering the Rogue Isles).*?, (?P<player_name>.+?)!"
    ),
    "player_name_backup": re.compile( # Backup method to capture player name from Stamina autohit, which should be pretty universal across characters
         r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<outcome>HIT|MISS(?:ED)?) (?P<player_name>[^.!]+)(?:!!|!) Your (Stamina|Health) power is autohit."
    ),
    "command": re.compile( # Matches a command message in chat
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) \[(?:Local|SuperGroup)\] (?P<player>.+?): .*?##(?P<command>\S+) (?P<value>.*)"
    ),
}

'''This pattern was intended to be used to quickly grab the data and time from the line without having to loop through the whole list of patterns.  It is not currently used.'''
PATTERN_DATETIME = {
    "date_time": re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2})"
    )
}