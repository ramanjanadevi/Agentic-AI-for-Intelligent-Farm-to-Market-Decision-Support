"""
AgriSell AI - Weather Agent
Evaluates meteorological conditions (rain probability, humidity, temperature, forecast)
and computes weather risk, transport risk, and spoilage vulnerability based on crop sensitivity.
"""

import json
import os
from datetime import datetime, date
from typing import Dict, Any

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def load_json(filename: str):
    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)

class WeatherAgent:
    def __init__(self):
        self.crops = {c["id"]: c for c in load_json("crops.json")}
        self.weather_data = load_json("weather.json")["weatherProfiles"]

    def analyze(self, crop_name: str, location_name: str, harvest_date_str: str = "") -> Dict[str, Any]:
        crop_key = crop_name.lower().replace(" ", "_")
        crop_info = self.crops.get(crop_key, {})
        weather_sens = crop_info.get("weatherSensitivity", "Medium")
        rain_tol = crop_info.get("rainTolerance", "Low")

        loc_key = location_name.lower().replace(" ", "_")
        # Default profile if not strictly mapped
        weather_profile = self.weather_data.get(loc_key, self.weather_data.get("ongole"))

        temp = weather_profile["temperature"]
        humidity = weather_profile["humidity"]
        rain_prob = weather_profile["rainProbability"]
        condition = weather_profile["condition"]
        forecast = weather_profile["forecast"]

        # Date impact: If harvest was several days ago, crop has already been exposed
        days_since_harvest = 0
        if harvest_date_str:
            try:
                h_date = datetime.strptime(harvest_date_str, "%Y-%m-%d").date()
                today = date.today()
                diff = (today - h_date).days
                days_since_harvest = max(0, diff)
            except Exception:
                days_since_harvest = 0

        # Calculate Weather Risk Score (0-100)
        # Factor in rain probability, humidity, and crop weather sensitivity
        sens_multiplier = 1.4 if weather_sens == "High" else 1.0 if weather_sens == "Medium" else 0.65
        rain_penalty = 1.3 if rain_tol == "Low" else 0.8
        exposure_penalty = min(25, days_since_harvest * 5)

        raw_weather_score = (rain_prob * 0.5 + (humidity - 40) * 0.5) * sens_multiplier * rain_penalty + exposure_penalty
        raw_weather_score = max(5, min(98, raw_weather_score))

        if raw_weather_score >= 65:
            weather_risk = "HIGH"
            weather_risk_color = "red"
        elif raw_weather_score >= 40:
            weather_risk = "MEDIUM"
            weather_risk_color = "amber"
        else:
            weather_risk = "LOW"
            weather_risk_color = "emerald"

        # Transport Risk: Rain makes highway driving hazardous for open trailers / perishable produce
        if rain_prob > 60 or weather_sens == "High" and rain_prob > 35:
            transport_risk = "HIGH" if weather_sens == "High" else "MEDIUM"
        elif rain_prob > 30:
            transport_risk = "MEDIUM"
        else:
            transport_risk = "LOW"

        # Spoilage Risk: Humidity + Temp + elapsed time
        if humidity > 75 and temp > 28 and weather_sens in ["High", "Medium"]:
            spoilage_risk = "HIGH"
        elif humidity > 60 or days_since_harvest >= 3:
            spoilage_risk = "MEDIUM"
        else:
            spoilage_risk = "LOW"

        return {
            "temperature": f"{temp}°C",
            "temperatureVal": temp,
            "humidity": f"{humidity}%",
            "humidityVal": humidity,
            "rainProbability": f"{rain_prob}%",
            "rainProbabilityVal": rain_prob,
            "condition": condition,
            "weatherRisk": weather_risk,
            "weatherRiskScore": round(raw_weather_score, 1),
            "transportRisk": transport_risk,
            "spoilageRisk": spoilage_risk,
            "cropSensitivity": weather_sens,
            "daysSinceHarvest": days_since_harvest,
            "forecast": forecast,
            "status": "COMPLETED ✓"
        }
