from .characters import Player
from .equipment import Equipment
from .storage import Storage
from .database import db
from .exceptions import NotFound, InvalidAdventurer


class Trade:
    def __init__(self):
        self.player_1 = None
        self.player_2 = None
        self.inventory_1 = []
        self.inventory_2 = []
        self.money_1 = 0
        self.money_2 = 0
        self.confirm_1 = False
        self.confirm_2 = False
        self.waiting_on = None
        self.index = 0

    def new(self, adv1: Player, adv2: Player):
        self.index = db.add_trade(adv1.id, adv2.id)
        self.load(self.index)

    def load(self, id: int):
        data = db.get_trade(0, indx=id)
        if not data:
            raise NotFound('Trade not found')
        self.index = data['indx']
        self.player_1 = Player(data['adv1'])
        self.player_2 = Player(data['adv2'])
        self.money_1 = data['money1']
        self.money_2 = data['money2']
        self.confirm_1 = bool(data['confirm1'])
        self.confirm_2 = bool(data['confirm2'])
        self.active = bool(data['active'])

        if data['waitingOn'] == 1:
            self.waiting_on = self.player_1
        else:
            self.waiting_on = self.player_2

        self.inventory_1.clear()
        if data['inventory1']:
            for raw_item in data['inventory1'].split('/'):
                item = Equipment(raw_item)
                self.inventory_1.append(item)

        self.inventory_2.clear()
        if data['inventory2']:
            for raw_item in data['inventory2'].split('/'):
                item = Equipment(raw_item)
                self.inventory_2.append(item)

    def set_confirm(self, adv: Player, value: bool):
        if adv == self.player_1:
            self.confirm_1 = value
        elif adv == self.player_2:
            self.confirm_2 = value
        else:
            raise NotFound('Adventurer not found')

    def toggle_waiting_on(self):
        if self.waiting_on == self.player_1:
            self.waiting_on = self.player_2
        elif self.waiting_on == self.player_2:
            self.waiting_on = self.player_1

    def save(self):
        inventory_1_raw = []
        inventory_2_raw = []
        for i in self.inventory_1:
            inventory_1_raw.append(i.save())
        for i in self.inventory_2:
            inventory_2_raw.append(i.save())
        inventory_1 = '/'.join(inventory_1_raw)
        inventory_2 = '/'.join(inventory_2_raw)
        if self.waiting_on == self.player_1:
            waiting_on = 1
        else:
            waiting_on = 2
        db.update_trade(
            self.money_1,
            self.money_2,
            inventory_1,
            inventory_2,
            int(self.confirm_1),
            int(self.confirm_2),
            waiting_on,
            int(self.active),
            self.index
        )
        self.player_1.save()
        self.player_2.save()

    def add_item(self, adv: Player, index: int):
        if adv == self.player_1:
            if len(self.inventory_1) < 10:
                item = self.player_1.rem_item(index)
                if item:
                    self.inventory_1.append(item)
                return True
            else:
                return False
        elif adv == self.player_2:
            if len(self.inventory_2) < 10:
                item = self.player_2.rem_item(index)
                if item:
                    self.inventory_2.append(item)
                return True
            else:
                return False
        else:
            raise NotFound('Adventurer not found')

    def del_item(self, adv: Player, index: int):
        try:
            if adv == self.player_1:
                item = self.inventory_1.pop(index)
                if not self.player_1.add_item(item):
                    storage = Storage(self.player_1)
                    storage.add_item(item, True)
            elif adv == self.player_2:
                item = self.inventory_2.pop(index)
                if not self.player_2.add_item(item):
                    storage = Storage(self.player_2)
                    storage.add_item(item, True)
            else:
                raise NotFound('Adventurer not found')
        except IndexError:
            return None