import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
import pickle
import os

# ============================================================================
# 1. LOAD AND PREPROCESS DATASET
# ============================================================================
print("Loading dataset...")
data = pd.read_csv("data/supply_chain_data.csv")
print(f"Dataset shape: {data.shape}")

# Clean column names (remove spaces)
data.columns = data.columns.str.strip().str.replace(" ", "_")

# Handle missing values
initial_rows = len(data)
data = data.dropna()
print(f"Dropped {initial_rows - len(data)} rows with missing values")

# ============================================================================
# 2. CREATE TARGET VARIABLE (SUPPLY CHAIN RISK)
# ============================================================================
print("\nCreating target variable...")
print("Risk logic:")
print("  - High Risk (1) if: Lead_time > 20 OR Shipping_times > 7 OR Defect_rates > 3")
print("  - Else Safe (0)")

# Create risk target using specified logic
data["Supply_Chain_Risk"] = (
    (data["Lead_time"] > 20) | 
    (data["Shipping_times"] > 7) | 
    (data["Defect_rates"] > 3)
).astype(int)

risk_distribution = data["Supply_Chain_Risk"].value_counts()
print(f"\nRisk distribution:")
print(f"  Safe (0): {risk_distribution.get(0, 0)} ({risk_distribution.get(0, 0)/len(data)*100:.1f}%)")
print(f"  High Risk (1): {risk_distribution.get(1, 0)} ({risk_distribution.get(1, 0)/len(data)*100:.1f}%)")

# ============================================================================
# 3. FEATURE SELECTION AND PREPROCESSING
# ============================================================================
print("\nPreparing features...")

# Drop unnecessary columns (IDs, text-heavy, and the original target-related columns)
columns_to_drop = [
    "SKU", "Product_type", "Supplier_name", "Routes", "Customer_demographics",
    "Order_quantities"  # Less relevant to supply chain risk
]
data = data.drop(columns=columns_to_drop, errors='ignore')

# Keep important features for prediction:
# - Distance-related: Lead_time, Shipping_times
# - Cost-related: Shipping_costs, Manufacturing_costs, Price, Costs
# - Quality: Defect_rates
# - Stock/Inventory: Stock_levels, Availability
# - Production: Production_volumes, Manufacturing_lead_time
# - Categorical (to be encoded): Shipping_carriers, Inspection_results, Transportation_modes, Location

print(f"Features before encoding: {data.columns.tolist()}")

# Identify categorical columns to encode
categorical_cols = data.select_dtypes(include=['object']).columns.tolist()
print(f"Categorical columns to encode: {categorical_cols}")

# Encode categorical variables
label_encoders = {}
for col in categorical_cols:
    le = LabelEncoder()
    data[col] = le.fit_transform(data[col].astype(str))
    label_encoders[col] = le
    print(f"  Encoded '{col}'")

# ============================================================================
# 4. PREPARE FEATURES AND TARGET
# ============================================================================
X = data.drop(columns=["Supply_Chain_Risk"])
y = data["Supply_Chain_Risk"]

print(f"\nFinal feature set ({len(X.columns)} features):")
for col in X.columns:
    print(f"  - {col}")

# ============================================================================
# 5. TRAIN-TEST SPLIT
# ============================================================================
print("\nSplitting dataset (80% train, 20% test)...")
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)
print(f"Train set: {len(X_train)} samples")
print(f"Test set: {len(X_test)} samples")

# Scale features for better model performance
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# ============================================================================
# 6. TRAIN RANDOM FOREST CLASSIFIER
# ============================================================================
print("\nTraining RandomForestClassifier...")
model = RandomForestClassifier(
    n_estimators=100,
    max_depth=15,
    min_samples_split=5,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1,
    class_weight='balanced'
)
model.fit(X_train_scaled, y_train)
print("✓ Model training complete")

# ============================================================================
# 7. EVALUATE MODEL
# ============================================================================
print("\n" + "="*70)
print("MODEL EVALUATION")
print("="*70)

# Predictions
y_pred = model.predict(X_test_scaled)

# Accuracy
accuracy = accuracy_score(y_test, y_pred)
print(f"\nAccuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")

# Confusion Matrix
cm = confusion_matrix(y_test, y_pred)
print(f"\nConfusion Matrix:")
print(f"  True Negatives (Safe predicted as Safe):     {cm[0][0]}")
print(f"  False Positives (Safe predicted as Risk):    {cm[0][1]}")
print(f"  False Negatives (Risk predicted as Safe):    {cm[1][0]}")
print(f"  True Positives (Risk predicted as Risk):     {cm[1][1]}")

# Classification Report
print(f"\nClassification Report:")
print(classification_report(y_test, y_pred, target_names=["Safe", "High Risk"]))

# Feature Importance
feature_importance = pd.DataFrame({
    'feature': X.columns,
    'importance': model.feature_importances_
}).sort_values('importance', ascending=False)

print(f"\nTop 10 Most Important Features:")
for idx, row in feature_importance.head(10).iterrows():
    print(f"  {row['feature']}: {row['importance']:.4f}")

# ============================================================================
# 8. SAVE MODEL AND SCALER
# ============================================================================
print("\n" + "="*70)
print("SAVING MODEL")
print("="*70)

os.makedirs("models", exist_ok=True)

# Save the model
with open("models/model.pkl", "wb") as f:
    pickle.dump({
        'model': model,
        'scaler': scaler,
        'feature_columns': X.columns.tolist(),
        'label_encoders': label_encoders
    }, f)
print("✓ Model saved to models/model.pkl")

# Save feature importance
feature_importance.to_csv("models/feature_importance.csv", index=False)
print("✓ Feature importance saved to models/feature_importance.csv")

print("\n" + "="*70)
print("✓ Model trained and saved successfully!")
print("="*70)