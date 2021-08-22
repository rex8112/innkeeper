from adventure.tools.json_manager import dumps
import datetime
import random
import logging

from .characters import Player, Enemy
from .equipment import Equipment
from .encounter import Encounter
from .database import Database

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
        if self.id != 0:
            self.load()

    def new(self, aID: int, difficulty: int):
        self.adv = Player(aID)
        self.stage = 1
        self.active = False
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

        #self.save()

    def save(self):
        loot = dumps(self.loot)
        enemies = dumps(self.enemies)
        time = self.time.strftime('%Y-%m-%d %H:%M:%S')
        save = {
            'active': self.active,
            'stage': self.stage,
            'enemies': enemies,
            'loot': loot,
            'xp': self.xp,
            'combatInfo': dumps(self.combat_log)}
        with Database() as db:
            if not self.id: # New Quest
                self.id = db.insert_quest(self.adv.id, self.stages, time, **save)
            else: # Update Quest
                save['adventurer'] = self.adv.id
                save['stages'] = self.stages
                save['time'] = time
                db.update_quest(self.id, **save)
    @classmethod
    def get_active(cls, adv_id):
        c = cls()
        with Database() as db:
            save = db.get_quest(adventurer=adv_id, active=True)
        c.load(save=save)
        return c

    def load(self, save = None) -> bool:
        try:
            if not save:
                with Database() as db:
                    save = db.fetchone(db.get_quest(indx=self.id))
            self.loot = []
            if save[6]:
                loot_tmp = save[6].split('/')
            else:
                loot_tmp = []
            for l in loot_tmp:
                loot = Equipment(l)
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
            logger.debug('Failed to load quest {}\n{}:{}:{}'.format(
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
        info = '**{0}**: {0.health}/{0.max_health}'.format(self.adv)
        info += '\n__*Enemies*__'
        for e in self.encounter.enemies:
            info += '\n*Lv {0.level}* **{0.name}**: {0.health}/{0.max_health}'.format(e)
        info += '\n\n'
        info += self.encounter.log
        self.combat_log.append(info)
        if self.encounter.winner == 1:
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

    def start(self):
        self.adv.available = False
        self.adv.save()
        self.active = True
        self.calculateTime(Quest.stageTime)
        self.save()

    def end(self, result: bool):
        self.adv.load()
        self.active = False

        if result == True:
            self.adv.available = True
            self.adv.rest()
            self.adv.add_xp(self.xp)
            for l in self.loot:
                self.adv.add_item(l)
        else:
            self.adv.available = True  # TEMPORARY UNTIL RECOVERY IS CODED
            self.adv.rest()

        self.adv.save()
        self.save()