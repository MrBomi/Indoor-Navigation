from server.models import Door, db

def save_doors_to_db(doors_dict: dict, building_id: int) -> bool:
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
    
def update_doors_names(doors_dict: dict, building_id: int) -> bool:
    for door_id, name in doors_dict.items():
        key = int(door_id)
        db_door = Door.query.filter_by(id=key, building_id=building_id).first()
        if db_door:
            db_door.name = name
            
        else:
            print(f"[ERROR] Door with ID {door_id} not found in building {building_id}.")
            return False
    db.session.commit()
    return True

def get_coordinate_by_name(name: str, building_id: int) -> tuple:
    door = Door.query.filter_by(name=name, building_id=building_id).first()
    if door:
        return (door.x, door.y)
    else:
        raise ValueError(f"Door with name '{name}' not found in building {building_id}.")