import pandas as pd

# Load CSV files
train_df = pd.read_csv("scan/train_average.csv")
test_df = pd.read_csv("scan/test.csv")

# Separate 'vertex' column in test (if exists)
vertex_col = test_df["vertex"] if "vertex" in test_df.columns else None

# Drop 'vertex' from train features
train_features = train_df.drop(columns=["vertex"], errors="ignore")

# Convert test column names (excluding 'vertex') to uppercase
test_feature_cols = [col.upper() for col in test_df.columns if col != "vertex"]
test_df.columns = test_feature_cols + (["vertex"] if "vertex" in test_df.columns else [])

# Also convert train feature names to uppercase
train_features.columns = [col.upper() for col in train_features.columns]

# Find missing columns in test
missing_cols = [col for col in train_features.columns if col not in test_df.columns]

# Add missing columns with -100
for col in missing_cols:
    test_df[col] = -100

# Drop extra columns from test, except 'vertex'
extra_cols = [col for col in test_df.columns if col not in train_features.columns and col != "vertex"]
test_df = test_df.drop(columns=extra_cols)

# Reorder test columns to match train, with 'vertex' at the end if it exists
ordered_cols = list(train_features.columns)
if "vertex" in test_df.columns:
    ordered_cols.append("vertex")

test_df = test_df[ordered_cols]

# Save aligned test file
test_df.to_csv("scan/test_aligned.csv", index=False)

print("✅ Test file aligned to train features. 'vertex' column kept.")
