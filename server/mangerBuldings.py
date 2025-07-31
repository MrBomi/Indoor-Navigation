import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from collections import defaultdict
import threading

#import configLoader as cl
from core.app import App
from core.ManagerFloor import ManagerFloor
import core.configLoader as cl
import server.DataBaseManger.floorManager as b_db_manger

class mangerBuldings:
    def __init__(self):
        self.buildings = defaultdict()
        self.buildingsNumber = b_db_manger.getNewBuildingId()
        self.lock = threading.Lock()

    def addBuilding(self, yaml_file, dwg_file, buildingID):
        config = cl.Config(yaml_file)
        self.buildings[int(buildingID)] = App(config, dwg_file)
        return self.buildings[int(buildingID)].startProccesCreateNewBuilding()
        svg = self.buildings[buildingID].getSvgStrring()
        graph = self.buildings[buildingID].getGraph()
        doors = self.buildings[buildingID].getDoorsData()
        x_min = self.buildings[buildingID].getXMinRaw()
        x_max = self.buildings[buildingID].getXMaxRaw()
        y_min = self.buildings[buildingID].getYMinRaw()
        y_max = self.buildings[buildingID].getYMaxRaw()
        b_db_manger.add_building(buildingID, svg, graph, doors, x_min, x_max, y_min, y_max)

    def continueAddBuilding(self, buildingID, point1, point2, real_distance_cm):
        building = self.buildings[buildingID].continueAddBuilding(point1, point2, real_distance_cm)
        del self.buildings[buildingID]
        svg = building.getSvgString()
        grid_svg = building.getGridSvgString()
        graph = building.getGraph()
        doors = building.getDoorsData()
        x_min = building.getXMinRaw()
        x_max = building.getXMaxRaw()
        y_min = building.getYMinRaw()
        y_max = building.getYMaxRaw()
        b_db_manger.add_building(str(buildingID), svg, grid_svg, graph, doors, x_min, x_max, y_min, y_max)
        return building.create_door_json()

    def getBuildings(self):
        return self.buildings

    def getBuilding(self, buildingID):
        if buildingID in self.buildings:
            return self.buildings[buildingID]
        else:
            return None
    


