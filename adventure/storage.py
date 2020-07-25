import logging

from .database import db
from .characters import Player
from .equipment import Equipment


logger = logging.getLogger('storage')
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


class Storage():
    def __init__(self, adv_id):
        self.loaded = False
        self.owner = Player(adv_id)
        self.slots = 20
        self.inventory = []
        if not self.load():
            self.new()
        
    def new(self):
        self.loaded = True
        logger.debug(f'{str(self.owner)}\'s Storage Initialized')
        return db.add_storage(self.owner.id)

    def load(self):
        raw_data = db.get_storage(self.owner.id)
        if raw_data:
            self.inventory = []
            self.slots = raw_data['slots']
            raw_inventory = raw_data['inventory'].split('/')
            for i in raw_inventory:
                self.inventory.append(Equipment(i))
            self.loaded = True
            logger.debug(f'{str(self.owner)}\'s Storage Loaded')
            return True
        else:
            logger.debug(f'{str(self.owner)}\'s Storage Failed to Load')
            return False

    def save(self):
        raw_inventory = []
        for i in self.inventory:
            raw_inventory.append(i.save())
        if not self.loaded:
            self.new()
        db.update_storage(self.owner.id, self.slots, '/'.join(raw_inventory))
        logger.debug(f'{str(self.owner)}\'s Storage Saved')

    def delete(self):
        for i in self.inventory:
            i.delete()
        db.delete_storage(self.owner.id)

    def add_item(self, item, force = False):
        if not isinstance(item, Equipment):
            raise ValueError(f'item must be of type {type(Equipment).__name__}')
        if len(self.inventory) >= self.slots and force == False:
            return False
        else:
            self.inventory.append(item)
            return True
    
    def remove_item(self, index, force = False):
        item = self.inventory[index]
        self.inventory.pop(index)
        return item