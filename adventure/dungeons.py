import random

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
        self.north = None
        self.east = None
        self.south = None
        self.west = None
        self.description = 'A non-descript room.'

    def set_description(self, description):
        self.description = description

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


class Dungeon:
    def __init__(self):
        self.matrix = self.build_matrix()
        self.room_list = []
        self.adventurers = []
        self.current_room = None
        self.starting_room = None
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
        self.room_id_incrementer += 1
        return room

    def place_room(self, room: Room):
        row, column = self.get_indexes(room.coordinates)
        if not self.matrix[row][column]:
            self.matrix[row][column] = room
            self.room_list.append(room)

    def run_room_gen(self, room: Room):
        SIZE = 15
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

                elif new_count == 0 and len(self.room_list) < SIZE:
                    new_count += 1
                    new_room = self.new_room()
                    room.build_direction(d, new_room)
                    self.place_room(new_room)
                    self.run_room_gen(new_room)
                elif new_count >= 1 and random.uniform(0.0, 1.0) < chances[new_count] and room != self.starting_room:
                    new_count += 1
                    new_room = self.new_room()
                    room.build_direction(d, new_room)
                    self.place_room(new_room)
                    self.run_room_gen(new_room)

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

    def build_dungeon(self):
        self.starting_room = self.new_room()
        self.place_room(self.starting_room)
        self.run_room_gen(self.starting_room)
