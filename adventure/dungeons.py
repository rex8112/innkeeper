import discord
import random

from .colour import Colour

class Coordinates:
    def __init__(self, x: int, y: int):
        self.row = x
        self.column = y

    def __eq__(self, other):
        if isinstance(other, Coordinates):
            return self.row == other.x and self.column == other.y
        elif isinstance(other, (tuple, list)):
            return self.row == other[0] and self.column == other[1]
        else:
            return NotImplemented

    def __iter__(self):
        for i in [self.row, self.column]:
            yield i

    def add_x(self, value: int):
        self.row += value
        return self.row

    def add_y(self, value: int):
        self.column += value
        return self.column

    def get_direction(self, direction: str):
        if direction == 'north':
            return self.north()
        elif direction == 'east':
            return self.east()
        elif direction == 'south':
            return self.south()
        elif direction == 'west':
            return self.west()

    def north(self, amount = 1):
        return Coordinates(self.row-amount, self.column)

    def east(self, amount = 1):
        return Coordinates(self.row, self.column+amount)

    def south(self, amount = 1):
        return Coordinates(self.row+amount, self.column)

    def west(self, amount = 1):
        return Coordinates(self.row, self.column-amount)


class Room:
    def __init__(self, id: int, coords = Coordinates(0, 0)):
        self.id = id
        self.coordinates = coords
        self.dungeon = None
        self.north = None
        self.east = None
        self.south = None
        self.west = None
        self.visited = False
        self.event = False
        self.description = 'A non-descript room.'
        self.north_description = 'A passage to the North is open./There is a wall to the North.'
        self.east_description = 'A passage to the East is open./There is a wall to the East.'
        self.south_description = 'A passage to the South is open./There is a wall to the South.'
        self.west_description = 'A passage to the West is open./There is a wall to the West.'

    def set_description(self, description):
        self.description = description

    def get_description(self):
        description = f'{self.description}\n\n'
        north = self.north_description.split('/')
        if self.north:
            description += f'{north[0]}\n'
        else:
            description += f'{north[1]}\n'
        east = self.east_description.split('/')
        if self.east:
            description += f'{east[0]}\n'
        else:
            description += f'{east[1]}\n'
        south = self.south_description.split('/')
        if self.south:
            description += f'{south[0]}\n'
        else:
            description += f'{south[1]}\n'
        west = self.west_description.split('/')
        if self.west:
            description += f'{west[0]}\n'
        else:
            description += f'{west[1]}\n'
        return description

    def get_direction(self, direction: str):
        if direction == 'north':
            return self.north
        elif direction == 'east':
            return self.east
        elif direction == 'south':
            return self.south
        elif direction == 'west':
            return self.west

    def set_direction(self, direction: str, new_value):
        if direction == 'north':
            self.north = new_value
        elif direction == 'east':
            self.east = new_value
        elif direction == 'south':
            self.south = new_value
        elif direction == 'west':
            self.west = new_value

    def build_direction(self, direction: str, new_room):
        if direction == 'north':
            self.build_north(new_room)
        elif direction == 'east':
            self.build_east(new_room)
        elif direction == 'south':
            self.build_south(new_room)
        elif direction == 'west':
            self.build_west(new_room)

    def build_north(self, room):
        new_coordinates = self.coordinates.north()
        self.north = room
        room.south = self
        room.coordinates = new_coordinates

    def build_east(self, room):
        new_coordinates = self.coordinates.east()
        self.east = room
        room.west = self
        room.coordinates = new_coordinates

    def build_south(self, room):
        new_coordinates = self.coordinates.south()
        self.south = room
        room.north = self
        room.coordinates = new_coordinates

    def build_west(self, room):
        new_coordinates = self.coordinates.west()
        self.west = room
        room.east = self
        room.coordinates = new_coordinates

    def enter(self):
        if self.visited:
            return None
        else:
            self.visited = True
            return self.event


class Dungeon:
    def __init__(self, players: list):
        self.name = 'Dungeon'
        self.matrix = self.build_matrix()
        self.room_list = []
        self.players = players
        self.actions = {}
        self.current_room = None
        self.starting_room = None
        self.rest_ambush_chance = 0.0
        self.room_id_incrementer = 0

    def build_matrix(self, columns = 21, rows = 21):
        matrix = []
        for _ in range(rows):
            row = []
            for _ in range(columns):
                row.append(None)
            matrix.append(row)
        return matrix

    def get_indexes(self, coords: Coordinates, x_offset = 10, y_offset = 10):
        row = coords.row + x_offset
        column = coords.column + y_offset
        return row, column

    def new_room(self):
        room = Room(self.room_id_incrementer)
        room.dungeon = self
        self.room_id_incrementer += 1
        return room

    def place_room(self, room: Room):
        row, column = self.get_indexes(room.coordinates)
        if not self.matrix[row][column]:
            self.matrix[row][column] = room
            self.room_list.append(room)

    def run_room_gen(self, room: Room, size = 15):
        CONNECT_CHANCE = 0.125
        FIRST_DOOR_CHANCE = 1.0
        SECOND_DOOR_CHANCE = 0.5
        THIRD_DOOR_CHANCE = 0.3
        directions = ['north', 'east', 'south', 'west']
        random.shuffle(directions)
        chances = [FIRST_DOOR_CHANCE, SECOND_DOOR_CHANCE, THIRD_DOOR_CHANCE]
        new_count = 0
        for d in directions:
            if not room.get_direction(d):
                x, y = self.get_indexes(room.coordinates.get_direction(d))
                if x < 0 or x >= len(self.matrix) or y < 0 or y >= len(self.matrix[0]):
                    continue
                if self.matrix[x][y]: #Check if a room already exists here
                    if self.matrix[x][y] == self.starting_room:
                        continue
                    if random.uniform(0.0, 1.0) < CONNECT_CHANCE:
                        room.build_direction(d, self.matrix[x][y])

                elif new_count == 0 and len(self.room_list) < size:
                    new_count += 1
                    new_room = self.new_room()
                    room.build_direction(d, new_room)
                    self.place_room(new_room)
                    self.run_room_gen(new_room, size=size)
                elif new_count >= 1 and random.uniform(0.0, 1.0) < chances[new_count] and room != self.starting_room:
                    new_count += 1
                    new_room = self.new_room()
                    room.build_direction(d, new_room)
                    self.place_room(new_room)
                    self.run_room_gen(new_room, size=size)

    def build_map(self):
        text = ''
        for row in self.matrix:
            first_line = ''
            second_line = ''
            third_line = ''
            for space in row:
                if space:
                    
                    first_line += f' {"||" if space.north else "--"} '
                    second_line += f'{"=" if space.west else "|"}{space.id:02}{"=" if space.east else "|"}'
                    third_line += f' {"||" if space.south else "--"} '
                else:
                    first_line += '    '
                    second_line += '    '
                    third_line += '    '
            text += f'{first_line}\n{second_line}\n{third_line}\n'
        with open(f'maps/dungeonmap.txt', 'w') as f:
            f.write(text)

    def build_dungeon(self, size = 15):
        self.starting_room = self.new_room()
        self.place_room(self.starting_room)
        self.run_room_gen(self.starting_room, size=size)
        self.current_room = self.starting_room

    def move(self, room: Room):
        self.current_room = room
        event = self.current_room.enter()
        return event

    def rest(self):
        if random.uniform(0.0, 1.0) < self.rest_ambush_chance:
            for a in self.players:
                a.rest()

    def build_status(self, embed: discord.Embed):
        available_skills = (
            '`north`\n`east`\n`south`\n`west`\n'
            '`rest`\n'
            '`inventory`\n'
            '`inspect <#>`\n'
            '`refresh`'
        )

        player_string = ''
        for i, player in enumerate(self.players, 1):
            act = self.actions.get(player.id, "")
            if act:
                player_string += f'{i}. {player.name} - **{act}**\n'
            else:
                player_string += f'{i}. {player.name} - \n'

        embed.add_field(name='Available Actions', value=available_skills)
        embed.add_field(name='Player List', value=player_string)

    async def run_turn(self, bot, message: discord.Message):
        channel = message.channel
        update_message = True
        while len(self.actions) < len(self.players):
            if update_message:
                menu_embed = discord.Embed(
                    title=self.name,
                    description=self.current_room.get_description(),
                    colour=Colour.activeColour
                )
                self.build_status(menu_embed)
                await message.edit(embed=menu_embed)
                update_message = False
            v_message = await bot.wait_for(
                'message',
                timeout=300.0,
                check=lambda m: m.author.id in (x.id for x in self.players) and m.channel == message.channel
            )
            action = v_message.content.lower()
            player = next(filter(lambda x: x == v_message.author, self.players))
            if action in ('north', 'east', 'south', 'west', 'rest'): # Action Voting
                self.actions[player.id] = action
                update_message = True
            elif action == 'inventory': # Inventory
                i_embed = discord.Embed(
                    title=f'{player.name}\'s Inventory',
                    colour=Colour.infoColour
                )
                player.fill_inventory_embed(i_embed)
                await channel.send(embed=i_embed)
            elif action.startswith('inspect'): # Inspection
                try:
                    index = int(action.split(' ')[1]) - 1
                except (ValueError, IndexError):
                    continue
                if index < 0 or index >= len(self.players):
                    continue
                target_player = self.players[index]
                embed = message.embeds[0]
                last_inspect = None
                for i, f in enumerate(embed.fields):
                    if f.name == 'Inspection':
                        last_inspect = i
                if last_inspect != None:
                    embed.remove_field(last_inspect)
                status_effects = "\n".join(x.name for x in target_player.status_effects)
                embed.add_field(
                    name='Inspection',
                    value=(
                        f'{target_player.name}\n'
                        f'HP: {target_player.health:4}\n'
                        'Status Effects\n'
                        f'{status_effects}'
                    )
                )
                await message.edit(embed=embed)
            elif action == 'refresh': # Refresh message
                embed = discord.Embed(
                    title='Building Embed',
                    colour=Colour.creationColour
                )
                message = await channel.send(embed=embed)
                update_message = True

        # END OF WHILE LOOP ----------------------------------------------
        action_count = { 
            'north': 0,
            'east': 0,
            'south': 0,
            'west': 0,
            'rest': 0
        }
        for a in self.actions.values():
            action_count[a] += 1
        sorted_actions = sorted(action_count.items(), reverse=True, key=lambda value: value[1])
        action = sorted_actions[0][0]
        if action == 'rest':
            self.rest()
        else:
            new_room = self.current_room.get_direction(action)
            if new_room:
                self.move(new_room)
            else:
                action = ''
        self.actions.clear()
        return action, message

