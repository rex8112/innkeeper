import discord

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
        self._owner_id = raw_data['ownerID']
        self.type = raw_data['type']

        category_id = raw_data['category']
        announcement_id = raw_data['announcement']
        general_id = raw_data['general']
        action_channels_string = raw_data['command']
        action_channels_id = (int(e) for e in action_channels_string.split('|'))
        adventurer_id = raw_data['adventureRole']
        traveler_id = raw_data['travelRole']

        self.guild = self.bot.get_guild(self.id)
        self.owner = self.guild.owner
        self.category = None
        for c in self.guild.categories:
            if c.id == category_id:
                self.category = c
                break
        self.announcement = self.guild.get_channel(announcement_id)
        self.general = self.guild.get_channel(general_id)
        self.action_channels = []
        for i in action_channels_id:
            c = self.guild.get_channel(i)
            if c:
                self.action_channels.append(c)
        self.adventurer_role = self.guild.get_role(adventurer_id)
        self.traveler_role = self.guild.get_role(traveler_id)

        Server.server_cache[self.id] = self

    def save(self):
        categoryID = self.category.id if self.category else None
        announcementID = self.announcement.id if self.announcement else None
        generalID = self.general.id if self.general else None
        command_string = '|'.join(str(x.id) for x in self.action_channels)
        adventureRole = self.adventurer_role.id if self.adventurer_role else None
        travelRole = self.traveler_role if self.traveler_role else None

        db.update_server(
            ID=self.id,
            name=self.name,
            ownerID=self.owner.id,
            type_=self.type,
            categoryID=categoryID,
            announcementID=announcementID,
            generalID=generalID,
            commandID=command_string,
            adventureRole=adventureRole,
            travelRole=travelRole
        )

    def new(self, type_of_server='continent'):
        self.guild = self.bot.get_guild(self.id)
        self.owner = self.guild.owner
        self.type = type_of_server

        db.add_server(
            ID=self.id,
            name=self.name,
            ownerID=self.owner.id,
            type_=self.type
        )
        self.load()

    async def build_category(self):
        self.category = await self.guild.create_category(name='The Inn', reason='Constructing the Inn')

    async def delete_category(self, recursive=True):
        if recursive:
            for c in self.category.channels:
                if c == self.announcement:
                    self.announcement = None
                elif c == self.general:
                    self.general = None
                elif c in self.action_channels:
                    self.action_channels.remove(c)
                await c.delete()
        await self.category.delete()
        self.category = None

    async def build_announcement_channel(self):
        announcePerms = {
            self.guild.default_role: discord.PermissionOverwrite(send_messages=False),
            self.guild.me: discord.PermissionOverwrite(send_messages=True)
        }
        self.announcement = await self.category.create_text_channel(
            name='notice_board',
            overwrites=announcePerms,
            topic='Announcement channel for The Innkeeper',
            reason='Constructing the Inn'
        )

    async def delete_announcement_channel(self):
        await self.announcement.delete()
        self.announcement = None

    async def build_general_channel(self):
        self.general = await self.category.create_text_channel(
            name='the_tavern',
            topic='General discussion focused around The Innkeeper',
            reason='Constructing the Inn'
        )

    async def delete_general_channel(self):
        await self.general.delete()
        self.general = None