from .modifiers import Modifier

class Effect:
    def __init__(self, group: str , modifier_id: str, value: float, effect_type = 0):
        self.group = group
        self.modifier_id = modifier_id
        self.effect_type = effect_type # 0 = Additive, 1 = Multiplicative
        self.value = value

    def get_modification(self):
        return Modifier(self.modifier_id, self.value)

class StatusEffect:
    def __init__(self, id, potency: float):
        self.id = id
        self.potency = potency
        self._max_lifespan = 3
        self.lifespan = self._max_lifespan
        self.effects = []

    def process_lifespan(self, round_count = 1):
        if self.lifespan > 0:
            self.lifespan -= round_count
        if self.lifespan <= 0:
            self.lifespan = 0
            return True
        else:
            return False

    def apply_effects(self, effect_dict: dict):
        effect_dict[self.id] = self.effects[:]

    def remove_effects(self, effect_dict: dict):
        del effect_dict[self.id]

class PersistentEffect:
    pass