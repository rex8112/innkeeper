from .characters import Player
from .equipment import Equipment
from .storage import Storage
from .database import db
from .exceptions import NotFound


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
        self.index = db.add_trade(adv1, adv2)
        self.load(self.index)

    def load(self, id: int):
        data = db.get_trade(0, indx=id)
        if not data:
            raise NotFound('Trade not found')
        self.index = data['indx']
        self.player_1 = Player(data['player1'])
        self.player_2 = Player(data['player2'])
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
        for raw_item in data['inventory1'].split('/'):
            item = Equipment(raw_item)
            self.inventory_1.append(item)

        self.inventory_2.clear()
        for raw_item in data['inventory2'].split('/'):
            item = Equipment(raw_item)
            self.inventory_2.append(item)


    def save(self):
        inventory_1 = '/'.join(self.inventory_1)
        inventory_2 = '/'.join(self.inventory_2)
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