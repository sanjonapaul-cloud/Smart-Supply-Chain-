import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import LabelEncoder, StandardScaler # Import StandardScaler
import pickle
import os

# load dataset
data = pd.read_csv("supply_chain_data.csv")

# clean column names (remove spaces)
data.columns = data.columns.str.strip().str.replace(" ", "_")

# drop unnecessary columns (IDs / text-heavy columns)
data = data.drop(columns=["SKU", "Product_Type", "Supplier_name", "Routes"], errors='ignore')

# handle missing values
data = data.dropna()

# convert categorical columns to numeric
label_encoders = {}
for col in data.select_dtypes(include=['object']).columns:
    le = LabelEncoder()
    data[col] = le.fit_transform(data[col])
    label_encoders[col] = le

# create target variable (High defect risk)
data["Defect_Risk"] = (data["Defect_rates"] > data["Defect_rates"].mean()).astype(int)

# features and target
X = data.drop(columns=["Defect_Risk", "Defect_rates"])
y = data["Defect_Risk"]

# split dataset
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale numerical features (newly added)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# train model
model = LogisticRegression(max_iter=5000) 
model.fit(X_train_scaled, y_train) # Fit on scaled data

# create folder if not exists
os.makedirs("models", exist_ok=True)

# save model
with open("models/model.pkl", "wb") as f:
    pickle.dump(model, f)

# save encoders and scaler (VERY IMPORTANT)
with open("models/encoders.pkl", "wb") as f:
    pickle.dump(label_encoders, f)
with open("models/scaler.pkl", "wb") as f:
    pickle.dump(scaler, f)

print("Model trained and saved successfully!")