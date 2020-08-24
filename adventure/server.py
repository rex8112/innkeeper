from .database import db
from .exceptions import NotFound

class Server:
    server_cache = {}
    def __init__(self, id, bot, load = True):
        self.id = id
        self.bot = bot
        if load:
            self.load()

    @staticmethod
    def refresh_cache(bot):
        Server.server_cache.clear()
        raw_data = db.get_all_servers()
        for data in raw_data:
            Server(data['id'], bot)

    def load(self, use_cache = True):
        if use_cache:
            cache = Server.server_cache.get(self.id, None)
            if cache:
                self = cache
                return

        raw_data = db.get_server(self.id)

        self.name = raw_data['name']
        self.owner_id = raw_data['ownerID']
        self.type = raw_data['type']
        self.category_id = raw_data['category']
        self.announcement_id = raw_data['announcement']
        self.general_id = raw_data['general']
        action_channels_string = raw_data['command']
        self.action_channels_id = (int(e) for e in action_channels_string.split('|'))
        self.adventurer_id = raw_data['adventureRole']
        self.traveler_id = raw_data['travelRole']

        self.guild = self.bot.get_guild(self.id)
        self.owner = self.guild.owner
        self.category = None
        for c in self.guild.categories:
            if c.id == self.category_id:
                self.category = c
                break
        self.announcement = self.guild.get_channel(self.announcement_id)
        self.general = self.guild.get_channel(self.general_id)
        self.action_channels = []
        for i in self.action_channels_id:
            self.action_channels.append(self.guild.get_channel(i))
        self.adventurer_role = self.guild.get_role(self.adventurer_id)
        self.traveler_role = self.guild.get_role(self.traveler_id)

        Server.server_cache[self.id] = self

    def save(self):
        command_string = '|'.join(str(x.id) for x in self.action_channels)
        db.update_server(
            ID=self.id,
            name=self.name,
            ownerID=self.owner.id,
            type_=self.type,
            categoryID=self.category.id,
            announcementID=self.announcement.id,
            generalID=self.general.id,
            commandID=command_string,
            adventureRole=self.adventurer_role.id,
            travelRole=self.traveler_role.id
        )

    def new(self, type_of_server='continent'):
        self.guild = self.bot.get_guild(self.id)
        self.owner = self.guild.owner
        self.type = type_of_server
        self.category_id = None
        self.announcement_id = None
        self.general_id = None
        self.action_channels_id = []
        self.adventurer_id = None
        self.traveler_id = None