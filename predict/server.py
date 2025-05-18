from flask import Flask, request, jsonify
import euclidean_distances as ed


IP = '0.0.0.0'
PORT = 5000
TRAIN_FILE = 'scan/train_median.csv'

train_X, train_y, feature_names = ed.load_training_data(TRAIN_FILE)

app = Flask(__name__)




@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    
    if not isinstance(data, dict):
        return jsonify({"error": "Invalid input format. Expected a JSON object (map of RSSI)."}), 400

    try:
        top3 = ed.predict_by_top3(data, train_X, train_y, feature_names)
        response = [
            {"vertex": vertex, "distance": round(dist, 3)}
            for vertex, dist in top3
        ]
        return jsonify({"top3": response})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def home():
    return "Flask server is up!"

@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "healthy"}), 200



if __name__ == '__main__':
    app.run(host=IP, port=PORT, debug=True)