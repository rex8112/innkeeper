from .database import db

class Modifier:
    def __eq__(self, other):
        if isinstance(other, Modifier):
            return self.value == other.value
        elif isinstance(other, (int, float)):
            return self.value == other
        else:
            return NotImplemented

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        if isinstance(other, Modifier):
            return self.value < other.value
        elif isinstance(other, (int, float)):
            return self.value < other
        else:
            return NotImplemented

    def __le__(self, other):
        if isinstance(other, Modifier):
            return self.value <= other.value
        elif isinstance(other, (int, float)):
            return self.value <= other
        else:
            return NotImplemented

    def __gt__(self, other):
        if isinstance(other, Modifier):
            return self.value > other.value
        elif isinstance(other, (int, float)):
            return self.value > other
        else:
            return NotImplemented

    def __ge__(self, other):
        if isinstance(other, Modifier):
            return self.value >= other.value
        elif isinstance(other, (int, float)):
            return self.value >= other
        else:
            return NotImplemented

    def __add__(self, other):
        if isinstance(other, Modifier):
            new_value = self.value + other.value
            return Modifier(self.id, new_value)
        elif isinstance(other, (int, float)):
            new_value = self.value + other
            return Modifier(self.id, new_value)
        else:
            return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Modifier):
            new_value = self.value - other.value
            return Modifier(self.id, new_value)
        elif isinstance(other, (int, float)):
            new_value = self.value - other
            return Modifier(self.id, new_value)
        else:
            return NotImplemented

    def __mul__(self, other):
        if isinstance(other, Modifier):
            new_value = self.value * other.value
            return Modifier(self.id, new_value)
        elif isinstance(other, (int, float)):
            new_value = self.value * other
            return Modifier(self.id, new_value)
        else:
            return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, Modifier):
            new_value = self.value / other.value
            return Modifier(self.id, new_value)
        elif isinstance(other, (int, float)):
            new_value = self.value / other
            return Modifier(self.id, new_value)
        else:
            return NotImplemented

    def __radd__(self, other):
        return self.__add__(other)

    def __rsub__(self, other):
        return self.__sub__(other)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __rtruediv__(self, other):
        return self.__truediv__(other)

    def __iadd__(self, other):
        if isinstance(other, Modifier):
            self.value = self.value + other.value
            return self
        elif isinstance(other, (int, float)):
            self.value = self.value + other
            return self
        else:
            NotImplemented

    def __isub__(self, other):
        if isinstance(other, Modifier):
            self.value = self.value - other.value
            return self
        elif isinstance(other, (int, float)):
            self.value = self.value - other
            return self
        else:
            NotImplemented

    def __imul__(self, other):
        if isinstance(other, Modifier):
            self.value = self.value * other.value
            return self
        elif isinstance(other, (int, float)):
            self.value = self.value * other
            return self
        else:
            NotImplemented

    def __itruediv__(self, other):
        if isinstance(other, Modifier):
            self.value = self.value / other.value
            return self
        elif isinstance(other, (int, float)):
            self.value = self.value / other
            return self
        else:
            NotImplemented
            
    def __int__(self):
        return int(self.value)

    def __float__(self):
        return float(self.value)

    def __str__(self):
        return str(self.display_name)


    def __init__(self, ID: str, value):
        self.id = ID
        if isinstance(value, (int, float)):
            self.value = value
        else:
            raise ValueError('Incorrect Value Type Passed')
        self.load()
    
    def load(self):
        data = db.get_modifier(self.id)
        if data:
            if data['displayName']:
                self.display_name = data['displayName']
            else:
                self.display_name = self.id
            if data['titleName']:
                self.title = data['titleName']
            else:
                self.title = None
            if data['description']:
                self.description = data['description']
            else:
                self.description = None
        else:
            self.display_name = self.id
            self.title = None
            self.description = None


class EliteModifier:
    def __init__(self, ID = 0):
        self.id = ID
        if self.id != 0:
            self.load(self.id)

    def load(self, ID):
        data = db.get_elite_modifier(self.id)
        self.id = int(data[0])
        self.name = str(data[1])
        self.title = str(data[2])
        self.attributes = [float(x) for x in data[3].split('|')]
        self.modifiers = {}
        modifier_string = data[4].split('|')
        for mod in modifier_string:
            key, value = tuple(mod.split(':'))
            self.modifiers[key] = Modifier(key, float(value))
        if data[5]:
            self.skills = data[5].split('|')
        else:
            self.skills = []