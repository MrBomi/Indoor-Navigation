import os
from flask import Flask, request, jsonify, send_file
import dataBaseManger as dbm
from mangerBuldings import mangerBuldings
app = Flask(__name__)

manger = mangerBuldings()

@app.route('/building/add', methods=['POST'], endpoint='addBuilding')
def add_building():
    try:
        if 'dwg' not in request.files or 'yaml' not in request.files:
            return "Both DWG and YAML files are required", 400

        dwg_file = request.files['dwg']
        yaml_file = request.files['yaml']
        buildingID = int(request.form.get('buildingId'))
        yaml_path, dwg_path = dbm.saveInLocal(dwg_file, yaml_file)
        manger.addBuilding(yaml_path, dwg_path, buildingID)

        door_json = manger.getBuilding(buildingID).crete_door_json()

        return jsonify({
                "image_url": manger.getBuilding(buildingID).getSvgPath(),
                "doors": door_json}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route('/building/updateDoorsName', methods=['PUT'], endpoint='updateDoorName')
def update_doors_name():
    try:
        doors = request.get_json().get('doors', {})
        buildingID = int(request.get_json().get('buildingID'))
        if not doors or not buildingID:
            return jsonify({"error": "Doors data or building ID is missing"}), 400
        manger.getBuilding(buildingID).updateDoorsNames(doors)
        return jsonify({"message": "Doors names updated successfully"}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.route('/building/getPath', methods=['GET'], endpoint='getSvgPath')
def get_svg_path():
    try:
        buildingID = int(request.args.get('buildingID'))
        start = request.args.get('start')
        goal = request.args.get('goal')
        if not buildingID:
            return jsonify({"error": "Building ID is required"}), 400
        if not start:
            return jsonify({"error": "Start point is required"}), 400
        if not goal:
            return jsonify({"error": "Goal point is required"}), 400
        #path = manger.getBuilding(buildingID).getPath(start, goal)
        #svg_path = manger.getBuilding(buildingID).getSvgDrawing()
        path_svg_with_path = manger.getBuilding(buildingID).getSvgWithPath(start, goal)
        #return send_file(path_svg_with_path, mimetype='image/svg+xml')
        return send_svg(path_svg_with_path)
        #return jsonify({"svg_path": svg_with_path}), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

@app.route('/building/getSvgDirect', methods=['GET'])
def send_svg(rel_path = None):
    try:
        if rel_path is None:
            rel_path = request.args.get('svgLink')
        if not rel_path:
            return jsonify({"error": "Missing 'svgLink' parameter"}), 400
        
        abs_path = os.path.abspath(rel_path)
        allowed_root = os.path.abspath("static/output")

        if not abs_path.startswith(allowed_root):
            return jsonify({"error": "Unauthorized file access attempt"}), 403

        if not os.path.exists(abs_path):
            return jsonify({"error": "File not found"}), 404

        return send_file(abs_path, mimetype='image/svg+xml')
    
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=False, port=8574)


