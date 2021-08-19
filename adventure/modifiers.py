import math

from .database import Database

class Effect:
    def __init__(self, group: str , modifier_id: str, value: float, effect_type = 0):
        self.group = group
        self.modifier_id = modifier_id
        self.effect_type = effect_type # 0 = Additive, 1 = Multiplicative
        self.value = value

    @classmethod
    def from_dict(cls, json_data):
        return cls(
            json_data['group'],
            json_data['modifier_id'],
            json_data['value'],
            json_data['effect_type']
        )

    def serialize(self):
        return {
            'group': self.group,
            'modifier_id': self.modifier_id,
            'effect_type': self.effect_type,
            'value': self.value
        }

    def get_modification(self):
        return Modifier(self.modifier_id, self.value)

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
            return Modifier(self.id, new_value, self.effects)
        elif isinstance(other, (int, float)):
            new_value = self.value + other
            return Modifier(self.id, new_value, self.effects)
        else:
            return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Modifier):
            new_value = self.value - other.value
            return Modifier(self.id, new_value, self.effects)
        elif isinstance(other, (int, float)):
            new_value = self.value - other
            return Modifier(self.id, new_value, self.effects)
        else:
            return NotImplemented

    def __mul__(self, other):
        if isinstance(other, Modifier):
            new_value = self.value * other.value
            return Modifier(self.id, new_value, self.effects)
        elif isinstance(other, (int, float)):
            new_value = self.value * other
            return Modifier(self.id, new_value, self.effects)
        else:
            return NotImplemented

    def __truediv__(self, other):
        if isinstance(other, Modifier):
            new_value = self.value / other.value
            return Modifier(self.id, new_value, self.effects)
        elif isinstance(other, (int, float)):
            new_value = self.value / other
            return Modifier(self.id, new_value, self.effects)
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
        return int(self.get_total())

    def __float__(self):
        return float(self.get_total())

    def __str__(self):
        return str(self.display_name)


    def __init__(self, ID: str, value = None, effects = []):
        self.id = ID
        self.default_value = 0
        self.effects = {}
        for e in effects:
            self.add_effect(e)
        if value == None:
            self.value = None
        elif isinstance(value, (int, float)):
            self.value = value
        else:
            raise ValueError('Incorrect Value Type Passed')
        self.load()

    @classmethod
    def from_dict(cls, json_data):
        id = json_data['id']
        value = json_data['value']
        raw_effects = json_data['effects']
        effects = []
        for e in raw_effects:
            effects.append(Effect.from_dict(e))
        return cls(id, value, effects)

    def serialize(self):
        return {
            'id': self.id,
            'value': self.value,
            'effects': self.effects
        }

    def get_total(self):
        additive = []
        multiplicative = []
        for e in self.effects.values():
            if e.effect_type == 0:
                additive.append(e.value)
            elif e.effect_type == 1:
                multiplicative.append(e.value)
        return (self.value + sum(additive)) * (sum(multiplicative) + 1)

    def add_effect(self, effect: Effect):
        if not isinstance(effect, Effect):
            raise ValueError('Must be an Effect')
        if effect.modifier_id == self.id:
            self.effects[effect.group] = effect

    def del_effect(self, effect: Effect):
        if not isinstance(effect, Effect):
            raise ValueError('Must be an Effect')
        if effect.modifier_id == self.id:
            del self.effects[effect.group]

    def clear_effects(self):
        self.effects.clear()

    def load(self):
        with Database() as db:
            data = db.get_modifier(id=self.id)
            if data:
                data = data[0]
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
            if data['defaultValue']:
                self.default_value = data['defaultValue']
        else:
            self.display_name = self.id
            self.title = None
            self.description = None
        if self.value == None:
            self.value = self.default_value

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