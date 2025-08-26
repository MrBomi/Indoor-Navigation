from server.models import Graph, db
import json
from typing import Dict, Tuple, Set, Iterable
Coord = Tuple[float, float]
CellID = int
Bounds = Tuple[float, float, float, float]

def save_graph_to_db(building_id: int, floor_id: int, graph_dict: dict, coords_to_cell: dict, cell_to_coords: dict, grid_graph: dict) -> bool:
    try:
        #json_graph = json.dumps(graph_dict) 
        json_graph = json.dumps(stringify_graph_keys(graph_dict))
        json_coords_to_cell = coord_to_cells_to_json(coords_to_cell)
        json_cell_to_coords = cell_to_coords_to_json(cell_to_coords)
        json_grid_graph = cell_to_cells_to_json(grid_graph)

        graph = Graph(building_id=building_id, floor_id=floor_id, json_data=json_graph, json_coords_to_cell=json_coords_to_cell, json_cell_to_coords=json_cell_to_coords, json_grid_graph=json_grid_graph)

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


def coord_to_cells_to_json(coord_to_cells: Dict[Coord, Set[CellID]]) -> str:
    """
    Convert Dict[(x,y), set(CellID)] into a JSON string:
      - tuple keys (x,y) become "x,y" strings
      - sets become lists
    """
    serializable = {f"{x},{y}": list(cells) for (x, y), cells in coord_to_cells.items()}
    return json.dumps(serializable)

def cell_to_coords_to_json(cell_to_coords: Dict[CellID, Set[Coord]]) -> str:
    """
    Convert Dict[CellID, set((x,y))] into a JSON string:
      - sets of tuples become lists of [x,y] lists
    """
    serializable = {cid: [list(coord) for coord in coords] for cid, coords in cell_to_coords.items()}
    return json.dumps(serializable)

def cell_to_cells_to_json(cell_to_cells: Dict[CellID, Set[CellID]]) -> str:
    """
    Convert Dict[CellID, set(CellID)] into a JSON string:
      - sets become lists
    """
    serializable = {cid: list(neighbors) for cid, neighbors in cell_to_cells.items()}
    return json.dumps(serializable)

def json_to_coord_to_cells(json_str: str) -> Dict[Coord, Set[CellID]]:
    """
    Convert JSON string back to Dict[(x,y), set(CellID)].
    Keys in JSON are "x,y" strings -> converted to (float(x), float(y)) tuples.
    Lists in JSON -> converted to sets.
    """
    data = json.loads(json_str)
    return {tuple(map(float, key.split(","))): set(val) for key, val in data.items()}

def json_to_cell_to_coords(json_str: str) -> Dict[CellID, Set[Coord]]:
    """
    Convert JSON string back to Dict[CellID, set((x,y))].
    Lists in JSON -> converted to sets of (float(x), float(y)).
    """
    data = json.loads(json_str)
    return {int(cid): {tuple(map(float, coord)) for coord in coords} for cid, coords in data.items()}

def json_to_cell_to_cells(json_str: str) -> Dict[CellID, Set[CellID]]:
    """
    Convert JSON string back to Dict[CellID, set(CellID)].
    Lists in JSON -> converted to sets of ints.
    """
    data = json.loads(json_str)
    return {int(cid): set(map(int, neighbors)) for cid, neighbors in data.items()}

def get_json_coord_to_cell(building_id: int, floor_id: int) -> str:
    graph_record = Graph.query.filter_by(building_id=building_id, floor_id=floor_id).first()
    if not graph_record:
        raise ValueError(f"No coords to cell mapping found for building ID {building_id} and floor ID {floor_id}")

    return json_to_coord_to_cells(graph_record.json_coords_to_cell)

def get_json_cell_to_coords(building_id: int, floor_id: int) -> str:
    graph_record = Graph.query.filter_by(building_id=building_id, floor_id=floor_id).first()
    if not graph_record:
        raise ValueError(f"No cell to coords mapping found for building ID {building_id} and floor ID {floor_id}")

    return json_to_cell_to_coords(graph_record.json_cell_to_coords)


def get_coord_from_cell(building_id: int, floor_id: int, cell_id: int) -> Set[Coord]:
    graph_record = Graph.query.filter_by(building_id=building_id, floor_id=floor_id).first()
    if not graph_record:
        raise ValueError(f"No cell to coords mapping found for building ID {building_id} and floor ID {floor_id}")

    cell_to_coords = json_to_cell_to_coords(graph_record.json_cell_to_coords)
    if cell_id not in cell_to_coords:
        raise ValueError(f"Cell ID {cell_id} not found in building ID {building_id} and floor ID {floor_id}")

    points = cell_to_coords[cell_id]
    if not points:
        return None
    
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    
    center_x = sum(xs) / len(xs)
    center_y = sum(ys) / len(ys)
    
    return (center_x, center_y)