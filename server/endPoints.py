import io
import traceback
import os
from flask import Flask, Response, request, jsonify, send_file, Blueprint, current_app
#import server.dataBaseManger as dbm
from server.mangerBuldings import mangerBuldings
import server.DataBaseManger.buildingManger as building_db_manger
import server.DataBaseManger.floorManager as floor_db_manger
import server.DataBaseManger.graphManger as graph_db_manger
import server.DataBaseManger.doorsManger as doors_db_manger
from io import BytesIO
import sys
import server.constants as constants
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import core.ManagerFloor as logicMangerFloor
from core.predict.predict import Predict
from server.discord_logs import get_logger
bp = Blueprint('building', __name__)
from core.predict.wknn_service import predict_top1 as wknn_predict_top1, predict_topk as wknn_predict_topk
from core.predict.wknn_service import predict_top1 as wknn_predict_top1
from core.predict.hmm_model import HMMModel

logger = get_logger(__name__)

@bp.route(constants.ADD_FLOOR, methods=['POST'], endpoint='newFloor')
def start_new_floor():
    try:
        logger.info("Starting new floor creation...")
        if 'dwg' not in request.files or 'yaml' not in request.files:
            return "Both DWG and YAML files are required", 400
        dwg_file = request.files['dwg']
        print(type(dwg_file))
        print(dwg_file.content_type)
        yaml_file = request.files['yaml']
        buildingID = request.form.get(constants.BUILDING_ID)
        floorId = request.form.get(constants.FLOOR_ID)
        #yaml_path, dwg_path = dbm.saveInLocal(dwg_file, yaml_file)
        manger = current_app.config['MANAGER']
        svg = manger.addBuilding(yaml_file, dwg_file, buildingID, floorId)
        svg_string = svg.tostring()
        svg_bytes = svg_string.encode('utf-8')
        return Response(svg_bytes, mimetype='image/svg+xml'), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route(constants.CALIBRATE_FLOOR, methods=['POST'], endpoint='calibrateFloor')
def calibrate_floor():
    try:
        logger.info("Calibrating building...")
        data = request.get_json(force=True)  
        building_id = data.get('building_id')
        floor_id = data.get('floor_id')
        calibration = data.get('calibration_data', {})
        first_point = calibration.get('first_point', {})
        second_point = calibration.get('second_point', {})
        real_distance_cm = calibration.get('real_distance_cm')
        if not building_id or not first_point or not second_point or not real_distance_cm:
            return jsonify({"error": "Missing required calibration data"}), 400
        point1 = (first_point.get('x'), first_point.get('y'))
        point2 = (second_point.get('x'), second_point.get('y'))

        
        manger = current_app.config['MANAGER']
        door_json = manger.continueAddBuilding(building_id, floor_id, point1, point2, real_distance_cm)
        return jsonify({
                "buildingId": building_id,
                "doors": door_json}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route(constants.GET_FLOOR_DATA, methods=['GET'], endpoint='getFloorData')
def get_floor_data():
    try:
        buildingId = request.args.get(constants.BUILDING_ID)
        floorId = request.args.get(constants.FLOOR_ID)
        if not buildingId or not floorId:
            return jsonify({"error": "Building ID and Floor ID are required"}), 400
        doors = doors_db_manger.get_all_doors_data(buildingId, floorId)
        return jsonify({
            "building_id" : str(buildingId),
            "floor_id" : str(floorId),
            "rooms" : doors
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route(constants.UPDATE_DOORS_NAMES, methods=['PUT'], endpoint='updateDoorName')
def update_doors_name():
    try:
        doors = request.get_json().get('doors', {})
        buildingID = request.get_json().get('buildingID')
        floorId = request.get_json().get('floorId')
        if not doors or not buildingID or not floorId:
            return jsonify({"error": "Doors data, building ID, or floor ID is missing"}), 400
        doors_db_manger.update_doors_names(doors, buildingID, floorId)
        doors_data = doors_db_manger.get_all_doors_data(buildingID, floorId)
        svg = floor_db_manger.get_Svg_data(buildingID, floorId)
        grid_svg = floor_db_manger.get_grid_svg(buildingID, floorId)
        x_min, x_max, y_min, y_max = floor_db_manger.get_floor_by_id(buildingID, floorId)
        update_svg = logicMangerFloor.update_svg_door_names(svg, doors_data, x_min, x_max, y_min, y_max)
        grid_svg = logicMangerFloor.update_svg_door_names(grid_svg, doors_data, x_min, x_max, y_min, y_max)
        floor_db_manger.update_svg_data(buildingID, floorId, update_svg)
        floor_db_manger.update_grid_svg_data(buildingID, floorId, grid_svg)
        return jsonify({"message": "Doors names updated successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route(constants.FLOOR_GET_ROUTE, methods=['GET'], endpoint='getSvgPath')
def get_svg_path():
    try:
        buildingID = request.args.get(constants.BUILDING_ID)
        floorID = request.args.get(constants.FLOOR_ID)
        start = request.args.get('start')
        goal = request.args.get('goal')
        session_id = request.args.get('sessionId')
        if not buildingID or not floorID or not session_id:
            return jsonify({"error": "Building ID, Floor ID, and Session ID are required"}), 400
        if not start:
            return jsonify({"error": "Start point is required"}), 400
        if not goal:
            return jsonify({"error": "Goal point is required"}), 400
        if start == constants.CURRENT_LOCATION:
            start = request.args.get('coordinate')
            coordStart = floor_db_manger.convert_string_to_float_coordinates(start)
            start_raw = floor_db_manger.svg_to_raw(buildingID,floorID, coordStart[0], coordStart[1])
            start_p = graph_db_manger.get_closest_point_in_graph(buildingID, floorID, start_raw)
        else: 
            start_p = doors_db_manger.get_coordinate_by_name(start, buildingID, floorID)
        graph = graph_db_manger.get_graph_from_db(buildingID, floorID)
        svg_data = floor_db_manger.get_Svg_data(buildingID, floorID)
        x_min, x_max, y_min, y_max = floor_db_manger.get_floor_by_id(buildingID, floorID)
        goal_p = doors_db_manger.get_coordinate_by_name(goal, buildingID, floorID)
        predict_manager = current_app.config['PREDICT_MANAGER']
        grid = graph_db_manger.get_grid_from_db(buildingID, floorID)
        coords_to_cells = graph_db_manger.get_json_coord_to_cell(buildingID, floorID)
        predict_manager.add_new_model(graph, grid, coords_to_cells, start_p, goal_p, session_id)
        svg_with_path = logicMangerFloor.get_svg_with_path(svg_data, graph, start_p, goal_p, x_min, x_max, y_min, y_max)
        svg_bytes = svg_with_path.encode('utf-8')
        buffer = BytesIO(svg_bytes)
        buffer.seek(0)
        return send_file(buffer, mimetype='image/svg+xml', as_attachment=False, download_name=f"building_{buildingID}_path.svg")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route(constants.GET_SVG_DIRECT, methods=['GET'], endpoint='getSvgDirect')
def send_svg(rel_path = None):
    try:
        buildingID = request.args.get(constants.BUILDING_ID)
        floorID = request.args.get(constants.FLOOR_ID)
        if not buildingID or not floorID:
            return jsonify({"error": "Building ID and Floor ID are required"}), 400
        svg_data = floor_db_manger.get_Svg_data(buildingID, floorID)
        if not svg_data:
            return jsonify({"error": "SVG data not found for the given building ID"}), 404
        svg_bytes = svg_data.encode('utf-8')
        buffer = BytesIO(svg_bytes)
        buffer.seek(0)
        return send_file(buffer, mimetype='image/svg+xml', as_attachment=False, download_name=f"building_{buildingID}.svg"), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route(constants.GET_ALL_BUILDINGS, methods=['GET'], endpoint='getBuildings')
def get_buildings():
    try:
        building_list = building_db_manger.get_all_buldings()
        if not building_list:
            return jsonify({"message": "No buildings found"}), 404
        return jsonify(building_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route(constants.GET_ALL_DOORS, methods=['GET'], endpoint='getAllDoors')
def get_all_doors():
    try:
        building_id = request.args.get(constants.BUILDING_ID)
        floor_id = request.args.get(constants.FLOOR_ID)
        if not building_id or not floor_id:
            return jsonify({"error": "Building ID and Floor ID are required"}), 400
        doors = doors_db_manger.get_doors_coord(building_id, floor_id)
        return jsonify(doors), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route(constants.GET_GRID_SVG, methods=['GET'], endpoint='getGridSvg')
def get_grid_svg():
    try:
        building_id = request.args.get(constants.BUILDING_ID)
        floor_id = request.args.get(constants.FLOOR_ID)
        if not building_id or not floor_id:
            return jsonify({"error": "Building ID and Floor ID are required"}), 400
        grid_svg = floor_db_manger.get_grid_svg(building_id, floor_id)
        if not grid_svg:
            return jsonify({"error": "Grid SVG not found for the given building ID"}), 404
        svg_bytes = grid_svg.encode('utf-8')
        buffer = BytesIO(svg_bytes)
        buffer.seek(0)
        return send_file(buffer, mimetype='image/svg+xml', as_attachment=False, download_name=f"building_{building_id}.svg")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route(constants.ADD_BUILDING, methods=['POST'], endpoint='addBuilding')
def add_building():
    try:
        name = request.args.get('name')
        city = request.args.get('city')
        address = request.args.get('address')
        if not name or not city or not address:
            return jsonify({"error": "Building ID, city, and address are required"}), 400
        if building_db_manger.add_building(name, city, address):
            return jsonify({"message": "Building added successfully", "name": name}), 201
        else:
            return jsonify({"error": "Building already exists"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route(constants.GET_FLOORS, methods=['GET'], endpoint='getFloorsForBuilding')
def get_floors_for_building():
    try:
        building_id = request.args.get(constants.BUILDING_ID)
        if not building_id:
            return jsonify({"error": "Building ID is required"}), 400
        
        floor_ids = floor_db_manger.get_all_floor_ids(building_id)
        return jsonify(floor_ids), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@bp.route(constants.ADD_SCAN, methods=['PUT'], endpoint='addScan')
def add_scan():
    try:
        data = request.get_json()
        building_id = data.get(constants.BUILDING_ID)
        floor_id = data.get(constants.FLOOR_ID)
        scan_data = data.get('featureVector', {})
        if not building_id or not floor_id or not scan_data:
            return jsonify({"error": "Building ID, Floor ID, and scan data are required"}), 400
        floor_db_manger.add_scan_data(building_id, floor_id, scan_data)
        return jsonify({"message": "Scan data added successfully"}), 201
    except Exception as e:
        #print traceback.format_exc(), file=sys.stderr
        logger.error(f"Failed to add scan data: {e}")
        return jsonify({"error": str(e)}), 500
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

# TODO: need to move to new endpoint file
@bp.route(constants.START_PREDICT1, methods=['GET'], endpoint='startPredict')
def start_predict():
    try:
        building_id = request.args.get(constants.BUILDING_ID)
        floor_id = request.args.get(constants.FLOOR_ID)
        goal = request.args.get('goal')
        start = request.args.get('start')
        samples = request.get_json(silent=True)
        if not building_id or not floor_id or not start or not goal:
            return jsonify({"error": "Building ID, Floor ID, start, and goal are required"}), 400
        graph = graph_db_manger.get_graph_from_db(building_id, floor_id)
        #coarse_to_fine = graph_db_manger.get_coarse_to_fine_from_db(building_id, floor_id)
        scan_data = floor_db_manger.get_scan_data(building_id, floor_id)
        coord_to_cell = graph_db_manger.get_json_coord_to_cell(building_id, floor_id)
        cell_to_coords = graph_db_manger.get_json_cell_to_coords(building_id, floor_id)
        goal_p = doors_db_manger.get_coordinate_by_name(goal, building_id, floor_id)
        start_p = floor_db_manger.convert_string_to_float_coordinates(start)
        start_p = floor_db_manger.svg_to_raw(building_id, floor_id, start_p[0], start_p[1])
        start_p = (-200,1200)
        predict = Predict(graph, coord_to_cell, cell_to_coords, scan_data, start_p, goal_p)
        predict.debug_transition_info(start_p)
        predict.test(samples)
        return jsonify({"message": "Prediction completed successfully"}), 200
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@bp.route(constants.UPLOAD_SCAN, methods=['POST'], endpoint='uploadScanTable')
def upload_scan_table():
    try:
        building_id = request.form.get(constants.BUILDING_ID)
        floor_id = request.form.get(constants.FLOOR_ID)
        if 'scan' not in request.files:
            return jsonify({"error": "No scan part in the request"}), 400
        file = request.files['scan']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        if not building_id or not floor_id:
            return jsonify({"error": "Building ID and Floor ID are required"}), 400
        floor_db_manger.upload_floor_scan_table(building_id, floor_id, file.stream)
        return jsonify({"message": "Scan table uploaded successfully"}), 200
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500

@bp.route(constants.GET_ONE_CM_SVG, methods=['GET'])
def get_one_cm_svg():
    try:
        building_id = request.args.get(constants.BUILDING_ID)
        floor_id = request.args.get(constants.FLOOR_ID)
        if not building_id or not floor_id:
            return jsonify({"error": "Building ID and Floor ID are required"}), 400
        one_cm_svg = floor_db_manger.get_one_cm_svg(int(building_id), int(floor_id))
        return jsonify({"one_cm_svg": one_cm_svg}), 200
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    

@bp.route(constants.PREDICT_TOP1, methods=['POST'], endpoint='predictTop1')
def predict_top1_endpoint():
    """
    Body:
    {
      "building_id": 1,
      "floor_id": 3,
      "featureVector": { "<bssid>": -67, ... }
    }
    """
    try:
        data = request.get_json(force=True)
        building_id = data.get(constants.BUILDING_ID)
        floor_id    = data.get(constants.FLOOR_ID)
        scan_dict   = data.get(constants.FEATURE_VECTOR)

        if building_id is None or floor_id is None or not isinstance(scan_dict, dict):
            return jsonify({"error": "building_id, floor_id, and featureVector (dict) are required"}), 400

        label, conf = wknn_predict_top1(int(building_id), int(floor_id), scan_dict) # TODO: need to use wknn_predict_topk instead
        coord = graph_db_manger.get_coord_from_cell(building_id, floor_id, int(label))
        svg_coord = floor_db_manger.raw_to_svg(coord, building_id, floor_id)
        return jsonify({
            "svgX": svg_coord[0],
            "svgY": svg_coord[1],
            "label": label,
            "confidence": conf
        }), 200

    except ValueError as e:
        print(traceback.format_exc())
        logger.warning(f"[predictTop1] bad request: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        print(traceback.format_exc())
        logger.error(f"[predictTop1] internal error: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "internal error"}), 500

@bp.route(constants.CONCAT_SCAN, methods=['POST'], endpoint='insertScan')
def concatenate_scan_tables():
    try:
        #building_id = request.args.get(constants.BUILDING_ID)
        #floor_id = request.args.get(constants.FLOOR_ID)
        building_id = request.form.get(constants.BUILDING_ID)
        floor_id = request.form.get(constants.FLOOR_ID)
        if 'scan' not in request.files:
            return jsonify({"error": "No scan part in the request"}), 400
        file = request.files['scan']
        if file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        if not building_id or not floor_id:
            return jsonify({"error": "Building ID and Floor ID are required"}), 400
        success = floor_db_manger.concatenate_scan_tables(int(building_id), int(floor_id), file.stream)
        if success:
            return jsonify({"message": "Scan tables concatenated successfully"}), 200
        else:
            return jsonify({"error": "Failed to concatenate scan tables"}), 500
    except Exception as e:
        print(traceback.format_exc())
        return jsonify({"error": str(e)}), 500
    
@bp.route('/test', methods=['POST'])
def test_endpoint():
    data = request.get_json(force=True)
    graph = graph_db_manger.get_graph_from_db(2, 2)
    grid = graph_db_manger.get_grid_from_db(2, 2)
    coord_to_cell = graph_db_manger.get_json_coord_to_cell(2, 2)
    start_p = doors_db_manger.get_coordinate_by_name("2", 2, 2)
    goal_p = doors_db_manger.get_coordinate_by_name("59", 2, 2)
    predict = HMMModel(graph, grid, coord_to_cell, start_p, goal_p)
    
    predict.set_dynamic_cells_prob(682)
    scan_dict   = data.get('featureVector')
    results = wknn_predict_topk(2, 2, scan_dict, top_k=8)
    observations = {int(res['label']): res['confidence_norm'] for res in results}
    cell, conf = predict.viterbi(observations)
    return jsonify({
        "cell": cell,
        "confidence": conf
    }), 200

@bp.route(constants.PREDICT_TOP5, methods=['POST'], endpoint='predictTop5')
def predict_top5_endpoint():
    """
    Body:
    {
      "building_id": 1,
      "floor_id": 3,
      "featureVector": { "<bssid>": -67, ... }
    }

    Response:
    {
      "building_id": "1",
      "floor_id": "3",
      "predictions": [
         {"label": "A12", "confidence": 12.34, "confidence_norm": 0.41},
         ...
      ]
    }
    """
    try:
        data = request.get_json(force=True)
        building_id = data.get('building_id')
        floor_id    = data.get('floor_id')
        scan_dict   = data.get('featureVector')

        if building_id is None or floor_id is None or not isinstance(scan_dict, dict):
            return jsonify({"error": "building_id, floor_id, and featureVector (dict) are required"}), 400

        results = wknn_predict_topk(int(building_id), int(floor_id), scan_dict, top_k=1)

        return jsonify({
            "building_id": str(building_id),
            "floor_id": str(floor_id),
            "predictions": results
        }), 200

    except ValueError as e:
        logger.warning(f"[predictTop5] bad request: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"[predictTop5] internal error: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "internal error"}), 500

@bp.route(constants.GET_PREDICT, methods=['POST'], endpoint='getPredict')
def get_predict():
    try:
        data = request.get_json(force=True)
        predict_id = data.get(constants.SESSION_ID)
        scan_dict = data.get('featureVector')
        buildingId = data.get(constants.BUILDING_ID)
        floorId = data.get(constants.FLOOR_ID)
        prev_coord = data.get('userLocation')
        if not buildingId or not floorId or not scan_dict:
            return jsonify({"error": "Building ID, Floor ID, and featureVector (dict) are required"}), 400
        results = wknn_predict_topk(int(buildingId), int(floorId), scan_dict, top_k=5)
        prev_coord_raw = floor_db_manger.convert_string_to_float_coordinates(prev_coord)
        prev_coord_raw = floor_db_manger.svg_to_raw(buildingId, floorId, prev_coord_raw[0], prev_coord_raw[1])
        prev_cell = graph_db_manger.coord_to_cell2(buildingId, floorId, prev_coord_raw)
        predict_manager = current_app.config['PREDICT_MANAGER']
        curr_model = predict_manager.get_model(predict_id)
        curr_model.set_dynamic_cells_prob(prev_cell)
        observations = {int(res['label']): res['confidence_norm'] for res in results}
        cell, conf = curr_model.viterbi(observations)
        coord = graph_db_manger.get_coord_from_cell(buildingId, floorId, int(cell))
        svg_coord = floor_db_manger.raw_to_svg(coord, buildingId, floorId)
        return jsonify({
            "svgX": svg_coord[0],
            "svgY": svg_coord[1],
            "label": cell,
            "confidence": conf,
            "predictId": predict_id,
            "results": results
        }), 200
            

    except ValueError as e:
        logger.warning(f"[getPredict] bad request: {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"[getPredict] internal error: {e}\n{traceback.format_exc()}")
        return jsonify({"error": "internal error"}), 500


# @bp.route(constants.START_PREDICT, methods=['POST'], endpoint='addNewModel')
# def add_new_model():
#     try:
#         data = request.get_json(force=True)
#         building_id = data.get(constants.BUILDING_ID)
#         floor_id = data.get(constants.FLOOR_ID)
#         predictId = data.get("sessionId")
#         #start_p = data.get('start')
#         #goal_p = data.get('goal')
#         scan_dict = data.get('featureVector')
#         if not building_id or not floor_id or not scan_dict:
#             return jsonify({"error": "Building ID, Floor ID, and featureVector (dict) are required"}), 400
#         #graph = graph_db_manger.get_graph_from_db(building_id, floor_id)
#         #grid = graph_db_manger.get_grid_from_db(building_id, floor_id)
#        coord_to_cell = graph_db_manger.get_json_coord_to_cell(building_id, floor_id)
#         #start_p_raw = floor_db_manger.convert_string_to_float_coordinates(start_p)
#         #start_p_raw = floor_db_manger.svg_to_raw(building_id, floor_id, start_p_raw[0], start_p_raw[1])
#         #end_p = doors_db_manger.get_coordinate_by_name(goal_p, building_id, floor_id)
#         #predict_id = current_app.config['PREDICT_MANAGER'].add_new_id()
#         results = wknn_predict_topk(int(building_id), int(floor_id), scan_dict, top_k=1)
#         cell = results[0]['label']
#         coord = graph_db_manger.get_coord_from_cell(building_id, floor_id, int(cell))
#         svg_coord = floor_db_manger.raw_to_svg(coord, building_id, floor_id)
#         #predict_id = predict_manager.add_new_model(graph, grid, coord_to_cell, start_p_raw, end_p)
#         return jsonify({"svgX": svg_coord[0], "svgY": svg_coord[1], "label": cell}), 200
#     except Exception as e:
#         print(traceback.format_exc())
#         return jsonify({"error": str(e)}), 500