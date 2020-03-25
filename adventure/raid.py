import random

from .characters import RaidBoss
from .equipment import Equipment
from .encounter import Encounter
from .database import db

class Raid():
    def __init__(self, players, boss = 0):
        self.id = 0
        self.boss = None
        self.players = []
        self.loot = []
        if boss == 0:
            pass
        else:
            self.new(players, boss)
    
    def new(self, players, boss):
        self.boss = RaidBoss(boss)
        if self.boss.loaded == False:
            return False
        self.players = players
        
        player_ids = []
        count = 0
        total = 0
        for player in self.players:
            count += 1
            total += player.level
            player_ids.append(str(player.id))
        average = round(total / count)

        if average > self.boss.level + 5:
            level = self.boss.level + 5
        elif average > self.boss.level:
            level = average
        else:
            level = self.boss.level

        self.loot = []
        loot_ids = []
        for _ in range(5):
            base_loot = random.choice(self.boss.inventory)
            loot = Equipment(0)
            loot.generate_new(level, Equipment.calculate_drop_rarity(), base_loot)
            self.loot.append(loot)
            loot_ids.append(loot.save())
        
        self.id = db.add_raid(','.join(player_ids), self.boss.id, '/'.join(loot_ids))

    def build_encounter(self):
        self.encounter = Encounter(self.players, [self.boss])

    def finish_encounter(self, win: bool):
        totalXP = self.encounter.getExp() * 2 # Temporary
        for p in self.players:
            if win:
                p.addXP(totalXP)
            p.rest() # TEMPORARY UNTIL RECOVERY CODED
            p.save()