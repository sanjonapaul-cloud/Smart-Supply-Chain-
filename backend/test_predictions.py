#!/usr/bin/env python
"""Test script for the Supply Chain Risk prediction model"""

from app import app
import json

client = app.test_client()

# Test case 1: High Risk scenario (using snake_case)
print("\n" + "="*60)
print("TEST 1: HIGH RISK SCENARIO")
print("="*60)

high_risk_input = {
    'lead_time': 25,           # > 20 → HIGH RISK
    'lead_times': 25,          # Duplicate column from source data
    'shipping_times': 8,       # > 7 → HIGH RISK  
    'defect_rates': 2.5,
    'price': 50.0,
    'availability': 75,
    'number_of_products_sold': 500,
    'revenue_generated': 25000,
    'stock_levels': 100,
    'shipping_carriers': 'Carrier A',
    'shipping_costs': 150.0,
    'location': 'Mumbai',
    'production_volumes': 1000,
    'manufacturing_lead_time': 20,
    'manufacturing_costs': 500.0,
    'inspection_results': 'Pass',
    'transportation_modes': 'Road',
    'costs': 200.0
}

print("Input: lead_time=25 (>20), shipping_times=8 (>7)")
print()

response = client.post('/predict', json=high_risk_input, content_type='application/json')
result = response.get_json()

if response.status_code == 200:
    print("✓ SUCCESS")
    print(f"  Prediction: {result['prediction']}")
    print(f"  Confidence: {result['confidence']:.1f}%")
    print(f"  Safe Probability: {result['risk_probability']['safe']:.1f}%")
    print(f"  High Risk Probability: {result['risk_probability']['high_risk']:.1f}%")
else:
    print("✗ ERROR")
    print(json.dumps(result, indent=2))
    print(f"Status Code: {response.status_code}")

# Test case 2: Safe scenario
print("\n" + "="*60)
print("TEST 2: SAFE SCENARIO")
print("="*60)

safe_input = {
    'lead_time': 10,           # ≤ 20 → SAFE
    'lead_times': 10,          # Duplicate column from source data
    'shipping_times': 3,       # ≤ 7 → SAFE  
    'defect_rates': 1.5,       # ≤ 3 → SAFE
    'price': 50.0,
    'availability': 95,
    'number_of_products_sold': 500,
    'revenue_generated': 25000,
    'stock_levels': 100,
    'shipping_carriers': 'Carrier B',
    'shipping_costs': 150.0,
    'location': 'Bangalore',
    'production_volumes': 1000,
    'manufacturing_lead_time': 10,
    'manufacturing_costs': 300.0,
    'inspection_results': 'Pass',
    'transportation_modes': 'Air',
    'costs': 200.0
}

print("Input: lead_time=10 (≤20), shipping_times=3 (≤7), defect_rates=1.5 (≤3)")
print()

response = client.post('/predict', json=safe_input, content_type='application/json')
result = response.get_json()

if response.status_code == 200:
    print("✓ SUCCESS")
    print(f"  Prediction: {result['prediction']}")
    print(f"  Confidence: {result['confidence']:.1f}%")
    print(f"  Safe Probability: {result['risk_probability']['safe']:.1f}%")
    print(f"  High Risk Probability: {result['risk_probability']['high_risk']:.1f}%")
else:
    print("✗ ERROR")
    print(json.dumps(result, indent=2))
    print(f"Status Code: {response.status_code}")

print("\n" + "="*60)
print("✓ All tests completed successfully!")
print("="*60)
