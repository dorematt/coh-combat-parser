
import os.path
import re
import time
from datetime import datetime
from combat.Ability import Ability
from combat.Character import Character
from combat.DamageComponent import DamageComponent
from combat.CombatSession import CombatSession
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QMutex, QMutexLocker, QTimer, QCoreApplication, QSettings
from data.Globals import Globals
from data.pseudopets import is_pseudopet
from data.LogPatterns import PATTERNS, PATTERN_DATETIME
CLI_MODE = False # Flipped to True if this .py file is launched directly instead of through the UI

class Parser(QObject):
    '''Extracts data from log lines using regex patterns, Will return a list of tuples containing the log entry type and a dictionary of the extracted data.'''

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
        '''Resets all the parser variables to their default values. This is called when a new log file is loaded or when the parser is reset'''
        self.line_count = 0
        self.combat_session_data = [] # Stores a list of combat sessions
        self.no_hitroll_ability_list = [] # Stores a list of abilities that have no hit roll events (ie. were discovered and added using a damage event)
        self.session_count = 0 # Stores the number of combat sessions and also acts as a key to which combat session within the combat_session array is active
        self.session_name_count = 0 # For counting the number of sessions with the same name
        self.combat_session_live = False # Flag to indicate if a combat session is active
        self.in_combat = False # Flag to indicate that the player is/has dealing damage
        self.global_combat_duration = 0 # Stores the total durations of all combat sessions

        # Set Exp and Influence values
        self.EXP_VALUE = 0
        self.INF_VALUE = 0
        
        # create a key-value list of abilities
        self.GOBAL_START_TIME = 0 # Stores the timestamp of the first event as an int
        self.GLOBAL_CURRENT_TIME = 0 # Stores the latest timestamp as an int
        self.final_update = False # Flag to indicate if a final update is required
        self.user_session_name = ""

        if self.CONSOLE_VERBOSITY >= 2: print('          Parser variables cleaned...')

    
    def update_regex_player_name(self, player_name):
        '''Updates the regex patterns to include the player name, returns a dict of the updated regex patterns for the purposes of debugging and testing.'''
        updated_patterns = {}
        for key, regex in PATTERNS.items():
            updated_pattern = regex.pattern.replace('PLAYER_NAME', player_name)
            updated_regex = re.compile(updated_pattern)
            if self.CONSOLE_VERBOSITY == 3: print('Updated Regex: ', updated_regex)
            
            updated_patterns[key] = updated_regex
        return updated_patterns
    
    def extract_from_line(self, log_line):
        '''Extracts data from a log line using regex patterns, returns a string for the log entry type and a dict of the extracted data.'''
        for key, regex in PATTERNS.items():
            match = regex.match(log_line)
            if match:
                return (key, match.groupdict())
        return '',[]
    def extract_datetime_from_line(self, log_line):
        '''Faster version of extract_from_line that only extracts the datetime from the log line (for use in live monitoring updates)'''
        for key, regex in PATTERN_DATETIME.items():
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
        self.in_combat = False
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
    def remove_last_session(self):
        '''Removes the current combat session'''
        if self.CONSOLE_VERBOSITY >= 2: print ("---------->  Removed Combat Session: ", self.session_count, '\n')
        self.combat_session_data.pop()
        self.session_count -= 1
        self.session_name_count -= 1
        self.combat_session_live = False
        if self.monitoring_live: self.final_update = True
        

    def print_session_results(self, session):
        '''Displays the results of the current combat session'''
        if self.monitoring_live:
            output_tag = "Concluded"
        else:
            output_tag = "Processed"
        print("              Combat Session ",output_tag,": ", self.combat_session_data[-1].name, ", ", session.get_duration(), "s duration.", sep="")
        return
        
    def interpret_event(self, event, data):
        '''Interprets the data generated by the extract_from_line function and prepares it for the appropriate handler function.
        This will handle updating the global time, checking for combat session status and calling the event handler functions'''
        # Check for an active combat session and determine if it is still active

        # Update the current time and check combat session status
        with QMutexLocker(self.mutex):
            self.update_global_time(self.convert_timestamp(data["date"], data["time"]))
            timestamp = self.GLOBAL_CURRENT_TIME
            status = self.check_session(timestamp)

            def trigger_session_update(in_combat): # Helper function to call session updates as well as beginning new sessions
                if status == 0 or status == -1:
                    self.new_session(timestamp)
                    self.combat_session_data[-1].update_session_time(timestamp, in_combat)
                if in_combat:
                    self.combat_session_data[-1].update_session_time(timestamp, in_combat)


            if status == -1: # Checking for a timed-out combat session

                # Remove the session if it had no damage
                if self.combat_session_data[-1].has_no_damage():
                    self.remove_last_session()
                else:
                    self.end_current_session()
                    self.combat_session_live = False
                    self.print_session_results(self.combat_session_data[-1])

            # Clean the data of all None types
            for key in data:
                if data[key] is None:
                    data[key] = ""

            if event == "player_ability_activate":
                trigger_session_update(False)
                self.handle_event_player_power_activate(data)
                

            if event == "player_hit_roll" or event == "player_pet_hit_roll":
                trigger_session_update(False)
                self.handle_event_player_hit_roll(data, event == "player_pet_hit_roll")

            elif event == "player_damage" or event == "player_pet_damage":
                trigger_session_update(True)
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
        '''Handles power activation events found by the interpret_event function. This function will also create new abilities in the character list if they don't already exist.
        It will additionally set the active ability to the last used ability for the purposes of associating proc damage.'''

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
        player.last_ability = this_ability # Setting the active ability here to cover non-damaging abilities with procs attached to them

    def handle_event_player_hit_roll(self, data, pet=False):
        '''Handles a player hit roll event, assumes it came from player instead of pet unless pet=True'''

        # Ignore events where the player hits themselves
        if data["target"] == self.PLAYER_NAME:
            print(f'Player hit themselves with {data["ability"]}. Ignoring')
            return

        # Determine the ability and caster based on pet status
        this_ability = data["ability"]

        if pet:
            if is_pseudopet(data["pet_name"]):
                caster = self.PLAYER_NAME
            else:
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
        '''Handles a player damage event found by the interpret_event function.
        This function will also handle damage from proc effects, if the setting is enabled it will associate the proc damage with the last used ability'''
        
        # Ignore events where the player hits themselves
        if data["target"] == self.PLAYER_NAME:
            return
        
        if "Damage" in data["ability_desc"] or data["ability"] == "Doublehit" :
            proc = True
        else:
            proc = False


        this_ability = data["ability"]
        flair = data["damage_flair"]
        damage = float(data["damage_value"])

        if flair != "":
            type = (data["damage_type"] + " " + data["damage_flair"])
        else:
            type = data["damage_type"]

        if pet:
            if is_pseudopet(data["pet_name"]):
                caster = self.PLAYER_NAME
            else:
                caster = data["pet_name"]
        else:
            caster = self.PLAYER_NAME

        # Check and update the session's character list
        this_session = self.combat_session_data[-1]

        if caster not in this_session.chars:
            this_session.chars[caster] = Character(caster)
            if pet: this_session.chars[caster].is_pet = True
            if self.CONSOLE_VERBOSITY >= 3:
                print(f"     Added Character: {caster} to Session: {self.session_count} via Damage Event")

        caster = this_session.chars[caster]
        

        if proc and caster.last_ability is not None:
            if self.associating_procs:
                if flair != "": 
                    proc_name = (data["ability"] + " " + data["damage_flair"])
                else:
                    proc_name = data["ability"]
                caster.last_ability.add_damage(DamageComponent(proc_name),damage)
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

        # Some DoT auras don't have hit rolls recorded in the log when they hit, so we'll put those abilities in a list to add successful hit events via damage events instead
        if not proc and this_ability.get_hits() == 0:
            self.no_hitroll_ability_list.append(this_ability)
        
        if this_ability in self.no_hitroll_ability_list:
            this_ability.ability_used()
            this_ability.ability_hit(True)
        
        caster.last_ability = this_ability

  
    def handle_event_reward_gain(self, data):
        '''Handles a reward gain event, found by the interpret_event function'''
        
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
        '''Reads the log file from bottom to top, to find the last player name pattern (which is the welcome message the player recieves upon login) and returns'''
        # Check if the log file path is set
        if self.LOG_FILE_PATH == "":
            print('          Cannot find Player Name - Log File Path not set')
        
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
            refresher = 0 #just keeps the UI responsive
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
        if self.CONSOLE_VERBOSITY >= 4: print("Inside method process_live_log, with file_path: ", file_path, '\n')

        if not self.is_valid_file_path(file_path):
            return False
        self.set_log_file(file_path)
        self.check_parse_settings() # Call this again in case settings have been adjusted at all
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
        '''Calls a recalculation of the current combat session data and emits a signal to update the UI. This function is called by the interval_timer'''
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


    def check_parse_settings(self):
        '''Checks for QSettings and sets the parser settings appropriately. If no settings are found, the default settings are used.'''

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