class Dungeon:
    pass


class Room:
    def __init__(self):
        self.coordinates = Coordinates(0, 0)
        self.north = None
        self.east = None
        self.south = None
        self.west = None

    def build_north(self, room: Room):
        new_coordinates = Coordinates(self.coordinates.x, self.coordinates.y+1)
        self.north = room
        room.south = self
        room.coordinates = new_coordinates


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
