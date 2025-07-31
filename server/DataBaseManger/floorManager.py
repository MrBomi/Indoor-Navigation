from server.models import Floor, Building
from server.extensions import db
from server.DataBaseManger.graphManger import save_graph_to_db
from server.DataBaseManger.doorsManger import save_doors_to_db


def add_floor(building_id: int, floor_id: int, svg_data: str, grid_svg: str, graph_dict: dict, doors_dict: dict, x_min: float, x_max: float, y_min: float, y_max: float) -> bool:
    try:
        existing = Floor.query.get((floor_id, building_id))
        if existing:
            db.session.delete(existing)
            db.session.commit()

        floor = Floor(id=floor_id, svg_data=svg_data, grid_svg=grid_svg, x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max, building_id=building_id)
        db.session.add(floor)
        db.session.commit() 

        graph_ok = save_graph_to_db(building_id, floor_id, graph_dict)
        doors_ok = save_doors_to_db(doors_dict, building_id, floor_id)

        return graph_ok and doors_ok

    except Exception as e:
        print(f"[ERROR] Failed to add building: {e}")
        db.session.rollback()
        return False
    
def get_Svg_data(building_id: int, floor_id: int) -> str:
    try:
        floor = Floor.query.get((floor_id, building_id))
        if floor:
            return floor.svg_data
        else:
            raise ValueError(f"Floor with ID {floor_id} in building {building_id} not found.")
    except Exception as e:
        print(f"[ERROR] Failed to retrieve SVG data for floor {floor_id} in building {building_id}: {e}")
        return ""

def get_grid_svg(building_id: int, floor_id: int) -> str:
    try:
        floor = Floor.query.get((floor_id, building_id))
        if floor:
            return floor.grid_svg
        else:
            raise ValueError(f"Floor with ID {floor_id} in building {building_id} not found.")
    except Exception as e:
        print(f"[ERROR] Failed to retrieve grid SVG for floor {floor_id} in building {building_id}: {e}")
        return ""

def get_floor_by_pk(building_id: int, floor_id: int):
    floor = Floor.query.get((floor_id, building_id))
    if not floor:
        raise ValueError(f"Floor with ID {floor_id} in building {building_id} not found.")
    return floor.x_min, floor.x_max, floor.y_min, floor.y_max

def get_all_floor_ids(building_id: int):
    floors = Floor.query.filter_by(building_id=building_id).all()
    return [int(floor.id) for floor in floors]

def update_svg_data(building_id: int, floor_id: int, svg_data: str) -> bool:
    try:
        floor = Floor.query.get((floor_id, building_id))
        if not floor:
            raise ValueError(f"Floor with ID {floor_id} in building {building_id} not found.")
        
        floor.svg_data = svg_data
        db.session.commit()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update SVG data for floor {floor_id} in building {building_id}: {e}")
        db.session.rollback()
        return False

def update_grid_svg_data(building_id: int, floor_id: int, grid_svg: str) -> bool:
    try:
        floor = Floor.query.get((floor_id, building_id))
        if not floor:
            raise ValueError(f"Floor with ID {floor_id} in building {building_id} not found.")
        
        floor.grid_svg = grid_svg
        db.session.commit()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update SVG data for floor {floor_id} in building {building_id}: {e}")
        db.session.rollback()
        return False

#TODO: omri need to fix
def getNewBuildingId():
    try:
        last_building = Building.query.order_by(Building.id.desc()).first()
        if last_building:
            last_id = int(last_building.id)
            return str(last_id + 1)
        else:
            return "1"  # Start with ID 1 if no buildings exist
    except Exception as e:
        print(f"[ERROR] Failed to get new building ID: {e}")
        return None
    