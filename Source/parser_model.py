import re
from datetime import datetime
import random

class Parser:
    '''Extracts data from log lines using regex patterns, Will return a list of tuples containing the log entry type and a dictionary of the extracted data.'''
    PATTERNS = {
        "player_hit_roll": re.compile(
            r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<outcome>HIT|MISS(?:ED)?) (?P<target>[^.!]+)(?:!!|!) Your (?P<ability>[^.]+) power (?:had a .*?chance to hit, you rolled a (\d+\.\d+)|was forced to hit by streakbreaker)\."
        ),
        "player_damage": re.compile(
            r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?:PLAYER_NAME:  )?(?:You (?:hit|hits you with their)|HIT) (?P<target>[^:]+) with your (?P<ability>[^:]+)(?:: (?P<ability_desc>[\w\s]+))? for (?P<damage_value>[\d.]+) points of (?P<damage_type>[^\d]+) damage(?: over time)?\.*"
        ),
       # "foe_hit_roll": re.compile(
       #     r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<enemy>.+?) (?P<outcome>HIT|MISSES you!|HIT |MISS(?:ED)?) (?:(?P<ability>.+?) power had a .* to hit and rolled a .*\.?)?"
       # ),
       # "foe_damage": re.compile(
       #     r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<enemy>.+?) hits you with their (?P<ability>.+?) for (?P<damage_value>[\d.]+) points of (?P<damage_type>\w+) damage\.*"
       # ),
        "reward_gain_both": re.compile(
            r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) You gain (?P<exp_value>\d{1,3}(,\d{3})*(\.\d+)?) experience and (?P<inf_value>\d{1,3}(,\d{3})*(\.\d+)?) (?:influence|information|infamy)\.*"
        ),
        "reward_gain_exp": re.compile(
            r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) You gain (?P<exp_value>\d+(,\d{3})*|\d+) experience\."
        ),
        "reward_gain_inf": re.compile(
            r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) You gain (?P<inf_value>\d+(,\d{3})*|\d+) (?:influence|information|infamy)\."
        ),
       # "influence_gain": re.compile(
       #     r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) .*? and (?P<inf_value>\d+) (influence|infamy|information)\.*"
       # ),
       # "healing": re.compile(
       #     r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<healer>.+?) (?:heals|heal) (?:you|PLAYER_NAME) with their (?P<ability>.+?) for (?P<healing_value>[\d.]+) health points(?: over time)?\.*"
       # ),
        # This pattern should capture endurance recovery. An example line for endurance recovery is needed to refine this pattern.
       # "endurance_recovery": re.compile(
       #     r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<restorer>.+?) (?:restores|restore) (?:your|PLAYER_NAME's) endurance by (?P<endurance_value>[\d.]+) points\.*"
       # ),
    }

    def __init__(self, player_name):

        self.line_counter = 0

        #Assign the player name to the class
        self.PLAYER_NAME = player_name
        print("Player Name Set: ", self.PLAYER_NAME)
        self.PATTERNS = self.update_regex_player_name(player_name)

        # Set Exp and Influence values
        self.EXP_VALUE = 0
        self.INF_VALUE = 0
        
        # create a key-value list of abilities
        self.Abilities = {}
        self.START_TIME = 0 # Stores the timestamp of the first event as an int
        self.current_time = 0 # Stores the latest timestamp as an int
    
    def update_regex_player_name(self, player_name):
        updated_patterns = {}
        for key, regex in self.PATTERNS.items():
            updated_pattern = regex.pattern.replace('PLAYER_NAME', player_name)
            updated_regex = re.compile(updated_pattern)
            print('Updated Regex: ', updated_regex)
            updated_patterns[key] = updated_regex
        return updated_patterns
    
    def check_line_extract_event(self, log_line):
        '''Extracts data from a log line using regex patterns, returns a tuple containing the log entry type and a dictionary of the extracted data.'''
        for key, regex in self.PATTERNS.items():
            match = regex.match(log_line)
            if match:
                #print('Matched Event: ', key)
                #print(match.groupdict())
                #self.interpret_event(key, match.groupdict())
                return (key, match.groupdict())
        return '',[]

    def interpret_event(self, event, data):
        '''Interprets the event generated and creates or updates the corresponding data objects'''

        # Update the current time
        self.update_time(self.convert_timestamp(data["date"], data["time"]))

        if event == "player_hit_roll":
            self.handle_event_player_hit_roll(data)
        elif event == "player_damage":
            self.handle_event_player_damage(data)
        elif event == "reward_gain_both" or event == "reward_gain_exp" or event == "reward_gain_inf":

            if data.get("exp_value") is None:
                data["exp_value"] = ""
            if data.get("inf_value") is None: 
                data["inf_value"] = ""
            self.handle_event_reward_gain(data)


    def handle_event_player_damage(self, data):
        '''Handles a player damage event'''
        # First, ignore any matches that is the player hitting themselves
        if data["target"] == self.PLAYER_NAME:
            # print('Player hit themselves, with ', data["ability"] , '. Ignoring')
            return
        
        # Check for ability in directory, if it doesn't exist, create it
        if data["ability"] not in self.Abilities:
            self.Abilities[data["ability"]] = Ability(data["ability"])
            #self.Abilities[data["ability"]].ability_used(True)
            #print('Ability Created: ', self.Abilities[data["ability"]].name)

        active_ability = self.Abilities[data["ability"]]
        active_ability.add_damage(DamageComponent(data["damage_type"], data["damage_value"]))
        #print('Ability Executed:', active_ability.name)

    def handle_event_player_hit_roll(self, data):
        '''Handles a player hit roll event'''
        # First, ignore any matches that is the player hitting themselves
        if data["target"] == self.PLAYER_NAME:
            print('Player hit themselves, with ', data["ability"] , '. Ignoring')
            return
        
        # Check for ability in directory, if it doesn't exist, create it
        if data["ability"] not in self.Abilities:
            self.Abilities[data["ability"]] = Ability(data["ability"])
            #self.Abilities[data["ability"]].ability_used(True)
            #print('Ability Created: ', self.Abilities[data["ability"]].name)

        active_ability = self.Abilities[data["ability"]]
        active_ability.ability_used(data["outcome"] == "HIT")
        #print('Ability Executed:', active_ability.name)

    def handle_event_reward_gain(self, data):
        #return
        '''Handles a reward gain event'''
        #check
        exp_value = data["exp_value"].replace(',', '') # remove commas from the string
        exp_value = 0 if exp_value == "" else int(exp_value) # convert to int

        inf_value = data["inf_value"].replace(',', '') # remove commas from the string and convert to 
        inf_value = 0 if inf_value == "" else int(inf_value)

        self.add_inf(inf_value)
        self.add_exp(exp_value)


    def convert_timestamp(self, date, time):
        '''Converts a timestamp from the log file into a datetime object and returns an int representing the time in seconds'''
        # Convert the date and time into a datetime object
        timestamp = datetime.strptime(date + " " + time, "%Y-%m-%d %H:%M:%S")
        # Convert the datetime object into an int representing the time in seconds
        timestamp = int(timestamp.strftime("%H%M%S"))
        return timestamp
    
    def update_time(self, timestamp):
        '''Checks if the timestamp is the first event, if it is, set the start time to the timestamp, otherwise update the current time'''
        if self.START_TIME == 0:
            self.START_TIME = timestamp
        self.current_time = timestamp
    
    def get_log_duration(self):
        '''Calculates the duration of the log file'''
        return self.current_time - self.START_TIME
    def get_dps(self, duration):
        '''Calculates the DPS for the player'''
        total_damage = 0
        for ability in self.Abilities:
            total_damage += self.Abilities[ability].get_total_damage()
        return round(total_damage / duration, 2)
    
    def add_exp(self, exp_value):
        '''Adds the exp value to the total exp'''
        self.EXP_VALUE += exp_value
    def add_inf(self, inf_value):
        '''Adds the inf value to the total inf'''
        self.INF_VALUE += inf_value
    def get_exp(self):
        '''Returns the total exp'''
        return self.EXP_VALUE
    def get_inf(self):
        '''Returns the total inf'''
        return self.INF_VALUE

    def run_test_data(self, log_lines):
        
        extracted_data = []
        for line in log_lines:
            extracted_data = self.check_line_extract_event(line)
            print(extracted_data)
        return extracted_data


class Ability:
    '''Stores data about an ability used'''
    def __init__(self, name, hit=None):
        self.name = name
        self.count = 0 if hit is None else 1
        self.hits = 1 if hit is True else 0
        self.damage = [] 

    def add_damage(self, damage_component):
        '''Adds a damage component to the ability'''
        # Check if damage type is already in the ability, if it is, add the damage to the existing component
        for component in self.damage:
            if component.type == damage_component.type:
                component.add_damage(damage_component.type, damage_component.total_damage)
                return
        self.damage.append(damage_component)
        self.damage[-1].add_damage(damage_component.type, damage_component.total_damage)
        #print('Added new Damage Component: ', damage_component.type, 'to Ability: ', self.name)
    
    def ability_used(self, hit):
        self.count += 1
        
        # If the ability hit, increment the hit counter
        if hit:
            self.hits += 1
    
    def get_name(self):
        '''Returns the name of the ability'''
        return self.name
    
    def get_total_damage(self):
        '''Calculates the total damage for the ability'''
        sum = 0
        for component in self.damage:
            sum += component.get_damage()
            #print('Damage Component for ', self.name,': ', component.type,'|', component.total_damage,'|', component.count)
        return round(sum,2)
    
    def get_average_damage(self):
        '''Calculates the average damage for the ability'''
        if self.count > 1:
            return round(self.get_total_damage() / self.count,2)
        else:
            return self.get_total_damage()
    
    def get_accuracy(self):
        '''Calculates the accuracy for the ability'''
        if self.hits == 0 or self.count == 0:
            return 0
        return round((self.hits / self.count) * 100,2)
    
    def get_dps(self, duration):
        '''Calculates the DPS for the ability based off of the damage components'''
        dps = 0
        for component in self.damage:
            dps += component.get_dps(duration)
        return round(dps,2)

class DamageComponent:
    '''Stores data about a damage component'''
    def __init__(self, type, value : float):
        self.count = 0
        self.type = type
        self.total_damage = float(value)
        self.highest_damage = 0
        self.lowest_damage = 0
    
    def add_damage(self, type, value : float):
        '''Adds damage value to the damage component'''
        self.count += 1
        self.total_damage += value
        self.total_damage = round(self.total_damage, 2)
        if value > self.highest_damage or self.highest_damage == 0:
            self.highest_damage = value
        if value < self.lowest_damage or self.lowest_damage == 0:
            self.lowest_damage = value
    
    def get_dps(self, duration):
        '''Calculates the DPS for the damage component'''
        return round(self.total_damage / duration, 2)
    def get_average_damage(self):
        '''Calculates the average damage for the damage component'''
        return round(self.total_damage / self.count,2)
    def get_highest_damage(self):
        '''Returns the highest damage for the damage component'''
        return self.highest_damage
    def get_lowest_damage(self):
        '''Returns the lowest damage for the damage component'''
        return self.lowest_damage
    def get_damage(self):
        '''Returns the total damage for the damage component'''
        return self.total_damage
    def get_count(self):
        '''Returns the number of times the damage component has been used'''
        return self.count
    
class Target:
    '''Stores information and data about a target'''        
    def __init__(self, name):
        pass


def _test_hit_rolls():
        sample_hit_lines = [
    '2023-11-18 14:49:49 MISSED Ugly Face Mother!! Your Inky Aspect power had a 95.00% chance to hit, you rolled a 95.27.\n',
    '2023-11-18 14:49:51 HIT Thorn! Your Void Total Radial Judgement power had a 95.00% chance to hit, you rolled a 41.38.\n',
    '2023-11-18 14:49:51 HIT Lattice! Your Void Total Radial Judgement power had a 95.00% chance to hit, you rolled a 59.66.\n',
    '2023-11-18 14:49:53 HIT Your Worst Nightmare! Your Black Dwarf Mire power had a 95.00% chance to hit, you rolled a 68.99.\n',
    '2023-11-18 14:49:53 HIT Lattice! Your Black Dwarf Mire power had a 95.00% chance to hit, you rolled a 54.51.\n',
    '2023-11-18 14:49:54 MISSED Thug!! Your Inky Aspect power had a 95.00% chance to hit, you rolled a 99.40.\n',
    '2023-11-18 14:50:07 HIT Mighty Golem! Your Dark Detonation power was forced to hit by streakbreaker.\n',
    '2023-11-18 14:49:55 HIT Lattice! Your Dark Nova Blast power was forced to hit by streakbreaker.\n',
    '2023-11-18 14:49:56 HIT Lattice! Your Dark Nova Emanation power was forced to hit by streakbreaker.\n',
    '2023-11-18 14:50:00 MISSED Lattice!! Your Dark Nova Bolt power had a 95.00% chance to hit, you rolled a 95.37.\n',
    '2023-11-18 14:50:07 MISSED Dark Servant!! Your Dark Detonation power had a 95.00% chance to hit, you rolled a 95.99.'

]   
    
        print('\n \n', "---- STARTING HIT ROLL SAMPLE DATA TEST -----", '\n \n')
        #test extraction and interpretation of hit roll data
        for line in sample_hit_lines:
            event, data = self.check_line_extract_event(line)
            #self.line_counter += 1
            if event is not "":
                print(event, data)
                self.interpret_event(event, data)

def _test_damage_lines():
        sample_damage_lines = [
        "2023-11-18 14:50:23 You hit Lattice with your Black Dwarf Smite for 211.94 points of Smashing damage.",
        "2023-11-18 14:50:23 You hit Lattice with your Black Dwarf Smite for 378.47 points of Negative Energy damage.",
        "2023-11-18 14:50:23 You hit D0xx3r L0rD with your Gladiator's Strike: Chance for Smashing Damage for 246.66 points of Smashing damage.",
        "2023-11-18 14:50:18 You hit Emet Selch with your Inky Aspect for 4.72 points of unresistable Special damage.",
        "2023-11-18 14:50:19 You hit Lattice with your Bombardment: Chance for Fire Damage for 207.12 points of Fire damage.",
        "2023-11-18 14:50:19 You hit Big Birb with your Dark Nova Detonation for 352.19 points of Negative Energy damage.",
        "2023-11-18 14:50:19 You hit Mighty Golem with your Doublehit for 59.35 points of Energy damage.",
        "2023-11-18 14:50:20 You hit Lattice with your Dark Nova Emanation for 517.01 points of Negative Energy damage.",
        "2023-11-18 14:50:20 You hit Lattice with your Positron's Blast: Chance for Energy Damage for 142.71 points of Energy damage.",
        "2023-11-18 14:50:21 You hit Mega MInd with your Doublehit for 238.07 points of Energy damage.",
        "2023-11-18 14:50:23 You hit Thorn with your Black Dwarf Smite for 211.94 points of Smashing damage.",
        "2023-11-18 14:50:23 You hit Thorn with your Black Dwarf Smite for 378.47 points of Negative Energy damage.",
        "2023-11-18 14:50:23 You hit Thorn with your Gladiator's Strike: Chance for Smashing Damage for 246.66 points of Smashing damage.",
        "2023-11-18 14:50:23 You hit Thorn with your Mako's Bite: Chance for Lethal Damage for 176.18 points of Lethal damage.",
        "2023-11-18 14:50:23 You hit Thorn with your Touch of Death: Negative Energy Damage for 140.94 points of Negative Energy damage.",
        "2023-11-18 14:50:23 You hit Thorn with your Ice Mistral's Torment: Chance for Cold Damage for 176.18 points of Cold damage.",
        "2023-11-18 14:50:23 You hit Thorn with your Doublehit for 111.07 points of Energy damage.",
        "2023-11-18 14:50:23 You hit Lattice with your Dark Detonation for 186.33 points of Negative Energy damage.",
        "2023-11-18 14:50:23 You hit Thorn with your Dark Detonation for 266.9 points of Negative Energy damage.",
        "2023-11-18 14:50:23 You hit Thorn with your Degenerative Interface for 10.88 points of Toxic damage over time.",
    ]


        print('\n \n', "---- STARTING DAMAGE SAMPLE DATA TEST -----", '\n \n')
        #test extraction and interpretation of hit roll data
        for line in sample_damage_lines:
            event, data = self.check_line_extract_event(line)
            #self.line_counter += 1
            if event is not "":
                print(event, data)
                self.interpret_event(event, data)

def _test_reward_lines():
    sample_reward_lines = [
    '2023-11-18 14:48:05 You gain 1,525 experience and 763 influence.',
    '2023-11-18 14:48:15 You gain 2,922 experience and 1,461 influence.',
    '2023-11-18 14:49:16 You gain 67 experience and 47 influence.',
    '2023-11-18 14:49:10 You gain 2 experience.',
    '2023-11-18 14:50:16 You gain 47 influence.',
    '2023-11-18 14:50:16 You gain 148 influence',
    '2023-11-19 14:50:16 You gain 2,445 experience.',
    '2023-11-19 14:52:11 You gain 124,212,130 experience.',
    '2023-11-19 14:52:11 You gain 136,288,199 influence.',
    '2023-11-19 14:52:11 You gain 124,212,130 experience and 32,322,103 influence.'
    ]
    print('\n \n', "---- STARTING REWARD SAMPLE DATA TEST -----", '\n \n')

    for line in sample_reward_lines:
        event, data = self.check_line_extract_event(line)
        #self.line_counter += 1
        if event is not "":
            print(event, data)
            self.interpret_event(event, data)

def _test_log_file():
    print('\n \n', "---- STARTING LOG FILE DATA TEST -----", '\n \n')
#Open text file with test data, similarly test extraction data
    with open('C:\\Users\\mdore\\OneDrive\\02_Documents\\02_SCRIPTS\\CoH_Log_Parser\\coh_logfile_snippet.txt', 'r') as file:
        for line in file:
            event, data = self.check_line_extract_event(line)
            self.line_counter += 1
            if event is not "":
                print(event, data)
                self.interpret_event(event, data)

def _test_show_results():
    print('\n','\n',"---- SUMMARY -----")
    print('Player Name: ', self.PLAYER_NAME)
    print('Total Experience: ', self.get_exp())
    print('Total Influence: ', self.get_inf())
    print("---- ABILITY DATA -----")
    # loop down the ability dictionary and print the ability name, accuracy % and total damage
    for ability in self.Abilities:
        print(self.Abilities[ability].name,
              '\n    DPS: ', self.Abilities[ability].get_dps(self.get_log_duration()), 'Average Damage: ', self.Abilities[ability].get_average_damage(),
              '\n    Accuracy: ', self.Abilities[ability].get_accuracy(), '% | Count: ', self.Abilities[ability].count, '| Hits: ', self.Abilities[ability].hits, '|')
              
        
        # loop down the damage components and print the damage type, total damage and count
        for component in self.Abilities[ability].damage:
            print('      Damage Type: ', component.type,'| T:', component.total_damage,'| H:', component.highest_damage, '| L:', component.lowest_damage, '| Count: ', component.count)
        print('------------------')

    total_damage = 0
    print('')
    for ability in self.Abilities:
        total_damage += self.Abilities[ability].get_total_damage()
    print('Total Damage: ', total_damage)
    print('Total Duration of the log: ', self.get_log_duration(), 'seconds')
    print('Total Damage Per Second: ', self.get_dps(self.get_log_duration()))
    print('Lines processed: ', self.line_counter)

if __name__ == "__main__":
    # if this is being run directly, run the test data
    print("Parser has been directly called as __main__, running test data")

    PLAYER_NAME = "Emet Selch"
    self = Parser(PLAYER_NAME)
    
    self.line_counter = 0

    #Initiate tests
    #_test_hit_rolls()
    #_test_damage_lines()
    #_test_reward_lines()
    _test_log_file()
                
    _test_show_results()