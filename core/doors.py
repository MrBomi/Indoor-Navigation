from shapely.geometry import Point



class Door:
    def __init__(self, id, x, y, scale_p):
        self.id = id
        self.x = x
        self.y = y
        self.x_scale = scale_p[0]
        self.y_scale = scale_p[1]
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
    
    def getX(self):
        return self.x
    
    def getY(self):
        return self.y
    
    def getScaledCoordinates(self):
        return (self.x_scale, self.y_scale)
    
    def getCoordinates(self):
        return (self.x, self.y)

    def getPoint(self):
        return Point(self.x, self.y)
    