from server.models import Building
from server.extensions import db
from server.DataBaseManger.graphManger import save_graph_to_db
from server.DataBaseManger.doorsManger import save_doors_to_db

def add_floor(building_id: str, svg_data: str, grid_svg: str, graph_dict: dict, doors_dict: dict, x_min: float, x_max: float, y_min: float, y_max: float) -> bool:
    try:
        existing = Building.query.get(building_id)
        if existing:
            db.session.delete(existing)
            db.session.commit()

        building = Building(id=building_id, svg_data=svg_data, grid_svg=grid_svg, x_min=x_min, x_max=x_max, y_min=y_min, y_max=y_max)
        db.session.add(building)
        db.session.commit() 

        graph_ok = save_graph_to_db(building_id, graph_dict)
        doors_ok = save_doors_to_db(doors_dict, building_id)

        return graph_ok and doors_ok

    except Exception as e:
        print(f"[ERROR] Failed to add building: {e}")
        db.session.rollback()
        return False
    
def get_Svg_data(building_id: str) -> str:
    try:
        building = Building.query.get(building_id)
        if building:
            return building.svg_data
        else:
            raise ValueError(f"Building with ID {building_id} not found.")
    except Exception as e:
        print(f"[ERROR] Failed to retrieve SVG data for building {building_id}: {e}")
        return ""

def get_grid_svg(building_id: str) -> str:
    try:
        building = Building.query.egt(building_id)
        if building:
            return building.grid_svg
        else:
            raise ValueError(f"Building with ID {building_id} not found.")
    except Exception as e:
        print(f"[ERROR] Failed to retrieve grid SVG for building {building_id}: {e}")
        return ""

def get_building_by_id(building_id: str):
    building = Building.query.get(building_id)
    if not building:
        raise ValueError(f"Building with ID {building_id} not found.")
    return building.x_min, building.x_max, building.y_min, building.y_max

def get_all_ids():
    buildings = Building.query.all()
    return [str(building.id) for building in buildings]

def update_svg_data(building_id: str, svg_data: str) -> bool:
    try:
        building = Building.query.get(building_id)
        if not building:
            raise ValueError(f"Building with ID {building_id} not found.")
        
        building.svg_data = svg_data
        db.session.commit()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update SVG data for building {building_id}: {e}")
        db.session.rollback()
        return False
    
def update_grid_svg_data(building_id: str, grid_svg: str) -> bool:
    try:
        building = Building.query.get(building_id)
        if not building:
            raise ValueError(f"Building with ID {building_id} not found.")
        
        building.grid_svg = grid_svg
        db.session.commit()
        return True
    except Exception as e:
        print(f"[ERROR] Failed to update grid SVG data for building {building_id}: {e}")
        db.session.rollback()
        return False

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
    
