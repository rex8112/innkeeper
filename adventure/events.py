from discord import Message
from .encounter import Encounter

class RoomEvent:
    event_type = 'generic'

    def __init__(self, players = []):
        self.players = players

    def run(self, message: Message):
        pass

class EnemyEvent(RoomEvent):
    event_type = 'enemy'

    def __init__(self, players = [], enemies = [], ambush = False):
        self.players = players
        self.enemies = enemies
        self.ambush = ambush

    def generate_new_enemies(self):
        self.encounter = Encounter(self.players, self.enemies)

    def run(self, message: Message):
        pass