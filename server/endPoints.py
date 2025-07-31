import io
import os
from flask import Flask, Response, request, jsonify, send_file, Blueprint, current_app
import server.dataBaseManger as dbm
from server.mangerBuldings import mangerBuldings
bp = Blueprint('building', __name__)
import server.DataBaseManger.floorManager as building_db_manger
import server.DataBaseManger.graphManger as graph_db_manger
import server.DataBaseManger.doorsManger as doors_db_manger
from io import BytesIO
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import core.ManagerFloor as logic



# @bp.route('/building/new', methods=['POST'], endpoint='newBuilding')
# def new_building():
@bp.route('/building/add', methods=['POST'], endpoint='newBuilding')
def statr_new_building():
    try:
        if 'dwg' not in request.files or 'yaml' not in request.files:
            return "Both DWG and YAML files are required", 400
        dwg_file = request.files['dwg']
        print(type(dwg_file))
        print(dwg_file.content_type)
        yaml_file = request.files['yaml']
        buildingID = request.form.get('buildingId')
        #yaml_path, dwg_path = dbm.saveInLocal(dwg_file, yaml_file)
        manger = current_app.config['MANAGER']
        svg = manger.addBuilding(yaml_file, dwg_file, buildingID)
        svg_string = svg.tostring()
        svg_bytes = svg_string.encode('utf-8')
        return Response(svg_bytes, mimetype='image/svg+xml')
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/building/calibrate', methods=['POST'], endpoint='calibrateBuilding')
def calibrate_building():
    try:
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
        door_json = manger.continueAddBuilding(building_id, point1, point2, real_distance_cm)
        return jsonify({
                "buildingId": building_id,
                "doors": door_json}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
@bp.route('/building/data/get', methods=['GET'], endpoint='getBuildingData')
def get_building_data():
    try:
        buildingId = request.args.get('buildingId')
        if not buildingId:
            return jsonify({"error": "Building ID is required"}), 400
        doors = doors_db_manger.get_all_doors_data(buildingId)
        return jsonify({
            "building_id" : str(buildingId),
            "rooms" : doors
        }), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/building/updateDoorsName', methods=['PUT'], endpoint='updateDoorName')
def update_doors_name():
    try:
        doors = request.get_json().get('doors', {})
        buildingID = str(request.get_json().get('buildingID'))
        if not doors or not buildingID:
            return jsonify({"error": "Doors data or building ID is missing"}), 400
        doors_db_manger.update_doors_names(doors, buildingID)
        doors_data = doors_db_manger.get_all_doors_data(buildingID)
        svg = building_db_manger.get_Svg_data(buildingID)
        grid_svg = building_db_manger.get_grid_svg(buildingID)
        x_min, x_max, y_min, y_max = building_db_manger.get_building_by_id(buildingID)
        update_svg = logic.update_svg_door_names(svg, doors_data, x_min, x_max, y_min, y_max)
        grid_svg = logic.update_svg_door_names(grid_svg, doors_data, x_min, x_max, y_min, y_max)
        building_db_manger.update_svg_data(buildingID, update_svg)
        building_db_manger.update_grid_svg_data(buildingID, grid_svg)
        return jsonify({"message": "Doors names updated successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/building/route/get', methods=['GET'], endpoint='getSvgPath')
def get_svg_path():
    try:
        buildingID = request.args.get('buildingId')
        start = request.args.get('start')
        goal = request.args.get('goal')
        if not buildingID:
            return jsonify({"error": "Building ID is required"}), 400
        if not start:
            return jsonify({"error": "Start point is required"}), 400
        if not goal:
            return jsonify({"error": "Goal point is required"}), 400
        graph = graph_db_manger.get_graph_from_db(buildingID)
        svg_data = building_db_manger.get_Svg_data(buildingID)
        x_min, x_max, y_min, y_max = building_db_manger.get_building_by_id(buildingID)
        start_p = doors_db_manger.get_coordinate_by_name(start, buildingID)
        goal_p = doors_db_manger.get_coordinate_by_name(goal, buildingID)
        svg_with_path = logic.get_svg_with_path(svg_data, graph, start_p, goal_p, x_min, x_max, y_min, y_max)
        svg_bytes = svg_with_path.encode('utf-8')
        buffer = BytesIO(svg_bytes)
        buffer.seek(0)
        return send_file(buffer, mimetype='image/svg+xml', as_attachment=False, download_name=f"building_{buildingID}_path.svg")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/building/getSvgDirect', methods=['GET'])
def send_svg(rel_path = None):
    try:
        buildingID = request.args.get('buildingId')
        if not buildingID:
            return jsonify({"error": "Building ID is required"}), 400
        svg_data = building_db_manger.get_Svg_data(buildingID)
        if not svg_data:
            return jsonify({"error": "SVG data not found for the given building ID"}), 404
        svg_bytes = svg_data.encode('utf-8')
        buffer = BytesIO(svg_bytes)
        buffer.seek(0)
        return send_file(buffer, mimetype='image/svg+xml', as_attachment=False, download_name=f"building_{buildingID}.svg")
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
   
@bp.route('/buildings/get', methods=['GET'], endpoint='getBuildings')
def get_buildings():
    try:
        building_list = building_db_manger.get_all_ids()
        if not building_list:
            return jsonify({"message": "No buildings found"}), 404
        return jsonify(building_list), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/doors/getAll', methods=['GET'], endpoint='getAllDoors')
def get_all_doors():
    try:
        building_id = request.args.get('buildingId')
        if not building_id:
            return jsonify({"error": "Building ID is required"}), 400
        doors = doors_db_manger.get_doors_coord(building_id)
        return jsonify(doors), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    
@bp.route('/building/getGridSvg', methods=['GET'], endpoint='getDoorByName')
def get_grid_svg():
    try:
        building_id = request.args.get('buildingId')
        if not building_id:
            return jsonify({"error": "Building ID is required"}), 400
        grid_svg = building_db_manger.get_grid_svg(building_id)
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

