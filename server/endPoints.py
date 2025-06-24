import os
from flask import Flask, request, jsonify, send_file, Blueprint
import server.dataBaseManger as dbm
from server.mangerBuldings import mangerBuldings
bp = Blueprint('building', __name__)
import server.DataBaseManger.buildingManger as building_db_manger
import server.DataBaseManger.graphManger as graph_db_manger
import server.DataBaseManger.doorsManger as doors_db_manger
from io import BytesIO
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import core.ManagerFloor as logic

manger = mangerBuldings()

@bp.route('/building/add', methods=['POST'], endpoint='addBuilding')
def add_building():
    try:
        if 'dwg' not in request.files or 'yaml' not in request.files:
            return "Both DWG and YAML files are required", 400

        dwg_file = request.files['dwg']
        yaml_file = request.files['yaml']
        buildingID = request.form.get('buildingId')
        yaml_path, dwg_path = dbm.saveInLocal(dwg_file, yaml_file)
        manger.addBuilding(yaml_path, dwg_path, buildingID)
        door_json = manger.getBuilding(buildingID).crete_door_json()
        return jsonify({
                "buildingId": buildingID,
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
        x_min, x_max, y_min, y_max = building_db_manger.get_building_by_id(buildingID)
        update_svg = logic.update_svg_door_names(svg, doors_data, x_min, x_max, y_min, y_max)
        building_db_manger.update_svg_data(buildingID, update_svg)
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



