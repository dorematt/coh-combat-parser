from PyQt5.QtCore import QObject
class DamageComponent(QObject):
    '''Stores data about a damage component'''
    def __init__(self, type="", value : float = 0, is_proc=False):
        super().__init__()
        self.count = 0
        self.type = type
        self.name = type
        self.total_damage = value
        self.highest_damage = 0
        self.lowest_damage = 0
        self.last_damage = 0
        self.is_proc = is_proc  # True if this damage component is from a proc
        self.parent_hits = 0  # Track parent ability hits for proc rate calculation
    
    def add_damage(self, type, value : float):
        '''Adds damage value to the damage component'''
        self.count += 1
        self.total_damage += value
        # Don't round here - keep full precision for internal calculations
        self.last_damage = value
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
    def get_last_damage(self):
        '''Returns the last damage for the damage component'''
        return self.last_damage
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

    def increment_parent_hits(self):
        '''Increments the parent ability hit count (used for proc rate calculation)'''
        self.parent_hits += 1

    def get_proc_rate(self):
        '''Returns the proc rate as a percentage (proc activations / parent hits * 100)'''
        if not self.is_proc or self.parent_hits == 0:
            return 0
        return round((self.count / self.parent_hits) * 100, 0)
    