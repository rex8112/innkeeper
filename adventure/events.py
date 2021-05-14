from discord import Message

from . import dungeons
from .encounter import Encounter

class RoomEvent:
    event_type = 'generic'

    def __init__(self, players = []):
        self.players = players

    async def run(self, message: Message):
        return message

class EnemyEvent(RoomEvent):
    event_type = 'enemy'

    def __init__(self, room: dungeons.Room, enemies: list, ambush = False):
        self.players = room.dungeon.players
        self.enemies = enemies
        self.ambush = ambush

    def generate_new_enemies(self):
        self.encounter = Encounter(self.players, self.enemies)

    async def run(self, message: Message):
        return message