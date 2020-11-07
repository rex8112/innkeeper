"""
Adventure Wrapper
"""

__title__ = 'adventure'
__author__ = 'rex8112'
__copyright__ = 'Copyright 2019-2020 rex8112'
__version__ = '0.2.0'

import logging

from .character_class import CharacterClass
from .characters import Enemy, Player, RaidBoss, test_players
from .colour import Colour
from .data import TestData
from .database import db
from .dungeons import Dungeon
from .encounter import Encounter
from .equipment import BaseEquipment, Equipment
from .exceptions import *
from .formatting import Formatting
from .modifiers import EliteModifier, Modifier
from .quests import Quest
from .race import Race
from .raid import Raid
from .server import Server
from .shop import Shop
from .skills import Skill
from .statusEffects import StatusEffect
from .storage import Storage
from .trade import Trade

try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())
