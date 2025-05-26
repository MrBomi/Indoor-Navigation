import flask
from flask import Flask, request, jsonify
import dataBaseManger as dbm
from mangerBuldings import mangerBuldings
app = Flask(__name__)

manger = mangerBuldings()
@app.route('/building/add', methods=['POST'], endpoint='addBuilding')
def add_building():
    if 'dwg' not in request.files or 'yaml' not in request.files:
        return "Both DWG and YAML files are required", 400

    dwg_file = request.files['dwg']
    yaml_file = request.files['yaml']
    buildingID = request.form.get('buildingID')
    yaml_path, dwg_path = dbm.saveInLocal(dwg_file, yaml_file)
    manger.addBuilding(yaml_path, dwg_path, buildingID)

    door_json = manger.getBuilding(buildingID).crete_door_json()

    return jsonify({
            "image_url": manger.getBuilding(buildingID).getSvgPath(),
            "doors": door_json}), 200


if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=False, port=8574)


