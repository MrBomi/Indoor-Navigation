import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from pyarrow import nulls
from pydantic.fields import defaultdict
#import configLoader as cl
from engine.app import App
import configLoader as cl
import ManageBuilding as mb
import server.DataBaseManger.buildingManger as b_db_manger

class mangerBuldings:
    def __init__(self):
        self.buildings = defaultdict()
        self.buildingsNumber = 0

    def addBuilding(self, yaml_path, dwg_path, buildingID):
        config = cl.Config(yaml_path)
        app = App(config, dwg_path)
        self.buildings[buildingID] = app.run()
        svg = self.buildings[buildingID].getSvgString()
        graph = self.buildings[buildingID].getGraph()
        doors = self.buildings[buildingID].getDoorsData()
        x_min = self.buildings[buildingID].getXMinRaw()
        x_max = self.buildings[buildingID].getXMaxRaw()
        y_min = self.buildings[buildingID].getYMinRaw()
        y_max = self.buildings[buildingID].getYMaxRaw()
        b_db_manger.add_building(buildingID, svg, graph, doors, x_min, x_max, y_min, y_max)
        
        self.buildingsNumber += 1

    def getBuildings(self):
        return self.buildings

    def getBuilding(self, buildingID):
        if buildingID in self.buildings:
            return self.buildings[buildingID]
        else:
            return None
    


