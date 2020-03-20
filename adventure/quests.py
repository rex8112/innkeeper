import datetime
import random
import logging

from .characters import Player, Enemy
from .equipment import Equipment
from .encounter import Encounter
from .database import db

logger = logging.getLogger('quests')
logger.setLevel(logging.INFO)
handler = logging.FileHandler(filename='bot.log', encoding='utf-8')
handler.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
handler2 = logging.FileHandler(
    filename='latest.log', encoding='utf-8', mode='a')
handler2.setFormatter(logging.Formatter(
    '%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
logger.addHandler(handler2)

class Quest:
    stageTime = 10  # Time it takes for each stage, in seconds

    def __init__(self, dID=0):
        self.id = dID
        self.combat_log = []

    def new(self, aID: int, difficulty: int):
        self.adv = Player(aID)
        self.adv.available = False
        self.adv.save()
        self.stage = 1
        self.active = True
        self.xp = 0
        self.calculateTime(Quest.stageTime)
        self.stages = difficulty

        self.enemies = []
        for i in range(1, self.stages + 1):
            if i > 6:
                bossToAdd = Enemy()
                bossToAdd.generate_new_elite(self.adv.level + 1)
            elif i > 2:
                bossToAdd = Enemy()
                bossToAdd.generate_new_elite(self.adv.level)
            else:
                bossToAdd = None

            if bossToAdd:
                stageEnemies = [bossToAdd.save()]
            else:
                stageEnemies = []

            randMax = random.randint(1, 3)
            for _ in range(1, randMax + 1):
                enemy = Enemy()
                enemy.generate_new(self.adv.level)
                stageEnemies.append(enemy.save())

            self.enemies.append(stageEnemies)

        self.loot = []
        self.lootInt = difficulty // 2

        try:
            for _ in range(1, self.lootInt + 1):
                loot = Equipment(0)
                loot.generate_new(self.adv.level, Equipment.calculate_drop_rarity())
                self.loot.append(loot)
        except Exception:
            logger.error('RNG Loot Failed to Load', exc_info=True)

        self.encounter = self.buildEncounter(
            [self.adv], self.enemies[self.stage - 1])

        self.save()

    def save(self):
        loot_tmp = []
        for l in self.loot:
            loot_tmp.append(l.save())
        loot = '/'.join(loot_tmp)
        tmp = []
        for stage in self.enemies:
            tmp.append('/'.join(str(e) for e in stage))
        enemies = ','.join(tmp)
        save = [self.id, self.adv.id, int(self.active), self.stage, self.stages,
                enemies, loot, self.time.strftime('%Y-%m-%d %H:%M:%S'), self.xp, '|'.join(self.combat_log)]
        self.id = db.saveRNG(save)

    def loadActive(self, aID):
        try:
            save = db.getActiveRNG(aID)
            self.loot = []
            if save[6]:
                loot_tmp = save[6].split('/')
            else:
                loot_tmp = []
            for l in loot_tmp:
                loot = Equipment(0)
                loot.load(l)
                self.loot.append(loot)

            self.enemies = []
            tmp = save[5].split(',')
            for stage in tmp:
                self.enemies.append(stage.split('/'))

            self.id = save[0]
            self.adv = Player(save[1])
            self.active = bool(save[2])
            self.stage = save[3]
            self.stages = save[4]
            self.time = datetime.datetime.strptime(
                save[7], '%Y-%m-%d %H:%M:%S')
            self.xp = int(save[8])
            self.combat_log = save[9].split('|')
            self.encounter = self.buildEncounter(
                [self.adv], self.enemies[self.stage - 1])
            return True
        except Exception as e:
            logger.error('Failed to load quest {}\n{}:{}:{}'.format(
                self.id, type(self).__name__, type(e).__name__, e))
            return False

    def calculateTime(self, time: int):
        timeToAdd = datetime.timedelta(days=0, seconds=time)
        self.time = datetime.datetime.now() + timeToAdd
        logger.debug('Time calculated to {}'.format(
            self.time.strftime('%Y-%m-%d %H:%M:%S')))

    def buildEncounter(self, players: list, enemies: list):
        bPlayers = []
        bEnemies = []
        for player in players:
            if player is int:
                tmp = Player(player)
            else:
                tmp = player
                tmp.load()
            bPlayers.append(tmp)

        for enemy in enemies:
            tmp = Enemy(enemy)
            bEnemies.append(tmp)
        return Encounter(bPlayers, bEnemies)

    def nextStage(self):
        info = '**{0}**: {0.health}/{0.maxHealth}'.format(self.adv)
        info += '\n__*Enemies*__'
        for e in self.encounter.enemies:
            info += '\n*Lv {0.level}* **{0.name}**: {0.health}/{0.maxHealth}'.format(e)
        for e in self.encounter.deadEnemies:
            info += '\n*Lv {0.level}* **{0.name}**: {0.health}/{0.maxHealth}'.format(e)
        info += '\n'
        self.combat_log.append(info)
        if self.adv.health > 0:
            self.stage += 1
            self.xp += int(self.encounter.getExp())
            self.loot += self.encounter.getLoot()
            if self.stage > self.stages:
                self.end(True)
            else:
                self.adv.load()
                self.adv.rest()
                self.adv.save()
                self.encounter = self.buildEncounter(
                    [self.adv], self.enemies[self.stage - 1])
                self.calculateTime(Quest.stageTime)
        else:
            self.end(False)

    def end(self, result: bool):
        self.adv.load()
        self.active = False

        if result == True:
            self.adv.available = True
            self.adv.rest()
            self.adv.addXP(self.xp)
            for l in self.loot:
                self.adv.addInv(l.save(database=True))
        else:
            self.adv.available = True  # TEMPORARY UNTIL RECOVERY IS CODED
            self.adv.rest()

        self.adv.save()
        self.save()