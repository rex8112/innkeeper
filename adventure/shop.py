import datetime

from .equipment import Equipment
from .database import db

class Shop():
    def __init__(self, adv, load=True):
        self.id = 0
        self.adv = adv
        self.adv.load()
        self.inventory = []
        self.buyback = []
        self.refresh = datetime.datetime.now()
        if load:
            self.loadActive()
        else:
            self.new()
            self.save()

    def new(self):
        for _ in range(10):
            equipment = Equipment(0)
            equipment.generate_new(self.adv.level, Equipment.calculate_drop_rarity())
            self.inventory.append(equipment)
        self.refresh = datetime.datetime.now() + datetime.timedelta(hours=12)

    def save(self):
        if len(self.inventory) > 0:
            equipment_string = '/'.join(e.save() for e in self.inventory)
        else:
            equipment_string = None
        if len(self.buyback) > 0:
            buyback_string = '/'.join(e.save() for e in self.buyback)
        else:
            buyback_string = None
        refresh_string = self.refresh.strftime('%Y-%m-%d %H:%M:%S')
        save = [self.id, self.adv.id, equipment_string, buyback_string, refresh_string]
        self.id = db.SaveShop(save)

    def loadActive(self): # Needs to be updated
        save = db.GetActiveShop(self.adv.id)
        if save:
            self.id = save[0]
            tmp = save[2].split('/')
            self.inventory = []
            for e in tmp:
                equip = Equipment(e)
                self.inventory.append(equip)
            self.buyback = []
            try:
                btmp = save[3].split('/')
                for e in btmp:
                    equip = Equipment(e)
                    self.buyback.append(equip)
            except AttributeError:
                pass
            self.refresh = datetime.datetime.strptime(save[4], '%Y-%m-%d %H:%M:%S')
        else:
            self.new()
            self.save()


    def buy(self, index: int): # Index has to be the index in list
        index = int(index)
        equipment = self.inventory[index]
        if len(self.adv.inventory) < self.adv.inventoryCapacity:
            if self.adv.remXP(equipment.price):
                self.adv.addInv(equipment)
                self.inventory.pop(index)
                return True
            else:
                return False
        else:
            return False

    def buyB(self, index: int): # Index has to be the index in list
        index = int(index)
        equipment = self.buyback[index]
        if len(self.adv.inventory) < self.adv.inventoryCapacity:
            save = equipment
            if self.adv.remXP(equipment.price):
                self.adv.addInv(save)
                self.buyback.pop(index)
                return True
            else:
                return False
        else:
            return False

    def sell(self, index: int):
        index = int(index)
        equipment = self.adv.inventory[index]
        if self.adv.remInv(index):
            save = equipment
            self.buyback.append(save)
            self.adv.addXP(equipment.sell_price)
            save.delete()
            return True
        else:
            return False
