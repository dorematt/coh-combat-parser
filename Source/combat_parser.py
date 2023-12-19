import re
import os
import time
from datetime import datetime
import random

class Parser:
    '''Extracts data from log lines using regex patterns, Will return a list of tuples containing the log entry type and a dictionary of the extracted data.'''
    PATTERNS = {
        "player_hit_roll": re.compile(
            r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<outcome>HIT|MISS(?:ED)?) (?P<target>[^.!]+)(?:!!|!) Your (?P<ability>[^.]+) power (?:had a .*?chance to hit, you rolled a (\d+\.\d+)|was forced to hit by streakbreaker)\."
        ),
        "player_pet_hit_roll": re.compile(
            r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<pet_name>[^.]+):? (?P<outcome>HIT|MISS(?:ED)?) (?P<target>[^.!]+)(?:!!|!) Your (?P<ability>[^.]+) power (?:had a .*?chance to hit, you rolled a (\d+\.\d+)|was forced to hit by streakbreaker)\."
        ),
        "player_damage": re.compile(
            r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?:PLAYER_NAME:  )?(?:You (?:hit|hits you with their)|HIT) (?P<target>[^:]+) with your (?P<ability>[^:]+)(?:: (?P<ability_desc>[\w\s]+))? for (?P<damage_value>[\d.]+) points of (?P<damage_type>[^\d]+) damage(?: over time)?\.*"
        ),
        "player_pet_damage": re.compile(
            r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<pet_name>[^.]+):? (?:You (?:hit|hits you with their)|HIT) (?P<target>[^:]+) with your (?P<ability>[^:]+)(?:: (?P<ability_desc>[\w\s]+))? for (?P<damage_value>[\d.]+) points of (?P<damage_type>[^\d]+) damage(?: over time)?\.*"
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
        "player_name": re.compile( # Matches a welcome message that includes the player name
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) Welcome to City of .*?, (?P<player_name>.+?)!"
        ),
    }
    LOG_FILE_PATH = ""
    PLAYER_NAME = ""
    COMBAT_SESSION_TIMEOUT = 30 # Seconds,  If no events are found within this time, the combat session will be closed
    monitoring_live = False # Flag to indicate if the parser is monitoring a live log file
    def __init__(self, LOG_FILE_PATH = ""):

        print('     Parser Initialize...')
        self.clean_variables()
    
    def update_regex_player_name(self, player_name):
        updated_patterns = {}
        for key, regex in self.PATTERNS.items():
            updated_pattern = regex.pattern.replace('PLAYER_NAME', player_name)
            updated_regex = re.compile(updated_pattern)
            print('Updated Regex: ', updated_regex)
            updated_patterns[key] = updated_regex
        return updated_patterns
    
    def extract_from_line(self, log_line):
        '''Extracts data from a log line using regex patterns, returns a tuple containing the log entry type and a dictionary of the extracted data.'''
        for key, regex in self.PATTERNS.items():
            match = regex.match(log_line)
            if match:
                #print('Matched Event: ', key)
                #print(match.groupdict())
                #self.interpret_event(key, match.groupdict())
                return (key, match.groupdict())
        return '',[]

    def new_session(self, timestamp):
        self.session_count += 1
        self.session.append(CombatSession(timestamp))
        self.combat_session_live = True
        print ("     Combat Session Started: ", self.session_count)
        return self.session[-1]

    def check_session(self, timestamp):
        '''Checks sessions, returns an int code for whether the session, exists or is outside the timeout duration'''

        if self.combat_session_live:
            # print('     Checking Session: ', self.session_count, ' With a duration of ', self.session[-1].get_duration(), ' seconds')
            chk_time = timestamp - self.session[-1].end_time
            # print(' Time since last activity in session: ', chk_time, ' seconds')
            if chk_time > self.COMBAT_SESSION_TIMEOUT:
                return -1 # Session over timeout
            else:
                return 1 # Session still active and valid
        return 0 # No active session

    def end_session(self):
        '''Ends the current combat session'''
        self.session[-1].update_duration()
        self.combat_session_live = False
        self.add_global_combat_duration(self.session[-1].get_duration())
        print ("     Ended Combat Session: ", self.session_count, " With a duration of ", self.session[-1].get_duration(), " seconds")

    def update_session_time(self, timestamp):
        '''Updates the current combat session time'''
        self.session[-1].update_session_time(timestamp)
        # print ("     Updated Combat Session: ", self.session_count, " With a duration of ", self.session[-1].get_duration(), " seconds")

    def interpret_event(self, event, data):
        '''Interprets the data generated by the extract_from_line function to update the parser data.
        This will handle updating the global time, checking for combat session status and calling the appropriate handler functions'''
        # Check for an active combat session and determine if it is still active

        # Update the current time and check combat session status
        self.update_global_time(self.convert_timestamp(data["date"], data["time"]))
        status = self.check_session(self.GLOBAL_CURRENT_TIME)

        def update_session_and_time(): # Helper function to update the session and time
            if status == 0:
                self.new_session(self.GLOBAL_CURRENT_TIME)
            self.session[-1].update_session_time(self.GLOBAL_CURRENT_TIME)

        if status == -1: # -1 indicates that the session has timed out
            self.end_session()

        if event == "player_hit_roll" or event == "player_pet_hit_roll":
            update_session_and_time()
            self.handle_event_player_hit_roll(data, event == "player_pet_hit_roll")

        elif event == "player_damage" or event == "player_pet_damage":
            update_session_and_time()
            self.handle_event_player_damage(data, event == "player_pet_damage")

        elif event == "reward_gain_both" or event == "reward_gain_exp" or event == "reward_gain_inf":
            if data.get("exp_value") is None:
                data["exp_value"] = ""
            if data.get("inf_value") is None: 
                data["inf_value"] = ""
            self.handle_event_reward_gain(data)

        elif event == "player_name": # This catches the welcome message that includes the player name either at the start of the log, or further down should the player log out and back in
            self.set_player_name(data["player_name"])
            self.PATTERNS = self.update_regex_player_name(self.PLAYER_NAME)


    def handle_event_player_damage(self, data, pet=False):
        '''Handles a player damage event'''
        # First, ignore any matches that is the player hitting themselves
        if data["target"] == self.PLAYER_NAME:
            # print('Player hit themselves, with ', data["ability"] , '. Ignoring')
            return
         
        '''Next, check for the ability in the directory. If it doesn't exist, create it, otherwise, add the damage to the ability.
        If we've gotten the damage event but no hit roll previous to it, then we assume the ability is a proc'''

        if pet:
            search_ability = data["pet_name"] + ": " + data["ability"]
        else:
            search_ability = data["ability"]

        if search_ability not in self.Abilities:
            self.Abilities[search_ability] = Ability(search_ability, None, True)
            #self.Abilities[data["ability"]].ability_used(True)
            #print('Ability Created: ', self.Abilities[data["ability"]].name)

        active_ability = self.Abilities[search_ability]
        active_ability.add_damage(DamageComponent(data["damage_type"], data["damage_value"]))
        #print('Ability Executed:', active_ability.name)

    def handle_event_player_hit_roll(self, data, pet=False):
        '''Handles a player hit roll event'''
        # First, ignore any matches that is the player hitting themselves
        if data["target"] == self.PLAYER_NAME:
            print('Player hit themselves, with ', data["ability"] , '. Ignoring')
            return
        
        if pet:
            search_ability = data["pet_name"] + ": " + data["ability"]
        else:
            search_ability = data["ability"]

        # Check for ability in directory, if it doesn't exist, create it.
        if search_ability not in self.Abilities:
            self.Abilities[search_ability] = Ability(search_ability)

        active_ability = self.Abilities[search_ability]
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
    
    def update_global_time(self, timestamp):
        '''Checks if the timestamp is the first event, if it is, set the start time to the timestamp, otherwise update the current time'''
        if self.GOBAL_START_TIME == 0:
            self.GOBAL_START_TIME = timestamp
        self.GLOBAL_CURRENT_TIME = timestamp
    def add_global_combat_duration(self, duration): 
        self.global_combat_duration += duration
        return self.global_combat_duration
    def get_log_duration(self):
        '''Calculates the duration of the log file'''
        return self.GLOBAL_CURRENT_TIME - self.GOBAL_START_TIME
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
            extracted_data = self.extract_from_line(line)
            print(extracted_data)
        return extracted_data

    def set_log_file(self, file_path):
        '''takes the file path and sets the log file to the file path'''
        self.LOG_FILE_PATH = file_path
        print('          Log File Path Set: ', self.LOG_FILE_PATH)
    def has_log_file(self):
        '''Checks if the log file path is set'''
        return self.LOG_FILE_PATH != ""
    def is_valid_file_path(self, file_path):
        '''CHeck if the given file path is valid'''
        # Check if the file path is valid
        file_path = file_path.strip()
        if not os.path.isfile(file_path):
            print('     Invalid File Path: ', file_path)
            return False
        return True
    def find_player_name(self):
        '''Reads the log file from bottom to top, to find the player name'''
        # Check if the log file path is set
        if self.LOG_FILE_PATH == "":
            print('          Log File Path not set')
        
        # Open the log file then read each line from bottom up to match the last player_name pattern
        with open(self.LOG_FILE_PATH, 'r') as file:
            for line in reversed(list(file)):
                event, data = self.extract_from_line(line)
                if event == "player_name":
                    return data["player_name"]
        print('          Unable to find Player Name in log')
        return ""

    def set_player_name(self, player_name):
        '''Sets the player name'''
        self.PLAYER_NAME = player_name
        print('          Player Name Updated to: ', self.PLAYER_NAME)
        self.PATTERNS = self.update_regex_player_name(self.PLAYER_NAME)
    
    def process_existing_log(self, file_path):
        '''Analyses a log file that has already been created. Function will terminate once the bottom of the file is reached'''
        
        # Check if the file path is valid
        if not self.is_valid_file_path(file_path):
            return False
        self.set_log_file(file_path)
    
        self.clean_variables()

        print('          Processing Log File: ', self.LOG_FILE_PATH)
        _log_process_start_ = time.time()
        #self.set_player_name(self.find_player_name())
        
        #Open file and iterate through each line
        with open(self.LOG_FILE_PATH, 'r') as file:
            for line in file:
                event, data = self.extract_from_line(line)
                self.line_count += 1
                if event is not "":
                    print(event, data)
                    self.interpret_event(event, data)
        _test_show_results()
        print('          Log File processed in: ', round(time.time() - _log_process_start_, 2), ' seconds')
        return True
    
    def process_live_log(self, file_path):
        '''Opens the file path and monitors the file for new entries until terminated. 
        This will not process any existing entries in the log file'''

        # Check if the file path is valid
        if not self.is_valid_file_path(file_path):
            return False
        self.set_log_file(file_path)

        self.clean_variables()


        print('          Monitoring Log File: ', self.LOG_FILE_PATH)
        self.monitoring_live = True

        # locate and assign player name
        self.set_player_name(self.find_player_name())

        # Begin monitoring the log file
        with open(self.LOG_FILE_PATH, 'r') as file:
            while self.monitoring_live:
                line = file.readline()
                if not line:
                    time.sleep(0.01)
                    continue
                event, data = self.extract_from_line(line)
                self.line_count += 1
                if event is not "":
                    print(event, data)
                    self.interpret_event(event, data)


    def handle_commands(self, command):
        '''When run in CLI mode, this function will handle the commands entered by the user'''
        if command.lower == "t":
            self.process_existing_log('path_to_test_file.txt')
        elif command == "live":
            #TODO Implement live monitoring logic here
            print("Live monitoring is not implemented yet.")
        elif command.lower() in ["analyze", "a", "analyse"]:
            _, file_path = command.split(" ", 1)
            self.process_existing_log(file_path)
        else:
            print("Unknown command. Please enter a valid command.")
            
    def clean_variables(self):
        '''Reset all'''
        self.line_count = 0
        self.session = [] # Stores a list of combat sessions
        self.session_count = 0 # Stores the number of combat sessions and also acts as a key to which combat session within the combat_session array is active
        self.combat_session_live = False # Flag to indicate if a combat session is active
        self.global_combat_duration = 0 # Stores the total durations of all combat sessions

        # Set Exp and Influence values
        self.EXP_VALUE = 0
        self.INF_VALUE = 0
        
        # create a key-value list of abilities
        self.Chars = {} # Stores a list of characters
        self.Abilities = {} # Stores a list of abilities
        self.GOBAL_START_TIME = 0 # Stores the timestamp of the first event as an int
        self.GLOBAL_CURRENT_TIME = 0 # Stores the latest timestamp as an int
        
class CombatSession:
    '''The CombatSession class stores data about a combat session, which is a period where damage events are registered.
    CombatSessions will automatically end based on the COMBAT_SESSION_TIMEOUT value to avoid including long downtime periods in the data.''' 
    def __init__(self, timestamp=0):
        self.start_time = timestamp
        self.end_time = timestamp
        self.duration = 0 # Seconds
        self.chars = {} # Stores a list of characters

    def set_start_time(self, start_time):
        self.start_time = start_time
    def set_end_time(self, end_time):
        self.end_time = end_time
    def update_duration(self):
        self.duration = self.end_time - self.start_time

    def update_session_time(self, timestamp):
        self.end_time = timestamp
        self.update_duration()

    def get_duration(self):
        self.update_duration()
        return self.duration

class Character:
    '''Stores data about a character, this can be the Player, pets or enemies'''
    def __init__(self, name="") -> None:
        self.name = ""
        self.abilities = {}

    def add_ability(self, ability):
        '''Adds an ability to the character'''
        self.abilities[ability.name] = ability
class Ability:
    '''Stores data about an ability used'''
    def __init__(self, name, hit=None, proc=False):
        self.name = name
        self.count = 0 if hit is None else 1
        self.hits = 1 if hit is True else 0
        self.damage = []
        self.proc = proc
        self.pet = False
        self.pet_name = "" # If ability came from a pet, store the pet name

    def add_damage(self, damage_component):
        '''Adds a damage component to the ability'''
        # Check if damage type is already in the ability, if it is, add the damage to the existing component
        for component in self.damage:
            if component.type == damage_component.type:
                component.add_damage(damage_component.type, damage_component.total_damage)
                return
        self.damage.append(damage_component)
        self.damage[-1].add_damage(damage_component.type, damage_component.total_damage)

        if self.proc: # If the ability is a proc, we'll need to incremement the ability hit count as there will be no hitroll for this ability.
            self.ability_used(True)
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
    
    def get_count(self):
        '''Returns the number of times the ability has been used'''
        return self.count
    
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
            event, data = self.extract_from_line(line)
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
            event, data = self.extract_from_line(line)
            #self.line_counter += 1
            if event != "":
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
        event, data = self.extract_from_line(line)
        #self.line_counter += 1
        if event is not "":
            print(event, data)
            self.interpret_event(event, data)

def _test_log_file():
    print('\n \n', "---- STARTING LOG FILE DATA TEST -----", '\n \n')
#Open text file with test data, similarly test extraction data
    with open('C:\\Users\\mdore\\OneDrive\\02_Documents\\02_SCRIPTS\\CoH_Log_Parser\\coh_logfile_snippet.txt', 'r') as file:
        for line in file:
            event, data = self.extract_from_line(line)
            self.line_count += 1
            if event is not "":
                print(event, data)
                self.interpret_event(event, data)

def _test_show_results():
    def format_duration(seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'{int(hours)} hours, {int(minutes)} minutes, {int(seconds)} seconds'
    
    print('\n','\n',"---- SUMMARY -----")
    print('Player Name: ', self.PLAYER_NAME)
    print(f'Total Experience: {self.get_exp():,}')
    print(f'Total Influence: {self.get_inf():,}')
    print("---- ABILITY DATA -----")
    # loop down the ability dictionary and print the ability name, and '(proc)' if the ability is a proc, accuracy % and total damage
    for ability in self.Abilities:
        print(self.Abilities[ability].name, ' (proc)' if self.Abilities[ability].proc else '',
              '\n    DPS: ', self.Abilities[ability].get_dps(self.global_combat_duration), 'Average Damage: ', self.Abilities[ability].get_average_damage(),
              '\n    Accuracy: ', self.Abilities[ability].get_accuracy(), '% | Count: ', self.Abilities[ability].count, '| Hits: ', self.Abilities[ability].hits, '|')
        
        
        # loop down the damage components and print the damage type, total damage and count
        for component in self.Abilities[ability].damage:
            print('      Damage Type: ', component.type,'| T:', component.total_damage,'| H:', component.highest_damage, '| L:', component.lowest_damage, '| Count: ', component.count)
        print('------------------')

    total_damage = 0
    print('')
    for ability in self.Abilities:
        total_damage += self.Abilities[ability].get_total_damage()
    print('Total Damage: ', round(total_damage,2))
    print('Total Duration of the log:', format_duration(self.get_log_duration()))
    print('Total Combat Duration:', format_duration(self.global_combat_duration))
    print('Total Combat Sessions: ', self.session_count)
    print('Total Damage Per Second: ', self.get_dps(self.global_combat_duration))
    print('Lines processed: ', self.line_count)

def _test_combat_sessions():
    pass

if __name__ == "__main__":
    # if this is being run directly, run the test data
    print("Parser has been directly called as __main__, running test data")

    #PLAYER_NAME = "Emet Selch"
    self = Parser()
    
    self.line_count = 0

    #Initiate tests
    #_test_hit_rolls()
    #_test_damage_lines()
    #_test_reward_lines()
    test_file = "H:\\Games\\Homecoming_COH\\accounts\\10kVolts\\Logs\\chatlog 2023-12-18.txt"
    self.process_existing_log(test_file)


    while True:
        user_command = input("Enter a command (e.g., 'run_test_file', 'live_monitor', 'analyze_log_file <path_to_log_file>'): ")
        self.handle_commands(user_command)
                