from server.models import Door, db

def create_key(door_id, building_id):
    return f"{building_id}_{door_id}"

def putId(door_id: str) -> int:
    try:
        return int(door_id.split('_')[1])
    except (IndexError, ValueError):
        raise ValueError(f"Invalid door ID format: {door_id}")

def save_doors_to_db(doors_dict: dict, building_id: int, floor_id: int) -> bool:
    Door.query.filter_by(building_id=building_id, floor_id=floor_id).delete()
    for door in doors_dict.values():
        door_id = door.getId() #create_key(door.getId(), building_id)
        db_door = Door(
            id=door_id,
            x=door.getX(),
            y=door.getY(),
            name=door.getName(),
            scale_x=door.getScaledCoordinates()[0],
            scale_y=door.getScaledCoordinates()[1],
            building_id=building_id,
            floor_id=floor_id
        )
        db.session.add(db_door)

    db.session.commit()
    return True
    
def update_doors_names(doors_dict: dict, building_id: str) -> bool:
    for door_id, name in doors_dict.items():
        key = create_key(door_id, building_id)
        db_door = Door.query.filter_by(id=key, building_id=building_id).first()
        if db_door:
            db_door.name = name
            
        else:
            print(f"[ERROR] Door with ID {door_id} not found in building {building_id}.")
            return False
    db.session.commit()
    return True

def get_coordinate_by_name(name: str, building_id: str) -> tuple:
    door = Door.query.filter_by(name=name, building_id=building_id).first()
    if door:
        return (door.x, door.y)
    else:
        raise ValueError(f"Door with name '{name}' not found in building {building_id}.")

def get_all_doors_data(building_id: str) -> dict:
    doors = Door.query.filter_by(building_id=building_id).all()
    doors_data = []
    for door in doors:
        doors_data.append({
            "id": putId(door.id),
            "x": door.x,
            "y": door.y,
            "name": door.name
        })
    return doors_data

def get_doors_coord(building_id: str) -> dict:
    doors = Door.query.filter_by(building_id=building_id).all()
    doors_data = []
    for door in doors:
        doors_data.append({
            "id": putId(door.id),
            "name": door.name,
            "scale_coord": (door.scale_x, door.scale_y),
        })
    return doors_data

    

