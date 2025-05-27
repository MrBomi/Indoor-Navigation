from shapely.geometry import Point



class Door:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
        self.name = ""

    def setName(self, name):
        self.name = name
    
    def getName(self):
        return self.name
    
    def to_dict(self):
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "name": self.name
        }
    
    def __repr__(self):
        return f"Door(id={self.id}, x={self.x}, y={self.y}, name='{self.name}')"

    def getId(self):
        return self.id
    
    def getCoordinates(self):
        return (self.x, self.y)

    def getPoint(self):
        return Point(self.x, self.y)