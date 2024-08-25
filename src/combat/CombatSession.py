from  PyQt5.QtCore import QObject
from combat.Character import Character
from PyQt5.QtCore import QSettings
from data.Globals import Globals
from datetime import datetime
import time
class CombatSession(QObject):
    '''The CombatSession class stores data about a combat session, which is a period where damage events are registered.
    CombatSessions will automatically end based on the COMBAT_SESSION_TIMEOUT value to avoid including long downtime periods in the data.
    
    The assumption is that this class will be under a mutex lock when it is being accessed.''' 
    def __init__(self, timestamp=0, name="", count=0, override=False):
        super().__init__()
        self.start_time = timestamp
        self.end_time = timestamp
        self.duration = 0 # Seconds
        self.chars = {} # Stores player and any pets involved in the session
        self.targets = {} # Stores a list of targets hit in the sesison
        self.chars_count = 0
        self.targets_count = 0
        self.exp_value = 0
        self.inf_value = 0
        self.name = name
        self.name_count = count
        self.name_override = override # Set to true if a name override is used via command, this ensures the name is not updated by other means

        self.settings = QSettings(Globals.AUTHOR, Globals.APPLICATION_NAME)
        self.name_type = self.settings.value("DefaultSessionNaming", Globals.DEFAULT_COMBAT_SESSION_OPTION, int)


    def end_time(self):
        return self.end_time

    def set_start_time(self, start_time):
        self.start_time = start_time
        if self.name_type == 2 and not self.name_override: #Update sesison name if we're using start time
            self.name = datetime.strftime("%H:%M:%S", time.localtime(start_time))

    def set_end_time(self, end_time):
        self.end_time = end_time
        self.update_duration()

    def set_name(self, name, count=0):
        self.name = name
        self.name_count = count

    def set_name_override(self, override):
        self.name_override = override

    def update_duration(self):
        self.duration = self.end_time - self.start_time

    def update_session_time(self, timestamp, in_combat = True):
        
        if in_combat:
            self.set_end_time(timestamp)

    def has_no_damage(self):
        '''Returns True if the session has no damage registered'''
        return self.get_total_damage() == 0
    

    def get_name(self):
        '''Returns the name of the session with appended count where necessary'''
        if self.name_count > 1 and self.name_type != 2 and not self.name_override:
            return self.name + " " + str(self.name_count)
        return self.name
    
    def get_duration(self):
        self.update_duration()
        return self.duration
    
    def get_total_damage(self):
        '''Calculates the total damage for the session'''
        sum = 0
        for char in self.chars:
            sum += self.chars[char].get_total_damage()
        return round(sum,2)
    
    def get_count_chars(self):
        '''Returns the number of characters in the session'''
        return self.chars_count
    
    def get_count_targets(self):
        '''Returns the number of targets in the session'''
        return self.targets
    
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
    
    def get_highest_damage_target(self):
        '''Returns the target that took the most damage in the session'''
        highest = 0
        target = ""
        for name in self.targets:
            if self.targets[name].get_total_damage() > highest:
                highest = self.targets[name].get_total_damage()
                target = name
        return target
    
    def add_character(self, character):
        self.chars[character.get_name()] = character
    
    def check_in_char(self, name, type) -> bool:
        '''Checks and adds the character to the session if they are not already in it, Returns True if the character was already in the session'''

        assert type in ["player", "pet", "enemy"], "Character Type: '" + type + "' is not valid"

        if type == "enemy":
            if name not in self.targets:
                self.targets[name] = Character(name, type)
                self.targets_count += 1
                if self.name_type == 3 and self.targets_count == 1 and not self.name_override: # If we're using first enemy hit as the session name, update the session name
                    self.name = name
                    return False
                return False
            return True
        else:
            if name not in self.chars:
                self.chars[name] = Character(name, type)
                self.chars_count += 1
                return False
            return True
        
    def end_session(self, timestamp=0):
        '''Ends the session and updates the session time one last time if provided'''
        if timestamp != 0: self.set_end_time(timestamp)
        else: self.update_duration()
        if self.name_type == 4 and not self.name_override: #If we're using highest damage enemy as the session name, update the session name
            self.name = self.get_highest_damage_target()
