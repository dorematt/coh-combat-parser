from  PyQt5.QtCore import QObject
from combat.Character import Character
class CombatSession(QObject):
    '''The CombatSession class stores data about a combat session, which is a period where damage events are registered.
    CombatSessions will automatically end based on the COMBAT_SESSION_TIMEOUT value to avoid including long downtime periods in the data.
    
    The assumption is that this class will be under a mutex lock when it is being accessed.''' 
    def __init__(self, timestamp=0, name=""):
        super().__init__()
        self.start_time = timestamp
        self.end_time = timestamp
        self.duration = 0 # Seconds
        self.chars = {} # Stores player and any pets involved in the session
        self.targets = {} # Stores a list of targets hit in the sesison
        self.exp_value = 0
        self.inf_value = 0
        self.name = name
        

    def set_start_time(self, start_time):
        self.start_time = start_time
    def set_end_time(self, end_time):
        self.end_time = end_time
    def set_name(self, name):
        self.name = name
    def update_duration(self):
        self.duration = self.end_time - self.start_time
    def update_session_time(self, timestamp, in_combat = True):
        
        if in_combat:
            self.end_time = timestamp
            self.update_duration()

    def has_no_damage(self):
        '''Returns True if the session has no damage registered'''
        return self.get_total_damage() == 0
    

    def get_name(self):
        return self.name
    def get_duration(self):
        self.update_duration()
        return self.duration
    
    def get_total_damage(self):
        '''Calculates the total damage for the session'''
        sum = 0
        for char in self.chars:
            sum += self.chars[char].get_total_damage()
        return sum  # Return raw value, rounding should only happen at display layer
    
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
    
    def check_in_char(self, name, type) -> bool:
        '''Checks and adds the character to the session if they are not already in it, Returns True if the character was already in the session'''

        assert type in ["player", "pet", "enemy"], "Invalid character type"

        if type == "enemy":
            if name not in self.targets:
                self.targets[name] = Character(name, type)
                return False
            return True
        else:
            if name not in self.chars:
                self.chars[name] = Character(name, type)
                return False
            return True
