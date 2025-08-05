from server.models import Graph, db
import json

def save_graph_to_db(building_id: int, floor_id: int, graph_dict: dict, coarse_to_fine: dict) -> bool:
    try:
        #json_graph = json.dumps(graph_dict) 
        json_graph = json.dumps(stringify_graph_keys(graph_dict))
        json_coarse_to_fine = json.dumps(stringify_graph_keys(coarse_to_fine))

        graph = Graph(building_id=building_id, floor_id=floor_id, json_data=json_graph, json_coarse_to_fine=json_coarse_to_fine)

        existing = Graph.query.filter_by(building_id=building_id, floor_id=floor_id).first()
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

def get_graph_from_db(building_id: int, floor_id: int) -> dict:
    graph_record = Graph.query.filter_by(building_id=building_id, floor_id=floor_id).first()
    if not graph_record:
        raise ValueError(f"No graph found for building ID {building_id} and floor ID {floor_id}")

    raw_graph = json.loads(graph_record.json_data)
    graph = unstringify_graph_keys(raw_graph)
    return graph

def get_coarse_to_fine_from_db(building_id: int, floor_id: int) -> dict:
    graph_record = Graph.query.filter_by(building_id=building_id, floor_id=floor_id).first()
    if not graph_record:
        raise ValueError(f"No coarse to fine mapping found for building ID {building_id} and floor ID {floor_id}")

    raw_coarse_to_fine = json.loads(graph_record.json_coarse_to_fine)
    coarse_to_fine = unstringify_graph_keys(raw_coarse_to_fine)
    return coarse_to_fine

def unstringify_graph_keys(d: dict) -> dict:
    new_dict = {}
    for key_str, neighbors in d.items():
        key = tuple(map(float, key_str.split(',')))
        neighbors_tuples = [tuple(map(float, n.split(','))) for n in neighbors]
        new_dict[key] = neighbors_tuples
    return new_dict


