from .database import db
from .characters import Player
from .equipment import Equipment


class Storage():
    def __init__(self, adv_id):
        self.owner = Player(adv_id)
        
    def new(self):
        return db.add_storage(self.owner.id)

    def load(self):
        raw_data = db.get_storage(self.owner.id)
        self.inventory = []
        self.slots = raw_data['slots']
        raw_inventory = raw_data['inventory'].split('/')
        for i in raw_inventory:
            self.inventory.append(Equipment(i))

    def save(self):
        raw_inventory = []
        for i in self.inventory:
            raw_inventory.append(i.save())
        db.update_storage(self.owner.id, self.slots, '/'.join(raw_inventory))

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