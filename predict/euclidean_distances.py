import pandas as pd
import numpy as np

# Load CSV file
def load_csv(filename, target_column):
    data = pd.read_csv(filename)
    X = data.drop(columns=[target_column]).values
    y = data[target_column].values
    return X, y

def load_training_data(file_path, target_column="vertex"):
    df = pd.read_csv(file_path)
    feature_names = list(df.columns.drop(target_column))
    X = df[feature_names].apply(pd.to_numeric, errors='coerce').fillna(-100).to_numpy()
    y = df[target_column].values
    return X, y, feature_names

def rssi_map_to_vector(rssi_map, feature_names):
    return np.array([rssi_map.get(name, -100) for name in feature_names])

def predict_by_top3(rssi_map, train_X, train_y, feature_names):
    test_vec = rssi_map_to_vector(rssi_map, feature_names)
    distances = [
        (train_y[i], np.linalg.norm(test_vec - train_X[i]))
        for i in range(len(train_X))
    ]
    top3 = sorted(distances, key=lambda x: x[1])[:3]
    return top3



# Predict top 3 closest vertices for each test vector
def predict_top_3(train_X, train_y, test_X):
    predictions = []
    all_distances = []
    for test_vec in test_X:
        distances = [
            (train_y[i], np.linalg.norm(test_vec - train_X[i]))
            for i in range(len(train_X))
        ]
        all_distances.append(distances)
        top3 = sorted(distances, key=lambda x: x[1])[:3]
        predictions.append(top3)
    return predictions, all_distances

# Calculate the vertex closest to the average of top 3 predictions
def predict_closest_to_average(predictions, all_distances):
    closest_vertices = []
    
    for i, preds in enumerate(predictions):
        # Extract the distances of the top 3 predictions
        distances = [dist for _, dist in preds]
        # Calculate the average distance of the top 3
        avg_distance = sum(distances) / len(distances)
        # Find the vertex closest to the average distance from all distances
        closest_vertex = min(all_distances[i], key=lambda x: abs(x[1] - avg_distance))[0]
        closest_vertices.append(closest_vertex)
    
    return closest_vertices

# Clean and convert data
def preprocess(X):
    return pd.DataFrame(X).apply(pd.to_numeric, errors='coerce').fillna(-100).to_numpy()

# Main logic
if __name__ == "__main__":
    target_col = "vertex"
    test_file = "scan/test_aligned.csv"
    train_files = {
        "Average Model": "scan/train_average.csv",
        "Median Model": "scan/train_median.csv"
    }

    # Load and preprocess test data once
    test_X_raw, test_y = load_csv(test_file, target_col)
    test_X = preprocess(test_X_raw)

    # Predict with each model
    for model_name, train_file in train_files.items():
        print(f"\n🔍 {model_name} - Predicting on {test_file}")
        train_X_raw, train_y = load_csv(train_file, target_col)
        train_X = preprocess(train_X_raw)

        predictions, all_distances = predict_top_3(train_X, train_y, test_X)
        closest_vertices = predict_closest_to_average(predictions, all_distances)

        for i, preds in enumerate(predictions):
            print(f"\n🧪 Test sample {i+1} (True vertex: {test_y[i]})")
            for rank, (vertex, dist) in enumerate(preds, 1):
                print(f"  #{rank} → Vertex {vertex} | Distance = {round(dist, 2)}")
            print(f"  Closest to average: Vertex {closest_vertices[i]}")
