import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score
from collections import defaultdict


def load_csv(filename, target_column):
    data = pd.read_csv(filename)
    X = data.drop(columns=[target_column]).values
    y = data[target_column].values
    return X, y

def preprocess(X):
    return pd.DataFrame(X).apply(pd.to_numeric, errors='coerce').fillna(-100).to_numpy()

def predict_knn(train_X, train_y, test_X, k=4):
    predictions = []
    for test_vec in test_X:
        distances = [
            (train_y[i], np.linalg.norm(test_vec - train_X[i]))
            for i in range(len(train_X))
        ]
        top_k = sorted(distances, key=lambda x: x[1])[:k]
        
        # Weighted vote
        score = defaultdict(float)
        for vertex, dist in top_k:
            score[vertex] += 1 / (dist + 1e-6)
        pred = max(score.items(), key=lambda x: x[1])[0]
        predictions.append(pred)
    return predictions

if __name__ == "__main__":
    target_col = "vertex"
    train_file = "scan/train.csv"
    test_file = "scan/test_aligned.csv"

    train_X_raw, train_y = load_csv(train_file, target_col)
    test_X_raw, test_y = load_csv(test_file, target_col)

    train_X = preprocess(train_X_raw)
    test_X = preprocess(test_X_raw)

    # k-NN
    knn_predictions = predict_knn(train_X, train_y, test_X)
    for i in range(len(knn_predictions)):
        print(f"Test sample {i+1} - True vertex: {test_y[i]}, Predicted vertex: {knn_predictions[i]}")