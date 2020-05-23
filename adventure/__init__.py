"""
Adventure Wrapper
"""

__title__ = 'adventure'
__author__ = 'rex8112'
__copyright__ = 'Copyright 2019-2020 rex8112'
__version__ = '0.2.0'

import logging

from .characters import Player, Enemy, RaidBoss
from .colour import Colour
from .encounter import Encounter
from .equipment import Equipment, BaseEquipment
from .exceptions import *
from .quests import Quest
from .raid import Raid
from .modifiers import Modifier, EliteModifier
from .shop import Shop
from .skills import Skill
from .database import db
from .data import TestData

try:
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.getLogger(__name__).addHandler(NullHandler())