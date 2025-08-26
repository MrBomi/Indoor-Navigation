import os

from pycurl import UPLOAD
import json
from server.models import Graph, Door, Building, db
#from server.models import Door as DoorModel, db


def save_graph_to_db(building_id: int, graph_dict: dict):
    try:
        #json_graph = json.dumps(graph_dict) 
        json_graph = json.dumps(stringify_graph_keys(graph_dict))
        graph = Graph(building_id=building_id, json_data=json_graph)
        
        existing = Graph.query.filter_by(building_id=building_id).first()
        if existing:
            db.session.delete(existing)

        db.session.add(graph)
        db.session.commit()
        return True
    except Exception as e:
        print(f"Error saving graph to DB: {e}")
        db.session.rollback()
        return False

def stringify_graph_keys(graph_dict):
    return {
        f"{x},{y}": [f"{nx},{ny}" for (nx, ny) in neighbors]
        for (x, y), neighbors in graph_dict.items()
    }

def save_doors_to_db(doors_dict: dict, building_id: int) -> bool:
    try:
        Door.query.filter_by(building_id=building_id).delete()

        for door in doors_dict.values():
            db_door = Door(
                id=door.getId(),
                x=door.getX(),
                y=door.getY(),
                name=door.getName(),
                building_id=building_id
            )
            db.session.add(db_door)

        db.session.commit()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to save doors to DB: {e}")
        db.session.rollback()
        return False

def add_building(building_id: int, svg_data: str, graph_dict: dict, doors_dict: dict, x_min: float, x_max: float, y_min: float, y_max: float) -> bool:
    try:
        existing = Building.query.get(building_id)
        if existing:
            db.session.delete(existing)
            db.session.commit()

        building = Building(id=building_id, svg_data=svg_data, x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)
        db.session.add(building)
        db.session.commit() 

        graph_ok = save_graph_to_db(building_id, graph_dict)
        doors_ok = save_doors_to_db(doors_dict, building_id)

        return graph_ok and doors_ok

    except Exception as e:
        print(f"[ERROR] Failed to add building: {e}")
        db.session.rollback()
        return False



UPLOAD_FOLDER = "static/upload"
def saveInLocal(dwg_file, yaml_file):
    os.makedirs("static/upload", exist_ok=True)
    dwg_path = os.path.join(UPLOAD_FOLDER, dwg_file.filename)
    yaml_path = os.path.join(UPLOAD_FOLDER, yaml_file.filename)
    dwg_file.save(dwg_path)
    yaml_file.save(yaml_path)
    return yaml_path , dwg_path



