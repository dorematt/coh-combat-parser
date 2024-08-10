from  PyQt5.QtCore import QObject

class Character(QObject):
    '''Stores data about a character, this can be the Player, pets or enemies'''
    def __init__(self, name="", type="") -> None:
        super().__init__()
        self.name = name
        self.type = type #player, pet, enemy
        self.abilities = {}
        self.is_pet = False
        self.last_ability = None # For the purposes of associating proc to powers

    def add_ability(self, ability_name, ability):
        self.abilities[ability_name] = ability

    def set_type(self, type):
        self.type = type

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
    
    def get_hits(self):
        '''Returns the number of times the character has hit'''
        hits = 0
        if self.abilities == {}: return hits
        for ability in self.abilities:
            hits += self.abilities[ability].get_hits()
        return hits
    
    def get_tries(self):
        '''Returns the number of times the character has been used'''
        tries = 0
        if self.abilities == {}: return tries
        for ability in self.abilities:
            tries += self.abilities[ability].get_tries()
        return tries
    
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
    
    def get_type(self):
        return self.type