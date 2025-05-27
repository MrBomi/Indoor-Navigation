import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pyarrow import nulls
from pydantic.fields import defaultdict
#import configLoader as cl
from app import App
import configLoader as cl

class mangerBuldings:
    def __init__(self):
        self.buildings = defaultdict()
        self.buildingsNumber = 0

    def addBuilding(self, yaml_path, dwg_path, buildingID):
        config = cl.Config(yaml_path)
        app = App(config, dwg_path)
        self.buildings[buildingID] = app.run()

    def getBuildings(self):
        return self.buildings

    def getBuilding(self, buildingID):
        if buildingID in self.buildings:
            return self.buildings[buildingID]
        else:
            return None

