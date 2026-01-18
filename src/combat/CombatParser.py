
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
from data.no_hit_abilities import is_no_hit_ability
from data.LogPatterns import PATTERNS, PATTERN_DATETIME
CLI_MODE = False # Flipped to True if this .py file is launched directly instead of through the UI

class Parser(QObject):
    '''
    This class handles parsing the combat log file, either live or from an existing file. It will iterate through a given log file, setting up combat sessions and organizing data as it goes.
    '''

    LOG_FILE_PATH = ""
    log_file = None
    PLAYER_NAME = ""# Seconds, determines how long to wait between  # 0 = Silent, 1 = Errors and Warnings, 3 = Errors, Warnings and Info, 3 = Debug level 1, 4 = Debug level 2
    monitoring_live = False # Flag to indicate if the parser is monitoring a live log file
    processing_live = False # Flag to indicate when processing is active (or used to terminate processing)
    combat_session_data = [] # Stores a list of combat sessions
    combat_mutex = QMutex()
    sig_finished = pyqtSignal(list)
    sig_periodic_update = pyqtSignal(list)
    sig_error = pyqtSignal(str, str)  # Signal for errors (message, title)
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
        self.no_hitroll_ability_list = {} # Stores a list of abilities that have no hit roll events (ie. were discovered and added using a damage event)
        self.session_count = 0 # Stores the number of combat sessions and also acts as a key to which combat session within the combat_session array is active
        self.session_name_count = 0 # For counting the number of sessions with the same name
        self.last_session_base_name = "" # Stores the base name (without number) of the last session for increment reset logic
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
        # Use self.PATTERNS if it exists (updated with player name), otherwise fall back to module PATTERNS
        patterns = getattr(self, 'PATTERNS', PATTERNS)
        for key, regex in patterns.items():
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

    def get_session_base_name(self, session):
        '''Determines the base name for a session based on the current naming mode

        :param session: The CombatSession object to get base name for
        :return: The base name (without numerical suffix), or None if not yet available
        '''
        # If user has set a custom name via command, use it (highest priority)
        if self.user_session_name != "":
            return self.user_session_name

        # Check naming mode
        if self.COMBAT_SESSION_NAMING_MODE == "First Enemy Damaged":
            first_enemy = session.get_first_enemy_damaged()
            return first_enemy if first_enemy else None
        elif self.COMBAT_SESSION_NAMING_MODE == "Highest Enemy Damaged":
            highest_enemy = session.get_highest_damaged_enemy()
            return highest_enemy if highest_enemy else None
        else:  # Default to "Custom Name" mode
            return self.COMBAT_SESSION_NAME

    def get_last_session_number_for_base_name(self, base_name, current_session_index=None):
        '''Finds the highest session number used for a given base name in previous sessions

        :param base_name: The base name to search for
        :param current_session_index: Index of current session to exclude (if updating existing session)
        :return: The highest number used, or 0 if not found
        '''
        max_number = 0
        for i, sess in enumerate(self.combat_session_data):
            # Skip the current session if we're updating it
            if current_session_index is not None and i == current_session_index:
                continue

            sess_name = sess.get_name()
            # Extract base name by removing the last word (number)
            parts = sess_name.rsplit(" ", 1)
            if len(parts) == 2:
                sess_base = parts[0]
                try:
                    sess_num = int(parts[1])
                    if sess_base == base_name and sess_num > max_number:
                        max_number = sess_num
                except ValueError:
                    pass  # Not a number suffix

        return max_number

    def generate_session_name(self, session, is_new_session=False):
        '''Generates a session name based on the current naming mode setting

        :param session: The CombatSession object to generate a name for
        :param is_new_session: True if this is a brand new session being created
        :return: The generated name with numerical suffix
        '''
        base_name = self.get_session_base_name(session)

        # If we don't have a base name yet (no enemy data), use fallback
        if base_name is None:
            base_name = self.COMBAT_SESSION_NAME

        # Determine the session number
        if is_new_session:
            # For new sessions, check last session's base name
            if base_name != self.last_session_base_name:
                self.session_name_count = 0
                self.last_session_base_name = base_name
            self.session_name_count += 1
        else:
            # For updates to existing session, look through session history
            # Find the current session's index
            current_index = len(self.combat_session_data) - 1
            last_num = self.get_last_session_number_for_base_name(base_name, current_index)
            self.session_name_count = last_num + 1
            self.last_session_base_name = base_name

        return base_name + " " + str(self.session_name_count)

    def new_session(self, timestamp):
        self.session_count += 1
        # Create session and generate initial name
        new_session = CombatSession(timestamp, "")
        self.combat_session_data.append(new_session)

        # Generate the name based on naming mode (will use fallback if no enemy data yet)
        name = self.generate_session_name(new_session, is_new_session=True)
        new_session.set_name(name)

        self.combat_session_live = True
        self.in_combat = False
        if self.monitoring_live: self.interval_timer.start() # Begins periodic UI refreshes
        if self.CONSOLE_VERBOSITY >= 2: print ("---------->  Combat Session Started: ", self.session_count, '\n')
        return self.combat_session_data[-1]
    
    def check_session(self, timestamp):
        '''Checks sessions, returns an int code for whether the session, exists or is outside the timeout duration
        
        :param timestamp: Current timestamp to check against
        :return: 1 = Session active and valid, 0 = No active session, -1 = Session timed out
        '''

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
        '''Ends the current combat session, finalizes session naming if necessary, calls one last live_monitoring update'''
        session = self.combat_session_data[-1]
        session.update_duration()

        # Final name update for "Highest Enemy Damaged" mode
        if self.user_session_name == "" and self.COMBAT_SESSION_NAMING_MODE == "Highest Enemy Damaged":
            highest_enemy = session.get_highest_damaged_enemy()
            if highest_enemy is not None:
                current_name = session.get_name()
                # Extract current base name (without number suffix)
                current_base = " ".join(current_name.split(" ")[:-1])

                # Only update if the highest enemy is different from current name
                if current_base != highest_enemy:
                    new_name = self.generate_session_name(session)
                    session.set_name(new_name)
                    if self.CONSOLE_VERBOSITY >= 2:
                        print(f"     Final session rename from '{current_name}' to '{new_name}' (highest damaged enemy)")

        self.combat_session_live = False
        self.add_global_combat_duration(session.get_duration())
        if self.CONSOLE_VERBOSITY >= 2: print ("---------->  Ended Combat Session: ", self.session_count, " With a duration of ", session.get_duration(), " seconds \n")
        if self.monitoring_live: self.final_update = True

        # Emit periodic update when processing existing logs (for UI updates during initial processing)
        # Don't hold mutex while emitting signal to avoid blocking
        if self.processing_live and not self.monitoring_live:
            self.sig_periodic_update.emit(self.combat_session_data)
    
    def remove_last_session(self):
        '''Removes the current combat session, usually for instances where the session has no damage-related events'''
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
        with QMutexLocker(self.combat_mutex):
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

            elif event == "player_name" or event == "player_name_backup": # This catches the welcome message that includes the player name either at the start of the log, or further down should the player log out and back in
                if self.PLAYER_NAME == "" or self.PLAYER_NAME != data["player_name"]: 
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
        
        check_player = this_session.check_in_char(player, "player")
        if not check_player:
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
            if self.CONSOLE_VERBOSITY >= 2: 
                print(f'Player hit themselves with {data["ability"]}. Ignoring')
            return

        # Determine the ability and caster based on pet status
        this_ability = data["ability"]
        target = data["target"]

        if pet:
            if is_pseudopet(data["pet_name"]):
                caster = self.PLAYER_NAME
            else:
                caster = data["pet_name"]
        else:
            caster = self.PLAYER_NAME

       

        # Check and update the session's char and target lists
        this_session = self.combat_session_data[-1]
        check_caster = this_session.check_in_char(caster, "pet" if pet else "player")
        check_target = this_session.check_in_char(target, "enemy")

        if not(check_caster):
            if self.CONSOLE_VERBOSITY >= 2:
                print(f"     Added Character: {caster} to Session: {self.session_count} via Hit Roll Event")
        
        if not(check_target):
            if self.CONSOLE_VERBOSITY >= 2:
                print(f"     Added Target: {target} to Session: {self.session_count} via Hit Roll Event")

        caster = this_session.chars[caster]
        target = this_session.targets[target]

        # Add the ability information to each character's ability list
        for char in [caster, target]:
            if this_ability not in char.abilities:
                char.abilities[this_ability] = Ability(this_ability)
                if self.CONSOLE_VERBOSITY >= 3:
                    print(f"     Added Ability: {this_ability} to Character: {char.get_name()} via Hit Roll Event")

            # Ability activation for the pet
            char_ability = char.abilities[this_ability]
            if char.get_type() == "pet": char_ability.ability_used() # We don't have power activation events for pets, so we'll use the hit roll as a proxy for ability usage
            char_ability.ability_hit(data["outcome"] == "HIT")

        # When associating procs and ability hits successfully, increment parent_hits for all proc damage components
        # Only do this for the caster's ability, not the target's (to avoid double-counting)
        if self.associating_procs and data["outcome"] == "HIT":
            caster_ability = caster.abilities[this_ability]
            for damage_component in caster_ability.damage:
                if damage_component.is_proc:
                    damage_component.increment_parent_hits()

        # Update the caster's last_ability to ensure procs are associated correctly
        # This is especially important for non-damaging abilities (debuffs, buffs, etc.)
        caster.last_ability = caster.abilities[this_ability]



    def handle_event_player_damage(self, data, pet=False):
        '''Handles a player damage event found by the interpret_event function.
        This function will also handle damage from procs and either handle them as separate or associate them with the last used ability depending on the settings.'''
        
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
        target = data["target"]

        this_session = self.combat_session_data[-1]

        if flair != "":
            type = (data["damage_type"] + " (" + data["damage_flair"] + ")")
        else:
            type = data["damage_type"]

        if pet:
            if is_pseudopet(data["pet_name"]):
                caster = self.PLAYER_NAME
            else:
                caster = data["pet_name"]
        else:
            caster = self.PLAYER_NAME


        # Check caster and target into the session
        check_caster = this_session.check_in_char(caster, "pet" if pet else "player")
        check_target = this_session.check_in_char(target, "enemy")

        if not check_caster:
            if self.CONSOLE_VERBOSITY >= 3: print("     Added New Character: ", this_session.chars[caster].get_name(), " to Session: ", self.session_count, ' via Damage Event')

        if not check_target:
            if self.CONSOLE_VERBOSITY >= 3: print("     Added New Target: ", this_session.targets[target].get_name(), " to Session: ", self.session_count, ' via Damage Event')

        # Track first enemy damaged for session naming (only if damage > 0)
        target_name = data["target"]
        if damage > 0:
            this_session.set_first_enemy_damaged(target_name)

            # Update session name if using enemy-based naming and no custom name is set
            if self.user_session_name == "":
                if self.COMBAT_SESSION_NAMING_MODE in ["First Enemy Damaged", "Highest Enemy Damaged"]:
                    # Get the current base name from the session
                    new_base_name = self.get_session_base_name(this_session)

                    # Only update if we now have enemy data (transitioning from fallback)
                    if new_base_name is not None and new_base_name != self.COMBAT_SESSION_NAME:
                        current_name = this_session.get_name()
                        # Check if current name is using the fallback (starts with default session name)
                        if current_name.startswith(self.COMBAT_SESSION_NAME + " "):
                            new_name = self.generate_session_name(this_session)
                            this_session.set_name(new_name)
                            if self.CONSOLE_VERBOSITY >= 3:
                                print(f"     Session renamed from '{current_name}' to '{new_name}'")

        caster = this_session.chars[caster]
        target = this_session.targets[target]

        if proc:
            if flair != "":
                proc_name = (data["ability"] + " (" + data["damage_flair"] + ")")
            else:
                proc_name = data["ability"]

            if caster.last_ability is not None and self.associating_procs: # We'll check and process procs first
                # Check if this proc damage component already exists
                existing_proc = None
                for component in caster.last_ability.damage:
                    if component.type == proc_name:
                        existing_proc = component
                        break

                if existing_proc is None:
                    # First time this proc fires - create new component and initialize parent_hits
                    proc_component = DamageComponent(proc_name, is_proc=True)
                    proc_component.parent_hits = caster.last_ability.get_hits()
                    caster.last_ability.add_damage(proc_component, damage)
                else:
                    # Proc already exists - just add damage
                    caster.last_ability.add_damage(DamageComponent(proc_name, is_proc=True), damage)

                if target.last_ability is not None:
                    # Check if this proc damage component already exists for target
                    existing_target_proc = None
                    for component in target.last_ability.damage:
                        if component.type == proc_name:
                            existing_target_proc = component
                            break

                    if existing_target_proc is None:
                        target_proc_component = DamageComponent(proc_name, is_proc=True)
                        target_proc_component.parent_hits = target.last_ability.get_hits()
                        target.last_ability.add_damage(target_proc_component, damage)
                    else:
                        target.last_ability.add_damage(DamageComponent(proc_name, is_proc=True), damage)
                return
            elif damage == 0:
                if self.CONSOLE_VERBOSITY >= 2: print(f"Ignoring zero-damage proc event: {data['ability']} on {data['target']}")
                return 
            
        
        
        current_char = caster # The loop below will run twice, once for the caster and once for the target, this variable will keep track of which character is being processed

        # Find ability in char list and add damage component, both for caster and the target
        for char in [caster, target]:
            char_ability = this_ability

            if char_ability not in char.abilities:
                char.abilities[char_ability] = Ability(char_ability, proc=proc)
                if self.CONSOLE_VERBOSITY >= 2:
                    print(f"     Added Ability: {char_ability} to Character: {char.get_name()} via Damage Event")

            char_ability = char.get_ability(char_ability)

            caster_ability = caster.get_ability(this_ability)


            char_ability.add_damage(DamageComponent(type), damage)
            if self.CONSOLE_VERBOSITY >= 3: 
                    print ('         Damage Component Added to ', char.get_name(),': ', char_ability.damage[-1].type, char_ability.damage[-1].get_last_damage(), 'Count: ', char_ability.damage[-1].count)

            # Some DoT auras don't have hit rolls recorded in the log when they hit, so we'll put those abilities in a list to treat damage events as successful hits as well
            if not proc and caster_ability.get_hits() == 0:
                    if is_no_hit_ability(char_ability.get_name()):
                        self.no_hitroll_ability_list[char_ability] = False # This ability is auto-hit and should not be included in hit-roll stats
                    else:
                        self.no_hitroll_ability_list[char_ability] = True # This ability is dependent on a hit-roll and should be included in hit-roll stats

            elif proc and char_ability.get_hits() == 0: #This handles incrementing activation counts for procs when associating_procs setting is off
                self.no_hitroll_ability_list[char_ability] = False


            # Finally, check the no_hitroll list and add activation and hit events as needed
            if char_ability in self.no_hitroll_ability_list:
                char_ability.ability_used()
                if self.no_hitroll_ability_list[char_ability]: 
                    char_ability.ability_hit(True)
            
            elif current_char == target and not proc: # This is so power activations that are counted in a separate event can be mapped to the correct ability and enemy target
                char_ability.ability_used()

            char.last_ability = char_ability
            if current_char == caster: current_char = target # Switch to the target for the second loop


  
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
        if data["command"] == "SET_NAME":
            self.user_session_name = data["value"]
            self.last_session_base_name = ""  # Reset to trigger counter reset
            if self.CONSOLE_VERBOSITY >= 2 or self.monitoring_live: print ("          Setting Session Name to: ", self.user_session_name, '\n')
            if self.combat_session_live:
                new_name = self.generate_session_name(self.combat_session_data[-1])
                self.combat_session_data[-1].set_name(new_name)
                if self.monitoring_live: print ("Updated Active Combat Session Name: ", self.combat_session_data[-1].get_name(), '\n')
        elif data["command"] == "START_SESSION":

            if self.combat_session_live:
                print ("    Active session ending from chat command")
                self.end_current_session()
                self.print_session_results(self.combat_session_data[-1])


            if data["value"] != "":
                self.user_session_name = data["value"]
                self.last_session_base_name = ""  # Reset to trigger counter reset

            self.new_session(self.GLOBAL_CURRENT_TIME)

    
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
        '''Calculates the duration of the log file across all combat sessions
        
        :param self: Parser instance
        :return: Duration of the log file in seconds'''
        for session in self.combat_session_data:
            self.global_combat_duration += session.get_duration()

        return self.GLOBAL_CURRENT_TIME - self.GOBAL_START_TIME
    def get_log_dps(self):
        '''
        Get the total DPS across all combat sessions in the log file.
        
        :param self: Parser instance
        :return: Total DPS as a float
        :rtype: float
        '''
        total_damage = 0
        duration = 0
        for session in self.combat_session_data:
            total_damage += session.get_total_damage()
            duration += session.get_duration()
        if duration == 0 or total_damage == 0:
            return 0
        else:
            return total_damage / duration
    
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
            for line in list(file):
                event, data = self.extract_from_line(line)
                if (event == "player_name" or event == "player_name_backup") and isinstance(data, dict):
                    print ('          Player Name Located: ', data["player_name"])
                    return data["player_name"]

        print('          Unable to find Player Name in log file')
        return "Player"
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

        # Only emit sig_finished if not suppressed (used when processing existing then starting live)
        if not getattr(self, 'suppress_finished_signal', False):
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
        '''
        Reads new lines from the log file and processes them in real-time. This then calls the interpret_event function to handle the extracted data.

        :param self: Description
        '''
        try:
            file = self.log_file
            if file is None:
                raise Exception("Cannot read from log file.")
            line = file.readline()
        except Exception as e:
            # Stop the monitoring timer to prevent repeated error attempts
            self.monitoring_timer.stop()
            self.monitoring_live = False

            # Emit error signal for UI to display
            error_message = f"Cannot read from log file: {str(e)}"
            self.sig_error.emit(error_message, "Log File Error")

            if self.CONSOLE_VERBOSITY >= 1:
                print(f"ERROR     {error_message}")
            return
        if not line: return
        event, data = self.extract_from_line(line)
        self.line_count += 1
        if event != "":
            if self.CONSOLE_VERBOSITY == 4: print(event, data)
            self.interpret_event(event, data)
        else:
            event, data = self.extract_datetime_from_line(line)
            if event != "":
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

        with QMutexLocker(self.combat_mutex):
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

                    # Update session name for enemy-based naming modes
                    if self.user_session_name == "":
                        if self.COMBAT_SESSION_NAMING_MODE in ["First Enemy Damaged", "Highest Enemy Damaged"]:
                            new_base_name = self.get_session_base_name(session)
                            current_name = session.get_name()
                            should_update = False

                            # Always transition from fallback to enemy name
                            if new_base_name is not None and new_base_name != self.COMBAT_SESSION_NAME:
                                if current_name.startswith(self.COMBAT_SESSION_NAME + " "):
                                    should_update = True
                                # For "Highest Enemy Damaged" during live monitoring, update when highest changes
                                elif self.COMBAT_SESSION_NAMING_MODE == "Highest Enemy Damaged" and self.monitoring_live:
                                    # Extract current base name (without number suffix)
                                    current_base = " ".join(current_name.split(" ")[:-1])
                                    if current_base != new_base_name:
                                        should_update = True

                            if should_update:
                                new_name = self.generate_session_name(session)
                                session.set_name(new_name)
                                if self.CONSOLE_VERBOSITY >= 3:
                                    print(f"     Session renamed from '{current_name}' to '{new_name}'")

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
        self.COMBAT_SESSION_NAMING_MODE = self.settings.value("CombatSessionNamingMode", Globals.DEFAULT_COMBAT_SESSION_NAMING_MODE, str)

    def on_sig_stop_monitoring(self):
        '''Stops monitoring the log file'''
        self.monitoring_timer.stop()
        print('          Monitoring Ended.')
        if self.combat_session_live: self.end_current_session()
        self.monitoring_live = False
        self.processing_live = False
        self.sig_finished.emit(self.combat_session_data)