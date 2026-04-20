# Supply Chain Risk Prediction Model

## Overview

This document describes the Supply Chain Risk prediction model trained with **RandomForestClassifier** achieving **85% accuracy** on test data.

---

## Model Details

### Target Variable: Supply Chain Risk
The model predicts whether a supply chain is at **High Risk** or **Safe**:

- **High Risk (1)** if ANY of these conditions are met:
  - Lead time > 20 days
  - Shipping time > 7 days
  - Defect rate > 3%

- **Safe (0)** if all conditions are met:
  - Lead time ≤ 20 days
  - AND Shipping time ≤ 7 days
  - AND Defect rate ≤ 3%

---

## Performance Metrics

| Metric | Score |
|--------|-------|
| **Accuracy** | 85.00% |
| **Precision (High Risk)** | 82% |
| **Recall (High Risk)** | 100% |
| **F1-Score (High Risk)** | 0.90 |

### Confusion Matrix (Test Set: 20 samples)
```
                Predicted
                Safe  High Risk
Actual Safe       3        3
       High Risk  0       14
```

**Key Insight:** The model has 100% recall for High Risk cases - it catches all risky situations!

---

## Features Used (18 Total)

### Numerical Features
- `lead_time` (days) - **Most important: 30.82%**
- `shipping_times` (days) - **2nd important: 16.21%**
- `defect_rates` (%) - **3rd important: 13.12%**
- `price`
- `availability` (%)
- `number_of_products_sold`
- `revenue_generated`
- `stock_levels`
- `shipping_costs`
- `production_volumes`
- `manufacturing_lead_time`
- `manufacturing_costs`
- `costs`

### Categorical Features (Encoded)
- `shipping_carriers` (Carrier A, Carrier B, Carrier C, etc.)
- `location` (Mumbai, Delhi, Bangalore, Kolkata, etc.)
- `inspection_results` (Pass, Fail, Pending)
- `transportation_modes` (Road, Air, Sea, Rail)

---

## Top 10 Most Important Features

| Rank | Feature | Importance |
|------|---------|-----------|
| 1 | Lead_time | 0.3082 |
| 2 | Shipping_times | 0.1621 |
| 3 | Defect_rates | 0.1312 |
| 4 | Availability | 0.0489 |
| 5 | Production_volumes | 0.0483 |
| 6 | Price | 0.0410 |
| 7 | Manufacturing_lead_time | 0.0361 |
| 8 | Manufacturing_costs | 0.0334 |
| 9 | Costs | 0.0309 |
| 10 | Stock_levels | 0.0297 |

---

## API Endpoint

### POST `/predict`

**Request (JSON):**
```json
{
    "lead_time": 25,
    "shipping_times": 8,
    "defect_rates": 2.5,
    "price": 50.0,
    "availability": 75,
    "number_of_products_sold": 500,
    "revenue_generated": 25000,
    "stock_levels": 100,
    "shipping_carriers": "Carrier A",
    "shipping_costs": 150.0,
    "location": "Mumbai",
    "production_volumes": 1000,
    "manufacturing_lead_time": 20,
    "manufacturing_costs": 500.0,
    "inspection_results": "Pass",
    "transportation_modes": "Road",
    "costs": 200.0
}
```

**Success Response (200):**
```json
{
    "status": "success",
    "prediction": "High Risk 🚨",
    "confidence": 92.5,
    "risk_probability": {
        "safe": 7.5,
        "high_risk": 92.5
    }
}
```

**Error Response (400/500):**
```json
{
    "status": "error",
    "message": "Missing required features: ..."
}
```

---

## Other Endpoints

### GET `/health`
Check model status and features
```bash
curl http://localhost:5000/health
```

Response:
```json
{
    "status": "ok",
    "model_loaded": true,
    "features_count": 18,
    "feature_columns": [...]
}
```

### GET `/history`
Get prediction history
```bash
curl http://localhost:5000/history
```

---

## Training Scripts

### Run Training
```bash
cd backend
python train_model.py
```

**Output Files:**
- `models/model.pkl` - Trained model + scaler + encoders
- `models/feature_importance.csv` - Feature importance ranking

### Key Training Parameters
- **Algorithm:** RandomForestClassifier
- **Trees:** 100
- **Max Depth:** 15
- **Train/Test Split:** 80/20 (stratified)
- **Feature Scaling:** StandardScaler
- **Class Weights:** Balanced

---

## Data Distribution

| Class | Count | Percentage |
|-------|-------|-----------|
| Safe | 29 | 29.0% |
| High Risk | 71 | 71.0% |

The dataset shows that ~71% of supply chains are at high risk, highlighting the importance of risk management.

---

## Model Files

```
backend/models/
├── model.pkl                  # Main model file (167.9 KB)
└── feature_importance.csv     # Feature rankings
```

### model.pkl Contents
```python
{
    'model': RandomForestClassifier,
    'scaler': StandardScaler,
    'feature_columns': [...],
    'label_encoders': {...}
}
```

---

## Usage Examples

### Python
```python
import pickle
from pathlib import Path

# Load model
model_path = Path("backend/models/model.pkl")
with open(model_path, "rb") as f:
    model_data = pickle.load(f)

model = model_data['model']
scaler = model_data['scaler']

# Prepare input (must match training features)
import pandas as pd
input_df = pd.DataFrame([{
    'lead_time': 25,
    'shipping_times': 8,
    ...
}])

# Encode categorical features
for col, encoder in model_data['label_encoders'].items():
    if col in input_df.columns:
        input_df[col] = encoder.transform(input_df[col])

# Predict
X_scaled = scaler.transform(input_df[model_data['feature_columns']])
prediction = model.predict(X_scaled)[0]
probability = model.predict_proba(X_scaled)[0]
```

### cURL
```bash
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "lead_time": 25,
    "shipping_times": 8,
    "defect_rates": 2.5,
    ...
  }'
```

---

## Improvements Over Previous Model

| Aspect | Old Model | New Model |
|--------|-----------|-----------|
| **Algorithm** | Logistic Regression | RandomForestClassifier |
| **Target** | Defect risk (weak) | Supply Chain Risk (comprehensive) |
| **Features** | Limited | 18 engineered features |
| **Accuracy** | ~65% | **85%** |
| **Recall (High Risk)** | ~60% | **100%** |
| **Predictions** | Random-like | Real ML training |

---

## Notes

1. **Feature Order Matters:** The model expects features in a specific order. Use the `feature_columns` from model.pkl
2. **Data Scaling:** Always scale features using the saved scaler
3. **Categorical Encoding:** Use the saved label_encoders for categorical features
4. **Missing Values:** The model was trained on complete data. Handle any missing values before prediction
5. **Valid Categories:** Ensure categorical values match those seen during training

---

## Training Date
- **Model Created:** April 20, 2026
- **Training Samples:** 80 (from 100 total)
- **Test Samples:** 20

---

## Support

For issues or questions:
1. Check that all required features are provided
2. Verify categorical values are valid
3. Ensure the model file exists at `backend/models/model.pkl`
4. Check server logs for detailed error messages
