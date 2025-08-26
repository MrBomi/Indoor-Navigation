from flask import json
from typing import BinaryIO
import io
from server.models import Floor, Building
from server.extensions import db
from server.DataBaseManger.graphManger import save_graph_to_db
from server.DataBaseManger.doorsManger import save_doors_to_db
from server.discord_logs import get_logger
import server.DataBaseManger.filesManager as fm
import pandas as pd
import csv

logger = get_logger(__name__)


def add_floor(building_id: int, floor_id: int, svg_data: str, grid_svg: str, graph_dict: dict, doors_dict: dict, x_min: float, x_max: float, y_min: float, y_max: float, grid_map: dict, coords_to_cell: dict, cell_to_coords: dict, grid_graph: dict, one_cm_svg: float) -> bool:
    try:
        existing = Floor.query.get((floor_id, building_id))
        if existing:
            db.session.delete(existing)
            db.session.commit()
            print("ℹ Deleted existing floor", flush=True)
            logger.info(f"Deleted existing floor {floor_id} in building {building_id}")
        logger.info(f"Adding floor {floor_id} to building {building_id} with SVG data and graph.")
        floor_grid_map = json.dumps({str(k): v for k, v in grid_map.items()})
        floor = Floor(
            id=floor_id,
            svg_data=svg_data,
            grid_svg=grid_svg,
            x_min=x_min, x_max=x_max,
            y_min=y_min, y_max=y_max,
            building_id=building_id,
            grid_map=floor_grid_map,
            one_cm_svg=one_cm_svg
        )
        db.session.add(floor)
        db.session.commit()
        logger.info(f"Added floor {floor_id} to building {building_id}")
        print("✅ Floor added to DB", flush=True)

        try:
            graph_ok = save_graph_to_db(building_id, floor_id, graph_dict, coords_to_cell, cell_to_coords, grid_graph)
            print("✅ Graph saved", flush=True)
            logger.info(f"Graph for floor {floor_id} in building {building_id} saved successfully")
        except Exception as e:
            print("❌ Error saving graph:", e, flush=True)
            logger.error(f"Error saving graph for floor {floor_id} in building {building_id}: {e}")
            graph_ok = False

        try:
            doors_ok = save_doors_to_db(doors_dict, building_id, floor_id)
            print("✅ Doors saved", flush=True)
            logger.info(f"Doors for floor {floor_id} in building {building_id} saved successfully")
        except Exception as e:
            print("❌ Error saving doors:", e, flush=True)
            logger.error(f"Error saving doors for floor {floor_id} in building {building_id}: {e}")
            doors_ok = False

        

        return graph_ok and doors_ok

    except Exception as e:
        print(f"[ERROR] Failed to add floor: {e}", flush=True)
        logger.error(f"Failed to add floor {floor_id} to building {building_id}: {e}")
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

def get_floor_by_id(building_id: int, floor_id: int):
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
    
def is_floor_exists(building_id: int, floor_id: int) -> bool:
    floor = Floor.query.get((floor_id, building_id))
    return floor is not None

def add_scan_data(building_id: int, floor_id: int, scan_records: list[dict]) -> bool:
    floor = Floor.query.get((floor_id, building_id))
    if not floor:
        raise ValueError(f"Floor {floor_id} in building {building_id} not found.")

    
    grid_map = json.loads(floor.grid_map) if floor.grid_map else {}
    new_data = {}
    for rec in scan_records:
        name = rec.get("name")
        if not name or name not in grid_map:
            continue
        coord = grid_map[name]
        key = f"{coord[0]},{coord[1]}"
        features = {k: v for k, v in rec.items() }
        new_data[key] = features

    existing = json.loads(floor.scan_table) if floor.scan_table else {}
    existing.update(new_data)
    floor.scan_table = json.dumps(existing)

    db.session.add(floor)
    db.session.commit()
    return True

def get_scan_data(building_id: int, floor_id: int) -> dict:
    floor = Floor.query.get((floor_id, building_id))
    if not floor:
        raise ValueError(f"Floor {floor_id} in building {building_id} not found.")
    
    scan_data = json.loads(floor.scan_table) if floor.scan_table else {}
    return scan_data

def svg_to_raw(building_id: int, floor_id: int, x_svg: float, y_svg: float) -> tuple[float, float]:
    x_min_raw, x_max_raw, y_min_raw, y_max_raw = get_floor_by_id(building_id, floor_id)
    scale = 800 / max(x_max_raw - x_min_raw, y_max_raw - y_min_raw)
    x_raw = x_svg / scale + x_min_raw
    y_raw = y_max_raw - (y_svg / scale)
    return (x_raw, y_raw)

def raw_to_svg(coord: tuple[float, float], building_id: int, floor_id: int) -> tuple[float, float]:
    x_raw, y_raw = coord
    x_min_raw, x_max_raw, y_min_raw, y_max_raw = get_floor_by_id(building_id, floor_id)
    scale = 800 / max(x_max_raw - x_min_raw, y_max_raw - y_min_raw)
    x_svg = (x_raw - x_min_raw) * scale
    y_svg = (y_max_raw - y_raw) * scale
    return (x_svg, y_svg)

def convert_string_to_float_coordinates(coord_str: str) -> tuple[float, float]:
    try:
        x_str, y_str = coord_str.split(',')
        return float(x_str), float(y_str)
    except ValueError as e:
        print(f"[ERROR] Failed to convert string to float coordinates: {e}")
        raise ValueError(f"Invalid coordinate string: {coord_str}") from e


def _read_new_csv(new_scan_table: BinaryIO) -> pd.DataFrame:
    """
    Read an incoming CSV into a pandas DataFrame.
    Supports:
      - File path as str (even though the type hint is BinaryIO, Python won't enforce it at runtime)
      - file-like object with .read() / .stream
      - raw bytes/bytearray
    Raises:
      - ValueError if the input is unsupported or cannot be parsed.
    """
    # Flask FileStorage-style (has .stream)
    if hasattr(new_scan_table, "stream"):
        new_scan_table.stream.seek(0)
        return pd.read_csv(new_scan_table.stream)

    # Generic file-like (has .read())
    if hasattr(new_scan_table, "read"):
        try:
            new_scan_table.seek(0)
        except Exception:
            pass
        return pd.read_csv(new_scan_table)

    # Raw bytes
    if isinstance(new_scan_table, (bytes, bytearray)):
        return pd.read_csv(io.BytesIO(new_scan_table))

    # File path as string
    if isinstance(new_scan_table, str):
        return pd.read_csv(new_scan_table)

    raise ValueError("Unsupported input for new_scan_table")


def upload_floor_scan_table(building_id: int, floor_id: int, scan_table: BinaryIO) -> bool:
    try:
        if not is_floor_exists(building_id, floor_id):
            raise ValueError(f"Floor {floor_id} in building {building_id} does not exist.")
        file_key = f"building_{building_id}/floor_{floor_id}/scan_table.csv"
        fm.upload_to_r2(scan_table, file_key, content_type="text/csv")
        print(f"✅ Scan table for floor {floor_id} in building {building_id} uploaded successfully.", flush=True)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to upload scan table for floor {floor_id} in building {building_id}: {e}", flush=True)
        return False
    
def download_floor_scan_table(building_id: int, floor_id: int) -> pd.DataFrame:
    try:
        if not is_floor_exists(building_id, floor_id):
            raise ValueError(f"Floor {floor_id} in building {building_id} does not exist.")
        file_key = f"building_{building_id}/floor_{floor_id}/scan_table.csv"
        file_bytes = fm.download_from_r2(file_key)
        from io import StringIO
        s = str(file_bytes, 'utf-8')
        data = StringIO(s) 
        df = pd.read_csv(data)
        print(f"✅ Scan table for floor {floor_id} in building {building_id} downloaded successfully.", flush=True)
        return df
    except FileNotFoundError:
        print(f"[ERROR] Scan table for floor {floor_id} in building {building_id} not found in R2.", flush=True)
        return pd.DataFrame()  # Return empty DataFrame if file not found
    except Exception as e:
        print(f"[ERROR] Failed to download scan table for floor {floor_id} in building {building_id}: {e}", flush=True)
        return pd.DataFrame()

def concatenate_scan_tables(building_id: int, floor_id: int, new_scan_table: BinaryIO) -> bool:
    """
    Merge the existing floor scan table with a new CSV and upload back to R2 as text/csv.

    Behavior:
      1) Load the existing table via download_floor_scan_table (returns empty DF if not found).
      2) Read the incoming CSV (file path, file-like stream, or bytes) into a DataFrame.
      3) Concatenate, drop duplicates, reset index.
      4) Upload the merged CSV to R2 under the stable key:
           building_{building_id}/floor_{floor_id}/scan_table.csv
      5) Return True on successful upload, False otherwise.

    Notes:
      - Adjust drop_duplicates(subset=[...]) if you have a logical unique key.
      - upload_to_r2 returns the key (string). Any exception will be raised and caught here.
    """
    try:
        # 1) Existing DataFrame (empty DF if not found is already handled inside your function)
        existing_df = download_floor_scan_table(building_id, floor_id)
        if existing_df is None:
            existing_df = pd.DataFrame()

        # 2) New DataFrame from provided source
        new_df = _read_new_csv(new_scan_table)

        # 3) Merge & dedupe (change subset to your unique columns if needed)
        if existing_df.empty:
            combined_df = new_df.reset_index(drop=True)
        else:
            combined_df = (
                pd.concat([existing_df, new_df], ignore_index=True)
                  .drop_duplicates()  # e.g. .drop_duplicates(subset=["x","y","ssid"])
                  .reset_index(drop=True)
            )

        # 4) Upload CSV bytes back to R2 (overwrite same key)
        key = f"building_{building_id}/floor_{floor_id}/scan_table.csv"
        csv_bytes = combined_df.to_csv(index=False).encode("utf-8")
        uploaded_key = fm.upload_to_r2(csv_bytes, key, content_type="text/csv")

        print(f"✅ Concatenated & uploaded scan table to '{uploaded_key}'", flush=True)
        return True
    except Exception as e:
        print(f"[ERROR] Failed to concatenate/upload scan table for floor {floor_id} in building {building_id}: {e}", flush=True)
        return False

def get_one_cm_svg(building_id: int, floor_id: int) -> float:
    try:
        floor = Floor.query.get((floor_id, building_id))
        if floor:
            return floor.one_cm_svg
        else:
            raise ValueError(f"Floor with ID {floor_id} in building {building_id} not found.")
    except Exception as e:
        print(f"[ERROR] Failed to retrieve one_cm_svg for floor {floor_id} in building {building_id}: {e}")
        return -1.0