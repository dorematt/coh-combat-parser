from re import compile
import os.path
import time
from datetime import datetime
from data.Ability import Ability
from data.Character import Character
from data.DamageComponent import DamageComponent
from combat.CombatSession import CombatSession
from tkinter import filedialog as tk
import sys
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QMutex, QMutexLocker, QTimer, QCoreApplication, QSettings
from CoH_Parser import Globals
CLI_MODE = False # Flipped to True if this .py file is launched directly instead of through the UI

class Parser(QObject):
    '''Extracts data from log lines using regex patterns, Will return a list of tuples containing the log entry type and a dictionary of the extracted data.'''
    PATTERNS = {
        "player_ability_activate": compile(
            r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) You activated the (?P<ability>.+?) power\."
        ),
        "player_hit_roll": compile(
            r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<outcome>HIT|MISS(?:ED)?) (?P<target>[^.!]+)(?:!!|!) Your (?P<ability>[^.]+) power (?:had a .*?chance to hit, you rolled a (\d+\.\d+)|was forced to hit by streakbreaker)\."
        ),
        "player_pet_hit_roll": compile(
            r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<pet_name>[^:]+?):? * (?P<outcome>HIT|MISS(?:ED)?) (?P<target>[^.!]+)(?:!!|!) Your (?P<ability>[^.]+) power (?:had a .*?chance to hit, you rolled a (\d+\.\d+)|was forced to hit by streakbreaker)\."
        ),
        "player_damage": compile(
            r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?:PLAYER_NAME:  )?(?:You (?:hit|hits you with their)|HIT) (?P<target>[^:]+) with your (?P<ability>[^:]+)(?:: (?P<ability_desc>(?:Recharge/Chance [\w\s]+|[\w\s]+)))? for (?P<damage_value>[\d.]+) points of (?P<damage_type>[^\d]+) damage(?: \((?P<damage_flair>[^\)]+)\))?(?: over time)?\.*"
        ),
        "player_pet_damage": compile(
             r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<pet_name>[^:]+?):? * You hit (?P<target>[^:]+) with your (?P<ability>[^:]+)(?:: (?P<ability_desc>(?:Recharge/Chance [\w\s]+|[\w\s]+)))? for (?P<damage_value>[\d.]+) points of (?P<damage_type>[^\d]+) damage(?: \((?P<damage_flair>[^\)]+)\))?(?: over time)?\.*"
        ),
       # "foe_hit_roll": compile(
       #     r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<enemy>.+?) (?P<outcome>HIT|MISSES you!|HIT |MISS(?:ED)?) (?:(?P<ability>.+?) power had a .* to hit and rolled a .*\.?)?"
       # ),
       # "foe_damage": compile(
       #     r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<enemy>.+?) hits you with their (?P<ability>.+?) for (?P<damage_value>[\d.]+) points of (?P<damage_type>\w+) damage\.*"
       # ),
        "reward_gain_both": compile(
            r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) You gain (?P<exp_value>\d{1,3}(,\d{3})*(\.\d+)?) experience and (?P<inf_value>\d{1,3}(,\d{3})*(\.\d+)?) (?:influence|information|infamy)\.*"
        ),
        "reward_gain_exp": compile(
            r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) You gain (?P<exp_value>\d+(,\d{3})*|\d+) experience\."
        ),
        "reward_gain_inf": compile(
            r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) You gain (?P<inf_value>\d+(,\d{3})*|\d+) (?:influence|information|infamy)\."
        ),
       # "influence_gain": compile(
       #     r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) .*? and (?P<inf_value>\d+) (influence|infamy|information)\.*"
       # ),
       # "healing": compile(
       #     r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<healer>.+?) (?:heals|heal) (?:you|PLAYER_NAME) with their (?P<ability>.+?) for (?P<healing_value>[\d.]+) health points(?: over time)?\.*"
       # ),
        # This pattern should capture endurance recovery. An example line for endurance recovery is needed to refine this pattern.
       # "endurance_recovery": compile(
       #     r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<restorer>.+?) (?:restores|restore) (?:your|PLAYER_NAME's) endurance by (?P<endurance_value>[\d.]+) points\.*"
       # ),
        "player_name": compile( # Matches a welcome message that includes the player name
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) Welcome to City of .*?, (?P<player_name>.+?)!"
        ),
        "command": compile( # Matches a command message in chat
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) \[Local\] (?P<player>.+?): .*?##(?P<command>\S+) (?P<value>.*)"
        ),
    }
    
    PATTERN_DATETIME = {
        "date_time": compile(
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2})"
        )
    }
    LOG_FILE_PATH = ""
    log_file = None
    PLAYER_NAME = ""# Seconds, determines how long to wait between  # 0 = Silent, 1 = Errors and Warnings, 3 = Errors, Warnings and Info, 3 = Debug level 1, 4 = Debug level 2
    monitoring_live = False # Flag to indicate if the parser is monitoring a live log file
    processing_live = False # Flag to indicate when processing is active (or used to terminate processing)
    combat_session_data = [] # Stores a list of combat sessions
    mutex = QMutex()
    sig_finished = pyqtSignal(list)
    sig_periodic_update = pyqtSignal(list)
    parentThread = None
    final_update = False # Flag to indicate if a final update is required
    user_session_name = ""
    settings = QSettings(Globals.AUTHOR, Globals.APPLICATION_NAME)

    def __init__(self, parent=None):
        super().__init__()
        self.check_parse_settings()
        print('     Parser Initialize...')
        if self.CONSOLE_VERBOSITY>= 3: print("Creating interval_timer")
        self.interval_timer = QTimer(parent) # Handles preriodic UI update events
        self.interval_timer.timeout.connect(self.live_log_interval_update)
        self.interval_timer.setInterval(250)
        self.interval_timedout = False
        self.monitoring_timer = QTimer(parent)
        self.clean_variables()
        self.check_parse_settings()

    def clean_variables(self):
        '''Reset all'''
        self.line_count = 0
        self.combat_session_data = [] # Stores a list of combat sessions
        self.session_count = 0 # Stores the number of combat sessions and also acts as a key to which combat session within the combat_session array is active
        self.session_name_count = 0 # For counting the number of sessions with the same name
        self.combat_session_live = False # Flag to indicate if a combat session is active
        self.global_combat_duration = 0 # Stores the total durations of all combat sessions
        self.active_ability = None # Stores a reference to the ability that is currently being processed

        # Set Exp and Influence values
        self.EXP_VALUE = 0
        self.INF_VALUE = 0
        
        # create a key-value list of abilities
        self.Chars = {} # Stores a list of characters
        self.abilities = {} # Stores a list of abilities
        self.GOBAL_START_TIME = 0 # Stores the timestamp of the first event as an int
        self.GLOBAL_CURRENT_TIME = 0 # Stores the latest timestamp as an int
        final_update = False # Flag to indicate if a final update is required
        user_session_name = ""

        if self.CONSOLE_VERBOSITY >= 2: print('          Parser variables cleaned...')

    
    def update_regex_player_name(self, player_name):
        updated_patterns = {}
        for key, regex in self.PATTERNS.items():
            updated_pattern = regex.pattern.replace('PLAYER_NAME', player_name)
            updated_regex = compile(updated_pattern)
            if self.CONSOLE_VERBOSITY == 3: print('Updated Regex: ', updated_regex)
            
            updated_patterns[key] = updated_regex
        return updated_patterns
    
    def extract_from_line(self, log_line):
        '''Extracts data from a log line using regex patterns, returns a tuple containing the log entry type and a dictionary of the extracted data.'''
        for key, regex in self.PATTERNS.items():
            match = regex.match(log_line)
            if match:
                return (key, match.groupdict())
        return '',[]
    def extract_datetime_from_line(self, log_line):
        '''Faster version of extract_from_line that only extracts the datetime from the log line (for use in live monitoring updates)'''
        for key, regex in self.PATTERN_DATETIME.items():
            match = regex.match(log_line)
            if match:
                return (key, match.groupdict())
        return '',[]

    def new_session(self, timestamp):
        self.session_count += 1
        if self.user_session_name == "": 
            self.session_name_count +=1
            name = self.COMBAT_SESSION_NAME + " " + str(self.session_name_count)
        else:
            self.session_name_count += 1
            name = self.user_session_name + " " + str(self.session_name_count)
        self.combat_session_data.append(CombatSession(timestamp,name))
        self.combat_session_live = True
        if self.monitoring_live: self.interval_timer.start() # Begins periodic UI refreshes
        if self.CONSOLE_VERBOSITY >= 2: print ("---------->  Combat Session Started: ", self.session_count, '\n')
        return self.combat_session_data[-1]
    def check_session(self, timestamp):
        '''Checks sessions, returns an int code for whether the session, exists or is outside the timeout duration'''

        if self.combat_session_live:
            # print('     Checking Session: ', self.session_count, ' With a duration of ', self.session[-1].get_duration(), ' seconds')
            time = timestamp - self.combat_session_data[-1].end_time
            # print(' Time since last activity in session: ', chk_time, ' seconds')
            if time > self.COMBAT_SESSION_TIMEOUT:
                if self.COMBAT_SESSION_TIMEOUT == 0: 
                    return 1 # Session still active and valid
                else: 
                    return -1 # Session over timeout
            else:
                return 1 # Session still active and valid
        return 0 # No active session
    def end_current_session(self):
        '''Ends the current combat session'''
        self.combat_session_data[-1].update_duration()
        self.combat_session_live = False
        self.add_global_combat_duration(self.combat_session_data[-1].get_duration())
        if self.CONSOLE_VERBOSITY >= 2: print ("---------->  Ended Combat Session: ", self.session_count, " With a duration of ", self.combat_session_data[-1].get_duration(), " seconds \n")
        if self.monitoring_live: self.final_update = True
        self.active_ability = None
    def remove_last_session(self):
        '''Removes the current combat session'''
        if self.CONSOLE_VERBOSITY >= 2: print ("---------->  Removed Combat Session: ", self.session_count, '\n')
        self.combat_session_data.pop()
        self.session_count -= 1
        self.session_name_count -= 1
        self.combat_session_live = False
        if self.monitoring_live: self.final_update = True
        self.active_ability = None
        
    def update_session_time(self, timestamp):
        '''Updates the current combat session time'''
        self.combat_session_data[-1].update_session_time(timestamp)
    def print_session_results(self, session):
        '''Displays the results of the current combat session'''
        if not CLI_MODE: 
            print("              Combat Session: ", self.combat_session_data[-1].name, ", ", session.get_duration(), "s duration processed.", sep="")
            return
        
        print('\n', '\n') 
        print('Session ', self.session_count, ' SUMMARY | Duration: ', session.get_duration())
        print(' EXP: ', session.get_exp(), ' | INF: ', session.get_inf())
        
        # Sort characters by DPS
        sorted_chars = sorted(session.chars.keys(), key=lambda char: session.chars[char].get_dps(session.get_duration()), reverse=True)
        
        for char in sorted_chars:
            print('---------------------------------')
            if session.chars[char].is_pet:
                print('  Pet: ', char)
            else:
                print('  Char: ', char)
            print('     DPS: ', session.chars[char].get_dps(session.get_duration()), ' | Acc: ', session.chars[char].get_accuracy(), '%')
            print('     Total : ', session.chars[char].get_total_damage(), ' | Avg Hit : ', session.chars[char].get_average_damage())
            print('\n')
            
            def print_sorted_abilities(sorted_abilities):
                for ability in sorted_abilities:
                    if session.chars[char].abilities[ability].get_count() == 0:
                        continue  # Skip zero count abilities
                    _ability = session.chars[char].abilities[ability]
                    print('     ',_ability.name, ' (proc)' if _ability.proc else '',
                    '\n        DPS: ', _ability.get_dps(session.get_duration()), 'Avg: ', _ability.get_average_damage(),
                    '\n        Accuracy: ', _ability.get_accuracy(), '% | Count: ', _ability.count, '| Hits: ', _ability.hits, '|')

                    for component in _ability.damage:
                        print('            Damage Type: ', component.type,'| T:', component.total_damage,'| H:', component.highest_damage, '| L:', component.lowest_damage, '| Count: ', component.count)
                    print('')

            if self.CONSOLE_VERBOSITY > 1:
                # Sort abilities by DPS
                sorted_abilities = sorted(session.chars[char].abilities.keys(), key=lambda ability: session.chars[char].abilities[ability].get_dps(session.get_duration()), reverse=True)
                print_sorted_abilities(sorted_abilities)

            
        
        print('---------------------')
        print('\n')


    def interpret_event(self, event, data):
        '''Interprets the data generated by the extract_from_line function to update the parser data.
        This will handle updating the global time, checking for combat session status and calling the appropriate handler functions'''
        # Check for an active combat session and determine if it is still active

        # Update the current time and check combat session status
        with QMutexLocker(self.mutex):
            self.update_global_time(self.convert_timestamp(data["date"], data["time"]))
            status = self.check_session(self.GLOBAL_CURRENT_TIME)

            def update_session_and_time(in_combat=False): # Helper function to call session updates as well as beginning new sessions
                if (status == 0 or status == -1) and in_combat:
                    self.new_session(self.GLOBAL_CURRENT_TIME) # We 
                self.combat_session_data[-1].update_session_time(self.GLOBAL_CURRENT_TIME)


            if status == -1: # Checking for a timed-out combat session

                # Remove the session if it had no damage
                if self.combat_session_data[-1].get_total_damage() == 0:
                    self.remove_last_session()
                else:
                    self.end_current_session()
                    self.combat_session_live = False
                    self.print_session_results(self.combat_session_data[-1])

            if event == "player_ability_activate":
                update_session_and_time(True)
                self.handle_event_player_power_activate(data)
                

            if event == "player_hit_roll" or event == "player_pet_hit_roll":
                update_session_and_time(True)
                self.handle_event_player_hit_roll(data, event == "player_pet_hit_roll")

            elif event == "player_damage" or event == "player_pet_damage":
                update_session_and_time(True)
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
            
            elif event == "command":
                if self.PLAYER_NAME == "": 
                    self.set_player_name(self.find_player_name())
                if data["player"] != self.PLAYER_NAME: # Make sure the command is from the player
                    return
                self.handle_event_command(data)

    def handle_event_player_power_activate(self, data):

        # We'll use these power_activation events in the log to create new abilties in our list
        this_ability = data["ability"]
        player = self.PLAYER_NAME
        this_session = self.combat_session_data[-1]
        
        if player not in this_session.chars: 
            this_session.chars[player] = Character(player)
            if self.CONSOLE_VERBOSITY >= 3: print("     Added New Character: ", this_session.chars[player].get_name(), " to Session: ", self.session_count, ' via Power Activation Event')
        
        player = this_session.chars[player]
        
        if this_ability not in player.abilities: 
            player.abilities[this_ability] = Ability(this_ability)
            if self.CONSOLE_VERBOSITY >= 3: print("     Added Ability: ", this_ability, " to Character: ", player.get_name(), ' via Power Activation Event')
        
        this_ability = player.abilities[this_ability]
        this_ability.ability_used()

    def handle_event_player_hit_roll(self, data, pet=False):
        '''Handles a player hit roll event, assumes it came from player instead of pet unless pet=True'''

        # Ignore events where the player hits themselves
        if data["target"] == self.PLAYER_NAME:
            print(f'Player hit themselves with {data["ability"]}. Ignoring')
            return

        # Determine the ability and caster based on pet status
        this_ability = data["ability"]

        if pet:
            caster = data["pet_name"]
        else:
            caster = self.PLAYER_NAME

        # Check and update the session's character list
        this_session = self.combat_session_data[-1]

        if caster not in this_session.chars: 
            this_session.chars[caster] = Character(caster)
            if pet: this_session.chars[caster].is_pet = True
            if self.CONSOLE_VERBOSITY >= 2:
                print(f"     Added Character: {caster} to Session: {self.session_count} via Hit Roll Event")

        caster = this_session.chars[caster]

        if this_ability not in caster.abilities:
            caster.abilities[this_ability] = Ability(this_ability)
            if self.CONSOLE_VERBOSITY >= 3:
                print(f"     Added Ability: {this_ability} to Character: {caster.get_name()} via Hit Roll Event")

        this_ability = caster.abilities[this_ability]

        if pet: this_ability.ability_used() # We don't have power activation events for pets, so we'll use the hit roll as a proxy for ability usage
        this_ability.ability_hit(data["outcome"] == "HIT") 

    def handle_event_player_damage(self, data, pet=False):
        '''Handles a player damage event'''
        
        # Ignore events where the player hits themselves
        if data["target"] == self.PLAYER_NAME:
            return
        
        if data["damage_flair"] is None: 
            data["damage_flair"] = ""

        if data["ability_desc"] is None:
            data["ability_desc"] = ""

        proc = False
        if "Chance for" in data["ability_desc"] or data["ability"] == "Doublehit" :
            proc = True


        this_ability = data["ability"]
        flair = data["damage_flair"]
        damage = float(data["damage_value"])

        if flair != "":
            type = (data["damage_type"] + " " + data["damage_flair"])
        else:
            type = data["damage_type"]

        if pet:
            caster = data["pet_name"]
        else:
            caster = self.PLAYER_NAME

        # Create or get the ability and update damage
        # active_ability = self.abilities.setdefault(search_ability, Ability(search_ability, None, True))
        # active_ability.add_damage(DamageComponent(data["damage_type"] + " " + data["damage_flair"]),float( data["damage_value"]))

        # Check and update the session's character list
        this_session = self.combat_session_data[-1]

        if caster not in this_session.chars:
            this_session.chars[caster] = Character(caster)
            if pet: this_session.chars[caster].is_pet = True
            if self.CONSOLE_VERBOSITY >= 3:
                print(f"     Added Character: {caster} to Session: {self.session_count} via Damage Event")

        caster = this_session.chars[caster]
        

        if proc and self.active_ability is not None:
            if self.associating_procs:
                # Add the proc damage to the last used ability
                if flair != "": 
                    proc_name = (data["ability"] + " " + data["damage_flair"])
                else:
                    proc_name = data["ability"]
                self.active_ability.add_damage(DamageComponent(proc_name),damage)
                # print('         Damage Proc', proc_name,'Added to ', self.active_ability.name, "with value", damage, "and total damage of:", self.active_ability.get_total_damage(), 'Count: ', self.active_ability.damage[-1].count)
                return
        
        if this_ability not in caster.abilities:
            caster.add_ability(this_ability, Ability(this_ability, None, proc))
            if self.CONSOLE_VERBOSITY >= 3:
                print(f"     Added Ability: {this_ability} to Character: {caster.get_name()} via Damage Event")

        this_ability = caster.get_ability(this_ability)


        this_ability.add_damage(DamageComponent(type), damage)
        if self.CONSOLE_VERBOSITY >= 3: 
                print ('         Damage Component Added: ', this_ability.damage[-1].type, this_ability.damage[-1].total_damage, 'Count: ', this_ability.damage[-1].count)

        self.active_ability = this_ability

  
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

        # Check for an active combat session and add the exp and inf to the session rewards
        if self.combat_session_live:
            self.combat_session_data[-1].add_exp(exp_value)
            self.combat_session_data[-1].add_inf(inf_value)

    def handle_event_command(self, data):
        if data["command"] == "SESSION_NAME":
            self.user_session_name = data["value"]
            self.session_name_count = 0
            if self.CONSOLE_VERBOSITY >= 2 or self.monitoring_live: print ("          Setting Session Name to: ", self.user_session_name, '\n')
            if self.combat_session_live:
                self.session_name_count += 1
                self.combat_session_data[-1].set_name(data["value"] + " " + str(self.session_name_count))
                if self.monitoring_live: print ("Updated Active Combat Session Name: ", self.combat_session_data[-1].get_name(), '\n')

    def convert_timestamp(self, date, time):
        '''Converts a timestamp from the log file into a datetime object and returns an int representing the time in seconds'''
        # Convert the date and time into a datetime object
        timestamp = datetime.strptime(date + " " + time, "%Y-%m-%d %H:%M:%S")
        # Convert the datetime object into an int representing the time in seconds
        timestamp = timestamp.hour * 3600 + timestamp.minute * 60 + timestamp.second
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
        for ability in self.abilities:
            total_damage += self.abilities[ability].get_total_damage()
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
        with open(self.LOG_FILE_PATH, 'r', encoding='utf-8') as file:
            for line in reversed(list(file)):
                event, data = self.extract_from_line(line)
                if event == "player_name":
                    print ('          Player Name Located: ', data["player_name"])
                    return data["player_name"]
        print('          Unable to find Player Name in log')
        return ""
    def set_player_name(self, player_name):
        '''Sets the player name'''
        self.PLAYER_NAME = player_name
        if self.CONSOLE_VERBOSITY>= 2: print('          Player Name Updated to: ', self.PLAYER_NAME)
        self.PATTERNS = self.update_regex_player_name(self.PLAYER_NAME)


    def process_existing_log(self, file_path):
        '''Analyses a log file that has already been created. Function will terminate once the bottom of the file is reached'''
        
        # Check if the file path is valid
        if not self.is_valid_file_path(file_path):
            return False
        self.set_log_file(file_path)
    
        self.clean_variables()

        if self.settings.value("AssociateProcsToPowers", True, bool):
            self.associating_procs = True
        else:
            self.associating_procs = False

        print('          Processing Log File: ', self.LOG_FILE_PATH)
        _log_process_start_ = time.time()
        #self.set_player_name(self.find_player_name())
        
        #Open file and iterate through each line
        with open(self.LOG_FILE_PATH, 'r', encoding='utf-8') as file:
            refresher = 0
            self.processing_live = True
            for line in file:
                event, data = self.extract_from_line(line)
                self.line_count += 1
                refresher += 1
                if event != "":
                    if self.CONSOLE_VERBOSITY == 4: print(event, data)
                    self.interpret_event(event, data)
                if refresher > 500:
                    refresher = 0
                    QCoreApplication.processEvents()
                    if not self.processing_live: break
        print('          Log File processed in: ', round(time.time() - _log_process_start_, 2), ' seconds')
        self.sig_finished.emit(self.combat_session_data)
        return True
    
    @pyqtSlot()
    def process_live_log(self, file_path):
        if self.CONSOLE_VERBOSITY >= 3: print("Inside method process_live_log, with file_path: ", file_path, '\n')
        # Check if the file path is valid
        if not self.is_valid_file_path(file_path):
            return False
        self.set_log_file(file_path)
        self.clean_variables()
        self.check_parse_settings()
        self.set_player_name(self.find_player_name())



        self.monitoring_timer.timeout.connect(self.monitoring_loop)
        self.monitoring_timer.setInterval(10)
        self.monitoring_timer.start()  # Adjust the interval (in milliseconds) as needed
        self.monitoring_live = True
        if self.CONSOLE_VERBOSITY >= 3: 
            print("monitoring_log timer started:", self.monitoring_timer.isActive(),"|", self.monitoring_timer.interval(), "ms interval")
            # print out the status of the event loop to confirm operation

        self.log_file = open(self.LOG_FILE_PATH, 'r', encoding='utf-8')
        self.log_file.seek(0, 2)
        
    def monitoring_loop(self):

        file = self.log_file
        line = file.readline()
        if not line: return
        event, data = self.extract_from_line(line)
        self.line_count += 1
        if event != "":
            if self.CONSOLE_VERBOSITY == 4: print(event, data)
            self.interpret_event(event, data)
        else:
            event, data = self.extract_datetime_from_line(line)
            self.interpret_event(event, data)

    def live_log_interval_update(self):
        '''Calls a recalculation of the current combat session and updates the UI'''
        # if not CLI_MODE: return
        if not (self.monitoring_live and self.combat_session_live):
            if not self.final_update:
                print('WARNING     No active combat session')
                return
            else:
                if self.CONSOLE_VERBOSITY >= 2: print('          Sending last session update...')
                self.interval_timer.stop()
                self.final_update = False

        with QMutexLocker(self.mutex):
            if self.combat_session_data == []:
                session = []
            else:
                try:
                    session = self.combat_session_data[-1]
                    duration = session.get_duration()
                    #dps = session.get_dps()
                    #acc = session.chars[self.PLAYER_NAME].get_accuracy()

                    if duration > 0 and session.get_total_damage() == 0:
                        session.set_start_time(self.GLOBAL_CURRENT_TIME)  # Reset the start time if there's still no damage

                except IndexError:
                    print("WARNING     No combat session found to update")
                
                except KeyError:
                    print("WARNING     No player found in combat session")
                
                except Exception as e:
                    print("ERROR     getting combat session data: ", e)
            

            self.sig_periodic_update.emit(self.combat_session_data)

    def on_interval_timeout(self):
        '''Reset the timer when the cooldown is over'''
        self.interval_timedout = False
        self.interval_timer.stop()
        self.interval_timer.setInterval(250)

    def check_parse_settings(self):
        '''Checks the settings for the parser'''
        if self.settings.value("AssociateProcsToPowers", Globals.DEFAULT_ASSOCIATE_PROCS_TO_POWERS, bool):
            self.associating_procs = True
        else:
            self.associating_procs = False
        
        self.CONSOLE_VERBOSITY = self.settings.value("ConsoleVerbosity", Globals.DEFAULT_CONSOLE_VERBOSITY, int)
        self.COMBAT_SESSION_TIMEOUT = self.settings.value("CombatSessionTimeout", Globals.DEFAULT_COMBAT_SESSION_TIMEOUT, int)
        self.COMBAT_SESSION_NAME = self.settings.value("CombatSessionName", Globals.DEFAULT_COMBAT_SESSION_NAME, str)

    def on_sig_stop_monitoring(self):
        '''Stops monitoring the log file'''
        self.monitoring_timer.stop()
        print('          Monitoring Ended.')
        if self.combat_session_live: self.end_current_session()
        self.monitoring_live = False
        self.processing_live = False
        self.sig_finished.emit(self.combat_session_data)