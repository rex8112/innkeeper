import discord
import asyncio

from .colour import Colour
from .data import PerLevel
from .database import db
from .exceptions import NotFound, InvalidGuild

class Server:
    server_cache = {}

    def __init__(self, id, bot, load = True):
        self.id = id
        self.bot = bot
        self.loaded = False
        if load:
            try:
                self.load()
            except NotFound:
                pass

    @staticmethod
    def refresh_cache(bot):
        Server.server_cache.clear()
        raw_data = db.get_all_servers()
        for data in raw_data:
            Server(data['id'], bot)

    @staticmethod
    def get_server(id):
        return Server.server_cache.get(id)

    def load(self):
        raw_data = db.get_server(self.id)
        if not raw_data:
            raise NotFound('Guild does not exist')

        self.name = raw_data['name']
        self._owner_id = raw_data['ownerID']
        self.type = raw_data['type']

        category_id = raw_data['category']
        announcement_id = raw_data['announcement']
        general_id = raw_data['general']
        action_channels_string = raw_data['command']
        if action_channels_string:
            action_channels_id = (int(e) for e in action_channels_string.split('|'))
        else:
            action_channels_id = []
        adventurer_id = raw_data['adventureRole']
        traveler_id = raw_data['travelRole']
        self.on_join = bool(raw_data['onjoin'])

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
        self.initialize_embeds()

        Server.server_cache[self.id] = self
        self.loaded = True

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
            travelRole=travelRole,
            onjoin=int(self.on_join)
        )

    def new(self, type_of_server='continent'):
        self.guild = self.bot.get_guild(self.id)
        self.owner = self.guild.owner
        self.type = type_of_server

        db.add_server(
            ID=self.id,
            name=self.guild.name,
            ownerID=self.owner.id,
            type_=self.type
        )
        self.load()

    async def delete(self, remove_channels = True, remove_roles = True):
        if remove_channels:
            if self.category:
                await self.delete_category(recursive=False)
            if self.announcement:
                await asyncio.sleep(0.26)
                await self.delete_announcement_channel()
            if self.general:
                await asyncio.sleep(0.26)
                await self.delete_general_channel()
            for _ in range(len(self.action_channels)):
                await asyncio.sleep(0.26)
                await self.delete_action_channel()
        
        if remove_roles:
            if self.adventurer_role:
                await asyncio.sleep(0.26)
                await self.delete_adventurer_role()
            if self.traveler_role:
                await asyncio.sleep(0.26)
                await self.delete_traveler_role()
        
        db.del_server(self.id)
        del Server.server_cache[self.id]

    def initialize_embeds(self):
        if len(self.action_channels) > 0:
            action_string = (
                'Head on over to one of the action channels in my Inn and run '
                f'the `{self.bot.CP}begin` command to get started.'
            )
        else:
            action_string = (
                f'Head over to where it is appropriate on {self.guild.name} '
                f'and run the `{self.bot.CP}begin` command to get started.'
            )
        description = (
            'You have set foot upon a continent of vast potential but you can '
            f'not begin your adventure without my help. {action_string}'
        )
        self.on_join_embed = discord.Embed(
            title=f'Welcome to {self.guild.name}, Citizen',
            colour=Colour.infoColour,
            description=description
        )

        self.introduction_embed = discord.Embed(
            title=f'Hello Citizens of {self.guild.name}',
            colour=Colour.infoColour,
            description=(
                'I have been summoned to your continent to bring wealth and glory '
                'to the citizens who call this place home. If you wish to partake '
                'in the adventures that I offer, I will be your gateway.'
            )
        )
        self.introduction_embed.add_field(
            name='How to get started',
            value=(
                'To begin the multi-step process to becoming an adventurer '
                f'head to the appropriate channel and run `{self.bot.CP}begin`'
            )
        )
        self.introduction_embed.add_field(
            name='Current Limitations',
            value=(
                f'Level Cap: **{PerLevel.level_cap}**\n'
                'Low amount of Skills and Equipment\n'
                'No Raids yet'
            )
        )

    async def build_category(self):
        self.category = await self.guild.create_category(name='The Inn', reason='Constructing the Inn')

    def set_category(self, category: discord.CategoryChannel):
        if category.guild == self.guild:
            self.category = category
        else:
            raise InvalidGuild('Can not set the category unless it is in your guild')

    async def delete_category(self, recursive=True, reason='Cleaning up my mess before I go'):
        if recursive:
            for c in self.category.channels:
                if c == self.announcement:
                    self.announcement = None
                elif c == self.general:
                    self.general = None
                elif c in self.action_channels:
                    self.action_channels.remove(c)
                await c.delete()
        await self.category.delete(reason=reason)
        self.category = None

    async def build_announcement_channel(self):
        if not self.category:
            raise NotFound('Category not found')
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

    def set_announcement_channel(self, announcement: discord.TextChannel):
        if announcement.guild == self.guild:
            self.announcement = announcement
        else:
            raise InvalidGuild('Can not set the channel unless it is in your guild')

    async def delete_announcement_channel(self, reason='Cleaning up my mess before I go'):
        await self.announcement.delete(reason=reason)
        self.announcement = None

    async def build_general_channel(self):
        if not self.category:
            raise NotFound('Category not found')
        self.general = await self.category.create_text_channel(
            name='the_tavern',
            topic='General discussion focused around The Innkeeper',
            reason='Constructing the Inn'
        )

    def set_general_channel(self, general: discord.TextChannel):
        if general.guild == self.guild:
            self.general = general
        else:
            raise InvalidGuild('Can not set the channel unless it is in your guild')

    async def delete_general_channel(self, reason='Cleaning up my mess before I go'):
        await self.general.delete(reason=reason)
        self.general = None

    async def build_action_channel(self):
        if not self.category:
            raise NotFound('Category not found')
        action_channel = await self.category.create_text_channel(
            name=f'actions_{len(self.action_channels)+1}'
        )
        self.action_channels.append(action_channel)

    async def delete_action_channel(self, reason='Cleaning up my mess before I go'):
        try:
            action_channel = self.action_channels.pop()
            await action_channel.delete(reason=reason)
        except IndexError:
            pass
        except discord.NotFound:
            pass

    async def build_adventurer_role(self):
        self.adventurer_role = await self.guild.create_role(
            name='adventurer',
            reason='Constructing the Inn'
        )

    def set_adventurer_role(self, role: discord.Role):
        if role.guild == self.guild:
            self.adventurer_role = role
        else:
            raise InvalidGuild('Can not set the role unless it is in your guild')
    
    async def delete_adventurer_role(self, reason='Cleaning up my mess before I go'):
        await self.adventurer_role.delete(reason=reason)
        self.adventurer_role = None

    async def build_traveler_role(self):
        self.traveler_role = await self.guild.create_role(
            name='traveler',
            reason='Constructing the Inn'
        )

    def set_traveler_role(self, role: discord.Role):
        if role.guild == self.guild:
            self.traveler_role = role
        else:
            raise InvalidGuild('Can not set the role unless it is in your guild')
    
    async def delete_traveler_role(self, reason='Cleaning up my mess before I go'):
        await self.traveler_role.delete()
        self.traveler_role = None