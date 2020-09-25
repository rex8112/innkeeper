from .modifiers import Modifier, Effect

class StatusEffect:
    def __init__(self, id, potency: float):
        self.id = id
        self.name = ''
        self.potency = potency
        self._max_lifespan = 3
        self.effects = []
        self.round_effects = []
        if self.potency >= 1:
            self.full_effect = True
        else:
            self.full_effect = False
        self.load()
        self.lifespan = self._max_lifespan

    def add_potency(self, potency):
        if isinstance(potency, (int, float)):
            self.potency += potency
        elif isinstance(potency, StatusEffect):
            self.potency += potency.potency
        if self.potency >= 1:
            self.potency = 1.0
            self.refresh_lifespan()
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

    def add_effect(self, effect_id: str, value, effect_type=0):
        e = Effect(self.id, effect_id, value, effect_type)
        self.effects.append(e)

    def add_round_effect(self, effect_id: str, value, effect_type=0):
        e = Effect(self.id, effect_id, value, effect_type)
        self.round_effects.append(e)

    def apply_effects(self, mod_dict: dict):
        for effect in self.effects:
            mod = mod_dict.get(effect.modifier_id)
            if mod:
                mod.add_effect(effect)

    def remove_effects(self, mod_dict: dict):
        for effect in self.effects:
            mod = mod_dict.get(effect.modifier_id)
            if mod:
                mod.del_effect(effect)

    def load(self):
        if self.id == 'poison':
            self.name = 'Poison'
            self.add_round_effect('health', -0.05, 1)
            self.add_effect('parmor', -5)

class PassiveEffect:
    pass