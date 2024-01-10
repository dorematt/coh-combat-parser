import re
import os
import time
from datetime import datetime
import random
from tkinter import filedialog as tk
import sys
from PyQt5.QtCore import QObject, pyqtSignal, QMutex, QMutexLocker

CONSOLE_VERBOSITY = 1
CLI_MODE = False # Flipped to True if this .py file is launched directly instead of through the UI

class Parser(QObject):
    '''Extracts data from log lines using regex patterns, Will return a list of tuples containing the log entry type and a dictionary of the extracted data.'''
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
            r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?:PLAYER_NAME:  )?(?:You (?:hit|hits you with their)|HIT) (?P<target>[^:]+) with your (?P<ability>[^:]+)(?:: (?P<ability_desc>[\w\s]+))? for (?P<damage_value>[\d.]+) points of (?P<damage_type>[^\d]+) damage(?: over time)?\.*"
        ),
        "player_pet_damage": re.compile(
            r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) (?P<pet_name>[^:]+?):? * (?:You (?:hit|hits you with their)|HIT) (?P<target>[^:]+) with your (?P<ability>[^:]+)(?:: (?P<ability_desc>[\w\s]+))? for (?P<damage_value>[\d.]+) points of (?P<damage_type>[^\d]+) damage(?: over time)?\.*"
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
    PATTERN_DATETIME = {
        "date_time": re.compile(
        r"(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2})"
        )
    }
    LOG_FILE_PATH = ""
    PLAYER_NAME = ""
    COMBAT_SESSION_TIMEOUT = 15 # Seconds, determines how long to wait between  # 0 = Silent, 1 = Errors and Warnings, 3 = Errors, Warnings and Info, 3 = Debug level 1, 4 = Debug level 2
    monitoring_live = False # Flag to indicate if the parser is monitoring a live log file
    combat_session_data = [] # Stores a list of combat sessions
    mutex = QMutex()
    sig_finished = pyqtSignal(list)
    sig_periodic_update = pyqtSignal(list)

    def __init__(self, LOG_FILE_PATH = ""):
        super().__init__()
        print('     Parser Initialize...')
        self.clean_variables()
    
    def update_regex_player_name(self, player_name):
        updated_patterns = {}
        for key, regex in self.PATTERNS.items():
            updated_pattern = regex.pattern.replace('PLAYER_NAME', player_name)
            updated_regex = re.compile(updated_pattern)
            if CONSOLE_VERBOSITY == 3: print('Updated Regex: ', updated_regex)
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
        self.combat_session_data.append(CombatSession(timestamp))
        self.combat_session_live = True
        if CONSOLE_VERBOSITY >= 2: print ("---------->  Combat Session Started: ", self.session_count, '\n')
        return self.combat_session_data[-1]
    def check_session(self, timestamp):
        '''Checks sessions, returns an int code for whether the session, exists or is outside the timeout duration'''

        if self.combat_session_live:
            # print('     Checking Session: ', self.session_count, ' With a duration of ', self.session[-1].get_duration(), ' seconds')
            chk_time = timestamp - self.combat_session_data[-1].end_time
            # print(' Time since last activity in session: ', chk_time, ' seconds')
            if chk_time > self.COMBAT_SESSION_TIMEOUT:
                return -1 # Session over timeout
            else:
                return 1 # Session still active and valid
        return 0 # No active session
    def end_current_session(self):
        '''Ends the current combat session'''
        self.combat_session_data[-1].update_duration()
        self.combat_session_live = False
        self.add_global_combat_duration(self.combat_session_data[-1].get_duration())
        if CONSOLE_VERBOSITY >= 2: print ("---------->  Ended Combat Session: ", self.session_count, " With a duration of ", self.combat_session_data[-1].get_duration(), " seconds \n")
    def remove_last_session(self):
        '''Removes the current combat session'''
        if CONSOLE_VERBOSITY >= 2: print ("---------->  Removed Combat Session: ", self.session_count, '\n')
        self.combat_session_data.pop()
        self.session_count -= 1
        self.combat_session_live = False
        
    def update_session_time(self, timestamp):
        '''Updates the current combat session time'''
        self.combat_session_data[-1].update_session_time(timestamp)
    def print_session_results(self, session):
        '''Displays the results of the current combat session'''
        if not CLI_MODE: 
            print("              Combat Session ", self.session_count, ", ", session.get_duration(), "s duration processed.", sep="")
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

            if CONSOLE_VERBOSITY > 1:
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
            

    def handle_event_player_power_activate(self, data):

        # We'll use these power_activation events in the log to create new abilties in our list
        if data["ability"] not in self.abilities:
            self.abilities[data["ability"]] = Ability(data["ability"])
        
        # Check if the player is in the char list for the current session, if not, add them and add the ability.
        name = self.PLAYER_NAME
        if name not in self.combat_session_data[-1].chars: 
            self.combat_session_data[-1].chars[name] = Character(name)
            if CONSOLE_VERBOSITY >= 3: print("     Added New Character: ", self.combat_session_data[-1].chars[name].get_name(), " to Session: ", self.session_count, ' via Power Activation Event')
        
        if data["ability"] not in self.combat_session_data[-1].chars[name].abilities: 
            self.combat_session_data[-1].chars[name].abilities[data["ability"]] = Ability(data["ability"])
            
            if CONSOLE_VERBOSITY >= 3: print("     Added Ability: ", data["ability"], " to Character: ", self.combat_session_data[-1].chars[name].get_name(), ' via Power Activation Event')
        
        self.combat_session_data[-1].chars[name].abilities[data["ability"]].ability_used()

    def handle_event_player_hit_roll(self, data, pet=False):
        '''Handles a player hit roll event, assumes it came from player instead of pet unless pet=True'''

        # Ignore events where the player hits themselves
        if data["target"] == self.PLAYER_NAME:
            print(f'Player hit themselves with {data["ability"]}. Ignoring')
            return

        # Determine the ability and caster based on pet status
        if pet:
            search_ability = f"{data['pet_name']}: {data['ability']}"
            caster = data["pet_name"]
        else:
            search_ability = data["ability"]
            caster = self.PLAYER_NAME

        # Create or get the ability and update hit roll
        active_ability = self.abilities.setdefault(search_ability, Ability(search_ability))
        active_ability.ability_hit(data["outcome"] == "HIT")

        # Check and update the session's character list
        session = self.combat_session_data[-1]

        if caster not in session.chars: 
            session.chars[caster] = Character(caster)
            if pet: session.chars[caster].is_pet = True
            if CONSOLE_VERBOSITY >= 2:
                print(f"     Added Character: {caster} to Session: {self.session_count} via Hit Roll Event")

        char = session.chars[caster]

        if search_ability not in char.abilities:
            char.abilities[search_ability] = Ability(search_ability)
            if CONSOLE_VERBOSITY >= 3:
                print(f"     Added Ability: {search_ability} to Character: {char.get_name()} via Hit Roll Event")

        # if pet: char.get_ability(search_ability).ability_used() # We don't have power activation events for pets, so we'll use the hit roll as a proxy for ability usage
        char.get_ability(search_ability).ability_hit(data["outcome"] == "HIT") 
    def handle_event_player_damage(self, data, pet=False):
        '''Handles a player damage event'''

        # Ignore events where the player hits themselves
        if data["target"] == self.PLAYER_NAME:
            return

        # determine if this is a pet or the player damage event
        if pet:
            search_ability = f"{data['pet_name']}: {data['ability']}"
            caster = data["pet_name"]
        else:
            search_ability = data["ability"]
            caster = self.PLAYER_NAME

        # Create or get the ability and update damage
        active_ability = self.abilities.setdefault(search_ability, Ability(search_ability, None, True))
        active_ability.add_damage(DamageComponent(data["damage_type"]),float( data["damage_value"]))

        # Check and update the session's character list
        session = self.combat_session_data[-1]

        if caster not in session.chars:
            session.chars[caster] = Character(caster)
            if pet: session.chars[caster].is_pet = True
            if CONSOLE_VERBOSITY >= 3:
                print(f"     Added Character: {caster} to Session: {self.session_count} via Damage Event")

        char = session.chars[caster]

        if search_ability not in char.abilities:
            char.add_ability(search_ability, Ability(search_ability, None, True))
            if CONSOLE_VERBOSITY >= 3:
                print(f"     Added Proc: {search_ability} to Character: {char.get_name()} via Damage Event")
        ability = char.get_ability(search_ability)
        if CONSOLE_VERBOSITY >= 3: 
                print( '------------- ', ability.name)
        ability.add_damage(DamageComponent(data["damage_type"]), float(data["damage_value"]))
        if CONSOLE_VERBOSITY >= 3: 
                print ('         Damage Component Added: ', ability.damage[-1].type, ability.damage[-1].total_damage, 'Count: ', ability.damage[-1].count)
  
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
        if CONSOLE_VERBOSITY>= 2: print('          Player Name Updated to: ', self.PLAYER_NAME)
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
        with open(self.LOG_FILE_PATH, 'r', encoding='utf-8') as file:
            for line in file:
                event, data = self.extract_from_line(line)
                self.line_count += 1
                if event != "":
                    if CONSOLE_VERBOSITY == 4: print(event, data)
                    self.interpret_event(event, data)
        if CLI_MODE: _test_show_results()
        print('          Log File processed in: ', round(time.time() - _log_process_start_, 2), ' seconds')
        self.sig_finished.emit(self.combat_session_data)
        return True
    
    def process_live_log(self, file_path):
        '''Opens the file path and monitors the file for new entries until terminated. 
        This will not process any existing entries in the log file'''

        # Check if the file path is valid
        if not self.is_valid_file_path(file_path):
            return False
        self.set_log_file(file_path)

        self.clean_variables()


        self.set_player_name(self.find_player_name())

        def monitoring_routine():
            heartbeat = 0
            while self.monitoring_live:
                line = file.readline()
                if not line:
                    heartbeat += 1
                    time.sleep(0.01)
                    continue
                event, data = self.extract_from_line(line)
                self.line_count += 1
                if event != "":
                    if CONSOLE_VERBOSITY == 4: print(event, data)
                    self.interpret_event(event, data)
                    self.live_log_interval_update()
                    heartbeat = 0
                elif heartbeat > 100:
                    event, data = self.extract_datetime_from_line(line)
                    # TODO: Call a function to update DPS and other values
                    self.interpret_event(event, data)
                    self.live_log_interval_update()
                    heartbeat = 0
                else:
                    heartbeat += 1
                    time.sleep(0.01)
                    continue
            
            print('          Monitoring Terminated')
            self.sig_finished.emit(self.combat_session_data)


        with open(self.LOG_FILE_PATH, 'a+') as file:
            file.seek(0, 2)  # Move the file pointer to the end of the file
            print('          Monitoring Log File: ', self.LOG_FILE_PATH)
            self.monitoring_live = True
            monitoring_routine()

    def live_log_interval_update(self):
        '''Calls a recalculation of the current combat session and updates the UI'''
        # if not CLI_MODE: return
        if not (self.monitoring_live and self.combat_session_live):
            print('ERROR     No active combat session')
            return

        with QMutexLocker(self.mutex):
            try:
                session = self.combat_session_data[-1]
                duration = session.get_duration()
                dps = session.get_dps()
                acc = session.chars[self.PLAYER_NAME].get_accuracy()

                if duration > 0 and session.get_total_damage() == 0:
                    session.set_start_time(self.GLOBAL_CURRENT_TIME)  # Reset the start time if there's still no damage


            except IndexError:
                print("ERROR     No combat session found")

            if CLI_MODE: print(" Combat Session: ", self.session_count, " | Duration: ", duration, "s | DPS: ", dps,
                " | Acc: ", acc, "%", end='\r')
            else: self.sig_periodic_update.emit(self.combat_session_data)

    def on_sig_stop_monitoring(self):
        '''Stops monitoring the log file'''
        self.monitoring_live = False

    def clean_variables(self):
        '''Reset all'''
        self.line_count = 0
        self.combat_session_data = [] # Stores a list of combat sessions
        self.session_count = 0 # Stores the number of combat sessions and also acts as a key to which combat session within the combat_session array is active
        self.combat_session_live = False # Flag to indicate if a combat session is active
        self.global_combat_duration = 0 # Stores the total durations of all combat sessions

        # Set Exp and Influence values
        self.EXP_VALUE = 0
        self.INF_VALUE = 0
        
        # create a key-value list of abilities
        self.Chars = {} # Stores a list of characters
        self.abilities = {} # Stores a list of abilities
        self.GOBAL_START_TIME = 0 # Stores the timestamp of the first event as an int
        self.GLOBAL_CURRENT_TIME = 0 # Stores the latest timestamp as an int

        if CONSOLE_VERBOSITY >= 2: print('          Parser reset...')
        
class CombatSession(QObject):
    '''The CombatSession class stores data about a combat session, which is a period where damage events are registered.
    CombatSessions will automatically end based on the COMBAT_SESSION_TIMEOUT value to avoid including long downtime periods in the data.''' 
    def __init__(self, timestamp=0):
        super().__init__()
        self.start_time = timestamp
        self.end_time = timestamp
        self.duration = 0 # Seconds
        self.chars = {} # Stores a list of characters
        self.exp_value = 0
        self.inf_value = 0
        

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
    
    def get_total_damage(self):
        '''Calculates the total damage for the session'''
        sum = 0
        for char in self.chars:
            sum += self.chars[char].get_total_damage()
        return round(sum,2)
    
    def get_average_damage(self):
        '''Calculates the average damage for the session'''
        damage = self.get_total_damage()
        if damage > 0 : damage =  round(damage / self.get_count(),2)
        return damage
    
    def get_dps(self):
        '''Calculates the DPS for the session based off of the damage components'''
        dps = 0
        for char in self.chars:
            dps += self.chars[char].get_dps(self.duration)
        return round(dps,2)
    
    def add_exp(self, exp_value):
        '''Adds the exp value to the total exp'''
        self.exp_value += exp_value
    def add_inf(self, inf_value):
        '''Adds the inf value to the total inf'''
        self.inf_value += inf_value
    def get_exp(self):
        '''Returns the total exp'''
        return self.exp_value
    def get_inf(self):
        '''Returns the total inf'''
        return self.inf_value
    
    def add_character(self, character):
        self.chars[character.get_name()] = character

class Character(QObject):
    '''Stores data about a character, this can be the Player, pets or enemies'''
    def __init__(self, name="") -> None:
        super().__init__()
        self.name = name
        self.abilities = {}
        self.is_pet = False

    def add_ability(self, ability_name, ability):
        self.abilities[ability_name] = ability

    def get_ability(self, ability_name):
        if ability_name not in self.abilities:
            return ""
        return self.abilities[ability_name]
    
    def get_name(self):
        return self.name
    
    def get_total_damage(self):
        '''Calculates the total damage for the character'''
        sum = 0
        if self.abilities == {}: return sum
        for ability in self.abilities:
            sum += self.abilities[ability].get_total_damage()
        return round(sum,2)
    
    def get_average_damage(self):
        '''Calculates the overall average damage per hit for the character by looping through all abilities' average damage and returning the sum'''
        average = 0
        ability_count = 0
        if self.abilities == {}: return average
        for ability in self.abilities:
            average += self.abilities[ability].get_average_damage()
            ability_count += 1
        if ability_count  > 0 and average > 0:
            return round(average / ability_count,2)
        return average

    def get_accuracy(self):
        '''Calculates the accuracy for the character'''
        if self.abilities == {}: return 0
        hits = 0
        tries = 0
        for ability in self.abilities:
            hits += self.abilities[ability].get_hits()
            tries += self.abilities[ability].get_tries()
        if tries == 0: return 0
        return round((hits / tries) * 100,2)
    
    def get_dps(self, duration):
        '''Calculates the DPS for the character based off of the damage components'''
        dps = 0
        if self.abilities == {}: return dps
        for ability in self.abilities:
            dps += self.abilities[ability].get_dps(duration)
        return round(dps,2)
    
    def get_count(self):
        '''Returns the number of times the character has been used'''
        count = 0
        if self.abilities == {}: return count
        for ability in self.abilities:
            count += self.abilities[ability].get_count()
        return count
    
class Ability(QObject):
    '''Stores data about an ability used'''
    def __init__(self, name, hit=None, proc=False):
        super().__init__()
        self.name = name
        self.count = 0
        self.tries = 0 if hit is None else 1
        self.hits = 1 if hit is True else 0
        self.damage = []
        self.proc = proc
        self.pet = False
        self.pet_name = "" # If ability came from a pet, store the pet name

    def add_damage(self, damage_component, value = 0):
        '''Adds a damage component to the ability'''
        # Check if damage type is already in the ability, if it is, add the damage to the existing component
        for component in self.damage:
            if component.type == damage_component.type:
                component.add_damage(damage_component.type, value)
                if self.proc: 
                    self.ability_used()
                    
                #print ('Added to existing damage component to ', self.name, ' | ', damage_component.type, ' | ', self.get_total_damage(), ' | ', self.damage[-1].get_count())
                return
            
        self.damage.append(damage_component)
        self.damage[-1].add_damage(damage_component.type, value)
        #print ('Added new damage component to ', self.name, ' | ', damage_component.type, ' | ', self.get_total_damage(), ' | ', self.damage[-1].get_count())

        if self.proc:
            self.ability_used() 
    
    def ability_used(self):
        '''Handles incrementing the count for each time ability is used. Can also be called during a hit check to increment the hit counter'''
        self.count += 1
    def ability_hit(self, hit):
        self.tries += 1
        if hit: self.hits += 1
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
    def get_max_damage(self):
        '''Returns the highest damage for the ability'''
        highest = 0
        for component in self.damage:
            highest += component.get_highest_damage()
        return highest
    def get_min_damage(self):
        '''Returns the lowest damage for the ability'''
        lowest = 0
        for component in self.damage:
            lowest = component.get_lowest_damage()
        return lowest
    def get_average_damage(self):
        '''Calculates the average damage for the ability'''
        average = 0
        for component in self.damage:
            average += component.get_average_damage()
        return round(average,2)
    
    def get_accuracy(self):
        '''Calculates the accuracy for the ability'''
        if self.hits == 0 or self.tries == 0:
            return 0
        return round((self.hits / self.tries) * 100,2)
    
    def get_count(self):
        '''Returns the number of times the ability has been used'''
        return self.count
    
    def get_dps(self, duration):
        '''Calculates the DPS for the ability based off of the damage components'''
        dps = 0
        for component in self.damage:
            dps += component.get_dps(duration)
        return round(dps,2)

    def get_hits(self):
        '''Returns the number of times the ability has hit'''
        return self.hits
    def get_tries(self):
        '''Returns the number of times the ability has been used'''
        return self.tries
class DamageComponent(QObject):
    '''Stores data about a damage component'''
    def __init__(self, type="", value : float = 0):
        super().__init__()
        self.count = 0
        self.type = type
        self.name = type
        self.total_damage = value
        self.highest_damage = 0
        self.lowest_damage = 0
    
    def add_damage(self, type, value : float):
        '''Adds damage value to the damage component'''
        self.count += 1
        self.total_damage += value
        self.total_damage = round(self.total_damage, 2)
        self.update_min_max_damage(value)
    
    def get_dps(self, duration):
        '''Calculates the DPS for the damage component'''
        if duration == 0: return self.total_damage
        else: return round(self.total_damage / duration, 2)
    def get_average_damage(self):
        '''Calculates the average damage for the damage component'''
        if self.count == 0: return self.total_damage
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
    def get_damage_component(self):
        return self
    def get_count(self):
        '''Returns the number of times the damage component has been used'''
        return self.count
    def update_min_max_damage(self, value : float):
        '''Updates the min and max damage for the damage component'''
        if value >= self.highest_damage or self.highest_damage == 0:
            self.highest_damage = value
            #print ('         Highest Damage Updated: ', self.highest_damage)
        if value <= self.lowest_damage or self.lowest_damage == 0:
            self.lowest_damage = value
            #print ('         Lowest Damage Updated: ', self.highest_damage)
    
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
            if event != "":
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
        if event != "":
            print(event, data)
            self.interpret_event(event, data)
def _test_log_file():
    print('\n \n', "---- STARTING LOG FILE DATA TEST -----", '\n \n')
#Open text file with test data, similarly test extraction data
    with open('C:\\Users\\mdore\\OneDrive\\02_Documents\\02_SCRIPTS\\CoH_Log_Parser\\coh_logfile_snippet.txt', 'r') as file:
        for line in file:
            event, data = self.extract_from_line(line)
            self.line_count += 1
            if event != "":
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
    for ability in self.abilities:
        if self.abilities[ability].get_count() == 0: continue # skip abilities with no count
        print(self.abilities[ability].name, ' (proc)' if self.abilities[ability].proc else '',
              '\n    DPS: ', self.abilities[ability].get_dps(self.global_combat_duration), 'Avg: ', self.abilities[ability].get_average_damage(),
              '\n    Accuracy: ', self.abilities[ability].get_accuracy(), '% | Count: ', self.abilities[ability].count, '| Hits: ', self.abilities[ability].hits, '|')
        
        
        # loop down the damage components and print the damage type, total damage and count
        for component in self.abilities[ability].damage:
            print('        Damage Type: ', component.type,'| T:', component.total_damage,'| H:', component.highest_damage, '| L:', component.lowest_damage, '| Count: ', component.count)
        print('------------------')

    total_damage = 0
    print('')
    for ability in self.abilities:
        total_damage += self.abilities[ability].get_total_damage()
    print('Total Damage: ', round(total_damage,2))
    print('Total Damage using Combat Sessions: ', round(total_damage,2))
    print('Total Duration of the log:', format_duration(self.get_log_duration()))
    print('Total Combat Duration:', format_duration(self.global_combat_duration))
    print('Total Combat Sessions: ', self.session_count)
    print('Total Damage Per Second: ', self.get_dps(self.global_combat_duration))
    print('Lines processed: ', self.line_count)

def _test_combat_sessions():
    pass

def open_file():
    root = tk.Tk()
    root.withdraw()
    file_path = tk.askopenfilename()
    return file_path

def handle_commands(self, command):
    '''When run in CLI mode, text commands entered will be processed'''
    if command.lower == "t":
        self.process_existing_log('path_to_test_file.txt')

    elif command.lower() in  ["live", "l"]:
        file_path = open_file()
        if file_path != "":
            self.process_live_log(file_path)
        # print("Live monitoring is not implemented yet.")
            
    elif command.lower() in ["analyze", "a", "analyse"]:
        file_path = open_file()
        if file_path != "":
            self.process_existing_log(file_path)
    
    elif command.lower() in ["exit", "quit", "q"]:
        print("Exiting...")
        sys.exit()
    else:
        print("Unknown command. Please enter a valid command.")    
if __name__ == "__main__":
    # if this is being run directly, run the test data
    print("Parser has been directly called as __main__, running test data")

    #PLAYER_NAME = "Emet Selch"
    self = Parser()
    
    self.line_count = 0
    CLI_MODE = True

    #Initiate tests
    #_test_hit_rolls()
    #_test_damage_lines()
    #_test_reward_lines()
    #test_file = open_file()
    #self.process_existing_log(test_file)


    while True:
        user_command = input("Enter a command (e.g., 'run_test_file', 'live_monitor', 'analyze_log_file <path_to_log_file>'): ")
        handle_commands(self, user_command)
                