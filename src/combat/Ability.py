from  PyQt5.QtCore import QObject

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
        return sum  # Return raw value, rounding should only happen at display layer
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
        '''Divides total damage by the number of hits to get the average damage for the ability.
        Will fall back to using the count if no hits are recorded, and return 0 if no damage or activations have been recorded.'''
        average = 0
        count = self.hits if self.count == 0 else self.count
        total = self.get_total_damage()
        if  count == 0 or total == 0:
            return 0
        average = total / count

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