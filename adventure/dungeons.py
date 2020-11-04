class Coordinates:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __eq__(self, other):
        if isinstance(other, Coordinates):
            return self.x == other.x and self.y == other.y
        elif isinstance(other, (tuple, list)):
            return self.x == other[0] and self.y == other[1]
        else:
            return NotImplemented

    def __iter__(self):
        for i in [self.x, self.y]:
            yield i

    def add_x(self, value: int):
        self.x += value
        return self.x

    def add_y(self, value: int):
        self.y += value
        return self.y

    def north(self, amount = 1):
        return Coordinates(self.x, self.y+amount)

    def east(self, amount = 1):
        return Coordinates(self.x+amount, self.y)

    def south(self, amount = 1):
        return Coordinates(self.x, self.y-amount)

    def west(self, amount = 1):
        return Coordinates(self.x-amount, self.y)


class Room:
    def __init__(self, id: int, coords = Coordinates(0, 0)):
        self.id = id
        self.coordinates = coords
        self.north = None
        self.east = None
        self.south = None
        self.west = None

    def build_north(self, room: Room):
        new_coordinates = self.coordinates.north()
        self.north = room
        room.south = self
        room.coordinates = new_coordinates

    def build_east(self, room: Room):
        new_coordinates = self.coordinates.east()
        self.east = room
        room.west = self
        room.coordinates = new_coordinates

    def build_south(self, room: Room):
        new_coordinates = self.coordinates.south()
        self.south = room
        room.north = self
        room.coordinates = new_coordinates

    def build_west(self, room: Room):
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
        self.room_id_incrementer = 0

    def build_matrix(self, columns = 21, rows = 21):
        matrix = []
        for _ in range(rows):
            row = []
            for _ in range(columns):
                row.append(None)
            matrix.append(row)
        return matrix

    def get_indexes(self, coords: Coordinates, x_offset = 11, y_offset = 11):
        x = coords.x - x_offset
        y = coords.y - y_offset
        return x, y

    def new_room(self):
        room = Room(self.room_id_incrementer)
        self.room_id_incrementer += 1
        return room

    def place_room(self, room: Room):
        x, y = self.get_indexes(room.coordinates)
        if not self.matrix[x][y]:
            self.matrix[x][y] = room
            self.room_list.append(room)

    def build_dungeon(self):
        pass
    