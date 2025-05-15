import pandas as pd
from sklearn.neighbors import KNeighborsClassifier
from sklearn.metrics import accuracy_score
import os

# Define the types of data you expect
types = ["", "average", "median"]

results = []

def load_data(path):
    df = pd.read_csv(path)
    df = df.fillna(-100)  # Fill missing RSSI with -100
    X = df.drop(columns=["vertex"])
    y = df["vertex"]
    return X, y


test_file = f"test.csv"
# Process each pair
for dtype in types:
    train_file = f"train_{dtype}.csv"
    
    if os.path.exists(train_file) and os.path.exists(test_file):
        print(f"Processing: {train_file} + {test_file}")
        X_train, y_train = load_data(train_file)
        X_test, y_test = load_data(test_file)

        model = KNeighborsClassifier(n_neighbors=3)
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)

        results.append({
            "Type": dtype,
            "Accuracy": round(acc * 100, 2)
        })
    else:
        print(f"Missing files for type: {dtype}")

# Print summary
print("\n📊 Evaluation Summary:")
for row in results:
    print(f"{row['Type'].capitalize():<10} | Accuracy: {row['Accuracy']}%")
