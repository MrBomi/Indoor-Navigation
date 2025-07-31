from server.models import Building
from server.extensions import db


def get_new_buildingId():
    try:
        last_building = Building.query.order_by(Building.id.desc()).first()
        if last_building:
            last_id = int(last_building.id)
            return str(last_id + 1)
        else:
            return 1  # Start with ID 1 if no buildings exist
    except Exception as e:
        print(f"[ERROR] Failed to get new building ID: {e}")
        return None

def add_building(name: str, city: str, address: str) -> bool:
    try:
        building_id = get_new_buildingId()
        if not building_id:
            return False
        # Check if the name already exists
        existing = Building.query.filter_by(name=name).first()
        if existing:
            # Building already exists, do not add again
            return False

        building = Building(id=building_id, city=city, address=address)
        db.session.add(building)
        db.session.commit()
        return True

    except Exception as e:
        print(f"[ERROR] Failed to add building: {e}")
        db.session.rollback()
        return False
