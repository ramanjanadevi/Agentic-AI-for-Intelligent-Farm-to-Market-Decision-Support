"""
AgriSell AI - Main Flask Application Server
Exposes REST API endpoints coordinating independent AI agents, orchestrator pipeline,
decision engine, and dynamic notification engine.
"""

import os
import json
import uuid
from datetime import datetime
from flask import Flask, request, jsonify
from flask_cors import CORS

from market_agent import MarketAgent
from weather_agent import WeatherAgent
from storage_agent import StorageAgent
from logistics_agent import LogisticsAgent
from decision_agent import DecisionAgent
from language_agent import LanguageAgent
from notification_engine import NotificationEngine

app = Flask(__name__)
CORS(app)

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def load_json(filename: str):
    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)

# Instantiate Agents
market_agent = MarketAgent()
weather_agent = WeatherAgent()
storage_agent = StorageAgent()
logistics_agent = LogisticsAgent()
decision_agent = DecisionAgent()
language_agent = LanguageAgent()
notification_engine = NotificationEngine()

# In-memory Decision History Store
SAVED_DECISIONS = [
    {
        "id": "dec_sample_01",
        "date": "2026-09-15 10:30 AM",
        "crop": "Chilli",
        "quantity": 1200,
        "location": "Guntur",
        "recommendation": "SELL AT ANOTHER MARKET",
        "market": "Hyderabad Bowenpally",
        "expectedReturn": 248000,
        "expectedPrice": 215,
        "risk": "MEDIUM",
        "notes": "Higher terminal rate in Hyderabad outweighed ₹4,200 freight cost."
    },
    {
        "id": "dec_sample_02",
        "date": "2026-09-12 04:15 PM",
        "crop": "Rice",
        "quantity": 5000,
        "location": "Vijayawada",
        "recommendation": "STORE & SELL LATER",
        "market": "Vijayawada Dry Godown",
        "expectedReturn": 185000,
        "expectedPrice": 38,
        "risk": "LOW",
        "notes": "Low spoilage risk for paddy; stored for 30-day price appreciation."
    }
]

# Track previous state for delta-based alert triggers
PREVIOUS_STATE = {}

@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "service": "AgriSell AI Backend Agent Orchestrator",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/crops", methods=["GET"])
def get_crops():
    crops = load_json("crops.json")
    return jsonify(crops)

@app.route("/api/markets", methods=["GET"])
def get_markets():
    markets_data = load_json("markets.json")
    return jsonify(markets_data)

@app.route("/api/weather", methods=["GET"])
def get_weather():
    location = request.args.get("location", "ongole").lower()
    weather_data = load_json("weather.json")["weatherProfiles"]
    profile = weather_data.get(location, weather_data.get("ongole"))
    return jsonify(profile)

@app.route("/api/locations", methods=["GET"])
def get_locations():
    locations = load_json("locations.json")
    return jsonify(locations)

@app.route("/api/translations", methods=["GET"])
def get_translations():
    lang = request.args.get("lang", "en")
    translations = load_json("translations.json")
    return jsonify(translations.get(lang, translations["en"]))

@app.route("/api/analyze", methods=["POST"])
def analyze_harvest():
    """
    Main Agentic Pipeline Orchestrator:
    Farmer Input -> Dynamic Data Engine -> (Market, Weather, Storage, Logistics Agents) ->
    Decision Engine -> Language Agent -> Notification Engine -> JSON Response
    """
    global PREVIOUS_STATE
    data = request.get_json() or {}

    crop_name = data.get("crop", "Tomato")
    custom_crop = data.get("customCropName", "")
    quantity = float(data.get("quantity", 1000))
    location = data.get("location", "Ongole")
    harvest_date = data.get("harvestDate", datetime.today().strftime("%Y-%m-%d"))
    storage_avail = bool(data.get("storageAvailable", True))
    storage_cap = float(data.get("storageCapacity", 1500))
    storage_cost = float(data.get("storageCostPerDay", 100))
    urgency = data.get("urgency", "few_days")
    language = data.get("language", "en")
    target_price = float(data.get("targetPrice", 0))
    weights = data.get("weights", {
        "market": 35.0,
        "demand": 20.0,
        "weather": 15.0,
        "logistics": 15.0,
        "storage": 15.0
    })

    # Step 1: Run Market Agent
    market_res = market_agent.analyze(
        crop_name=crop_name,
        location_name=location,
        quantity=quantity,
        custom_crop_name=custom_crop
    )

    # Step 2: Run Weather Agent
    weather_res = weather_agent.analyze(
        crop_name=crop_name,
        location_name=location,
        harvest_date_str=harvest_date
    )

    # Step 3: Run Storage Agent
    storage_res = storage_agent.analyze(
        crop_name=crop_name,
        quantity=quantity,
        storage_available=storage_avail,
        storage_capacity=storage_cap,
        storage_cost_per_day=storage_cost,
        harvest_date_str=harvest_date,
        expected_future_price=market_res.get("expectedFuturePrice", 0.0),
        current_local_price=market_res.get("localPrice", 0.0)
    )

    # Step 4: Run Logistics Agent
    logistics_res = logistics_agent.analyze(
        crop_name=crop_name,
        quantity=quantity,
        location_name=location,
        weather_risk=weather_res.get("weatherRisk", "LOW")
    )

    # Step 5: Synthesize in Decision Engine
    decision_res = decision_agent.evaluate(
        market_res=market_res,
        weather_res=weather_res,
        storage_res=storage_res,
        logistics_res=logistics_res,
        quantity=quantity,
        urgency=urgency,
        weights=weights
    )

    winning = decision_res["winningOption"]

    # Step 6: Generate Explainable AI Reasoning & Voice Script
    explanation_res = language_agent.generate_explanation(
        winning_option=winning,
        market_res=market_res,
        weather_res=weather_res,
        storage_res=storage_res,
        logistics_res=logistics_res,
        crop_name=market_res["crop"],
        quantity=quantity,
        language=language
    )

    # Step 7: Evaluate Dynamic Alerts & Notifications
    notifications = notification_engine.generate_alerts_and_notifications(
        crop_name=market_res["crop"],
        location_name=location,
        quantity=quantity,
        target_price=target_price,
        market_res=market_res,
        weather_res=weather_res,
        storage_res=storage_res,
        logistics_res=logistics_res,
        decision_res=decision_res,
        previous_state=PREVIOUS_STATE
    )

    # Update previous state cache
    PREVIOUS_STATE = {
        "crop": crop_name,
        "location": location,
        "quantity": quantity,
        "winningId": winning["id"],
        "localPrice": market_res["localPrice"]
    }

    # Auto-record checked crop decision directly into SAVED_DECISIONS
    auto_dec = {
        "id": f"dec_auto_{crop_name.lower()}_{location.lower()}",
        "date": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        "crop": market_res.get("crop", crop_name),
        "quantity": quantity,
        "location": location,
        "recommendation": winning["title"],
        "actionId": winning["id"],
        "market": winning.get("subtitle", location),
        "expectedReturn": winning["netReturn"],
        "expectedPrice": winning["pricePerKg"],
        "risk": winning["risk"],
        "confidence": decision_res["confidence"],
        "reasoning": explanation_res["explanation"],
        "actionPlan": decision_res["actionPlan"],
        "notes": f"Auto-recorded when checking {crop_name}."
    }
    existing_idx = next((i for i, d in enumerate(SAVED_DECISIONS) if d.get("crop") == auto_dec["crop"] and d.get("location") == auto_dec["location"]), None)
    if existing_idx is not None:
        SAVED_DECISIONS[existing_idx] = auto_dec
    else:
        SAVED_DECISIONS.insert(0, auto_dec)

    # Format alerts for banner display
    alerts = []
    if weather_res.get("weatherRisk") == "HIGH":
        alerts.append({
            "type": "danger",
            "title": "HIGH WEATHER RISK",
            "message": f"High rain probability ({weather_res['rainProbability']}) in {location}. Highway transport and unprotected field storage risk is elevated."
        })
    if market_res.get("demand") in ["HIGH", "VERY HIGH"]:
        alerts.append({
            "type": "success",
            "title": "HIGH MARKET DEMAND",
            "message": f"Demand for {market_res['crop']} is currently high across regional mandis."
        })
    if storage_avail and storage_cap < quantity:
        alerts.append({
            "type": "warning",
            "title": "STORAGE CAPACITY EXCEEDED",
            "message": f"Harvest quantity ({quantity:,.0f} kg) exceeds verified capacity ({storage_cap:,.0f} kg)."
        })

    response_payload = {
        "market": market_res,
        "weather": weather_res,
        "storage": storage_res,
        "logistics": logistics_res,
        "options": decision_res["allOptions"],
        "recommendation": {
            "action": winning["title"],
            "actionId": winning["id"],
            "subtitle": winning.get("subtitle", ""),
            "expectedPrice": winning["pricePerKg"],
            "expectedNetReturn": winning["netReturn"],
            "risk": winning["risk"],
            "confidence": decision_res["confidence"],
            "actionPlan": decision_res["actionPlan"]
        },
        "reasoning": explanation_res["explanation"],
        "voiceScript": explanation_res["voiceScript"],
        "alerts": alerts,
        "notifications": notifications,
        "savedDecisions": SAVED_DECISIONS,
        "weights": weights,
        "timestamp": datetime.now().isoformat(),
        "status": "SUCCESS"
    }

    return jsonify(response_payload)

@app.route("/api/decision", methods=["POST"])
def recalculate_decision():
    """
    Rapid re-scoring of decisions when farmer adjusts weight sliders or urgency
    without re-evaluating external market/weather data.
    """
    data = request.get_json() or {}
    market_res = data.get("market", {})
    weather_res = data.get("weather", {})
    storage_res = data.get("storage", {})
    logistics_res = data.get("logistics", {})
    quantity = float(data.get("quantity", 1000))
    urgency = data.get("urgency", "few_days")
    weights = data.get("weights", {})
    language = data.get("language", "en")
    crop_name = data.get("crop", "Tomato")

    decision_res = decision_agent.evaluate(
        market_res=market_res,
        weather_res=weather_res,
        storage_res=storage_res,
        logistics_res=logistics_res,
        quantity=quantity,
        urgency=urgency,
        weights=weights
    )

    winning = decision_res["winningOption"]

    explanation_res = language_agent.generate_explanation(
        winning_option=winning,
        market_res=market_res,
        weather_res=weather_res,
        storage_res=storage_res,
        logistics_res=logistics_res,
        crop_name=crop_name,
        quantity=quantity,
        language=language
    )

    return jsonify({
        "options": decision_res["allOptions"],
        "recommendation": {
            "action": winning["title"],
            "actionId": winning["id"],
            "subtitle": winning.get("subtitle", ""),
            "expectedPrice": winning["pricePerKg"],
            "expectedNetReturn": winning["netReturn"],
            "risk": winning["risk"],
            "confidence": decision_res["confidence"],
            "actionPlan": decision_res["actionPlan"]
        },
        "reasoning": explanation_res["explanation"],
        "voiceScript": explanation_res["voiceScript"],
        "weights": weights
    })

@app.route("/api/decisions", methods=["GET"])
def list_decisions():
    return jsonify(SAVED_DECISIONS)

@app.route("/api/decisions", methods=["POST"])
def save_decision():
    data = request.get_json() or {}
    new_dec = {
        "id": f"dec_{uuid.uuid4().hex[:8]}",
        "date": datetime.now().strftime("%Y-%m-%d %I:%M %p"),
        "crop": data.get("crop", "Crop"),
        "quantity": float(data.get("quantity", 1000)),
        "location": data.get("location", "Local"),
        "recommendation": data.get("recommendation", "SELL NOW"),
        "actionId": data.get("actionId", ""),
        "market": data.get("market", "Local Mandi"),
        "expectedReturn": float(data.get("expectedReturn", 0)),
        "expectedPrice": float(data.get("expectedPrice", 0)),
        "risk": data.get("risk", "LOW"),
        "confidence": float(data.get("confidence", 80)),
        "reasoning": data.get("reasoning", ""),
        "actionPlan": data.get("actionPlan", []),
        "notes": data.get("notes", "Saved from AgriSell AI decision run.")
    }
    SAVED_DECISIONS.insert(0, new_dec)
    return jsonify({"status": "SUCCESS", "savedDecision": new_dec}), 201

@app.route("/api/decisions/<dec_id>", methods=["DELETE"])
def delete_decision(dec_id):
    global SAVED_DECISIONS
    SAVED_DECISIONS = [d for d in SAVED_DECISIONS if d["id"] != dec_id]
    return jsonify({"status": "DELETED", "id": dec_id})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
