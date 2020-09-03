from .modifiers import Modifier, Effect

class StatusEffect:
    def __init__(self, id, potency: float):
        self.id = id
        self.potency = potency
        self._max_lifespan = 3
        self.lifespan = self._max_lifespan
        self.full_effect = False
        self.effects = []
        self.round_effects = []

    def add_potency(self, potency):
        if isinstance(potency, (int, float)):
            self.potency += potency
        elif isinstance(potency, StatusEffect):
            self.potency += potency.potency
        if self.potency >= 1:
            self.full_effect = True
            return True
        else:
            self.full_effect = False
            return False

    def process_lifespan(self, round_count = 1):
        if self.lifespan > 0:
            self.lifespan -= round_count
        if self.lifespan <= 0:
            self.lifespan = 0
            return True
        else:
            return False

    def refresh_lifespan(self):
        self.lifespan = self._max_lifespan

    def apply_effects(self, mod_dict: dict):
        for effect in self.effects:
            mod = mod_dict.get(effect.id)
            if mod:
                mod.add_effect(effect)

    def remove_effects(self, mod_dict: dict):
        for effect in self.effects:
            mod = mod_dict.get(effect.id)
            if mod:
                mod.del_effect(effect)

class PassiveEffect:
    pass