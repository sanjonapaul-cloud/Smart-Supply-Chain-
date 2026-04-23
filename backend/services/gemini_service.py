import os
import google.generativeai as genai

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")

def generate_risk_explanation(data):
    prompt = f"""
You are an intelligent logistics assistant.

Explain the delivery risk prediction in simple terms.

Input data:
- Risk Level: {data.get('risk_level')}
- Traffic: {data.get('traffic')}
- Weather: {data.get('weather')}
- Distance: {data.get('distance')}

Give:
1. Simple explanation
2. Reason for risk
3. Suggestion for improvement
"""

    response = model.generate_content(prompt)
    return response.text