from server.models import Building, db
from server.DataBaseManger.graphManger import save_graph_to_db
from server.DataBaseManger.doorsManger import save_doors_to_db


def add_building(building_id: str, svg_data: str, graph_dict: dict, doors_dict: dict, x_min: float, x_max: float, y_min: float, y_max: float) -> bool:
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

def get_building_by_id(building_id: str):
    building = Building.query.get(building_id)
    if not building:
        raise ValueError(f"Building with ID {building_id} not found.")
    return building.x_min, building.x_max, building.y_min, building.y_max

def get_all_ids():
    buildings = Building.query.all()
    return [str(building.id) for building in buildings]
    