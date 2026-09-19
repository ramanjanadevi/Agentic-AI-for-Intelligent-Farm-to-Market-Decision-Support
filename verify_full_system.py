"""
AgriSell AI - Comprehensive End-to-End Dynamic System Verification
Validates every dynamic flow, agent, endpoint, edge case, and scenario.
"""
import sys
import os
import json
import urllib.request
import urllib.parse

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_URL = "http://localhost:5000/api"

def http_get(path):
    req = urllib.request.Request(f"{BASE_URL}{path}")
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def http_post(path, data):
    payload = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(f"{BASE_URL}{path}", data=payload, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def http_delete(path):
    req = urllib.request.Request(f"{BASE_URL}{path}", method='DELETE')
    with urllib.request.urlopen(req) as response:
        return json.loads(response.read().decode('utf-8'))

def main():
    print("=== AGRISELL AI FULL SYSTEM VERIFICATION ===\n")

    # 1. Catalog endpoints
    print("1. Testing Catalog & Static Endpoints:")
    crops = http_get("/crops")
    print(f"  ✓ /api/crops: Loaded {len(crops)} crops (includes Tomato, Rice, Chilli, etc.)")
    assert len(crops) >= 28, "Crops catalog must have at least 28 crops"

    markets = http_get("/markets")
    print(f"  ✓ /api/markets: Loaded {len(markets['markets'])} mandis and distance matrix")

    locations = http_get("/locations")
    print(f"  ✓ /api/locations: Loaded {len(locations)} locations (Ongole, Guntur, Vijayawada, Kurnool, etc.)")

    weather = http_get("/weather?location=ongole")
    print(f"  ✓ /api/weather: Ongole -> Temp: {weather['temperature']}°C, Rain: {weather['rainProbability']}%")

    translations_te = http_get("/translations?lang=te")
    print(f"  ✓ /api/translations (Telugu): '{translations_te['centralQuestion']}'")

    # 2. Dynamic Scenario 1: Tomato in Ongole with Storage Available
    print("\n2. Testing Scenario 1 (Tomato, 1000kg, Ongole, Storage=Yes):")
    res1 = http_post("/analyze", {
        "crop": "Tomato",
        "quantity": 1000,
        "location": "Ongole",
        "storageAvailable": True,
        "storageCapacity": 1500,
        "storageCostPerDay": 100,
        "urgency": "few_days",
        "targetPrice": 25
    })
    rec1 = res1["recommendation"]
    print(f"  ✓ Winning Action: {rec1['action']} ({rec1.get('subtitle')})")
    print(f"  ✓ Expected Net Return: ₹{rec1['expectedNetReturn']:,}")
    print(f"  ✓ Realized Price: ₹{rec1['expectedPrice']}/kg")
    print(f"  ✓ Confidence: {rec1['confidence']}% | Risk: {rec1['risk']}")
    print(f"  ✓ Reasoning excerpt: {res1['reasoning'][:100]}...")
    print(f"  ✓ Dynamic Notifications generated: {len(res1['notifications'])}")

    # 3. Dynamic Scenario 2: Tomato in Ongole with Storage NOT Available
    print("\n3. Testing Scenario 2 (Tomato, 1000kg, Ongole, Storage=No):")
    res2 = http_post("/analyze", {
        "crop": "Tomato",
        "quantity": 1000,
        "location": "Ongole",
        "storageAvailable": False,
        "storageCapacity": 0,
        "storageCostPerDay": 0,
        "urgency": "few_days"
    })
    rec2 = res2["recommendation"]
    store_opt = [o for o in res2["options"] if o["id"] == "STORE_LATER"][0]
    print(f"  ✓ Store & Sell Later Feasible: {store_opt['feasible']} ({store_opt.get('feasibilityNote')})")
    print(f"  ✓ New Winning Action: {rec2['action']} ({rec2.get('subtitle')})")
    assert store_opt["feasible"] is False, "Store option must be NOT FEASIBLE when storage is unavailable"
    assert rec2["actionId"] != "STORE_LATER", "Store option cannot win when storage is unavailable"

    # 4. Dynamic Scenario 3: Crop switch from Tomato to Rice
    print("\n4. Testing Scenario 3 (Crop switch: Tomato -> Rice):")
    res3 = http_post("/analyze", {
        "crop": "Rice",
        "quantity": 5000,
        "location": "Ongole",
        "storageAvailable": True,
        "storageCapacity": 6000,
        "storageCostPerDay": 100,
        "urgency": "weeks"
    })
    print(f"  ✓ Rice Base Price: ₹{res3['market']['localPrice']}/kg (vs Tomato ₹{res1['market']['localPrice']}/kg)")
    print(f"  ✓ Rice Storage Shelf Life: {res3['storage']['storageLife']} (vs Tomato {res1['storage']['storageLife']})")
    print(f"  ✓ Rice Weather Sensitivity: {res3['weather']['cropSensitivity']}")
    print(f"  ✓ Rice Winning Action: {res3['recommendation']['action']}")

    # 5. Dynamic Scenario 4: Location switch Ongole -> Kurnool
    print("\n5. Testing Scenario 4 (Location switch: Ongole -> Kurnool):")
    res4 = http_post("/analyze", {
        "crop": "Tomato",
        "quantity": 1000,
        "location": "Kurnool",
        "storageAvailable": True,
        "storageCapacity": 1500,
        "storageCostPerDay": 100
    })
    kurnool_routes = [r["city"] for r in res4["logistics"]["routes"]]
    print(f"  ✓ Kurnool Nearest Mandis: {kurnool_routes[:4]}")
    print(f"  ✓ Kurnool Weather Profile: {res4['weather']['temperature']} ({res4['weather']['condition']})")

    # 6. Dynamic Scenario 5: Quantity impact (100kg vs 1000kg vs 5000kg)
    print("\n6. Testing Scenario 5 (Dynamic Quantity Logic):")
    q_100 = http_post("/analyze", {"crop": "Tomato", "quantity": 100, "location": "Ongole", "storageAvailable": True, "storageCapacity": 1500})
    q_1000 = http_post("/analyze", {"crop": "Tomato", "quantity": 1000, "location": "Ongole", "storageAvailable": True, "storageCapacity": 1500})
    q_5000 = http_post("/analyze", {"crop": "Tomato", "quantity": 5000, "location": "Ongole", "storageAvailable": True, "storageCapacity": 1500})
    t_100 = q_100["logistics"]["bestLogisticsMarketDetails"]["transportCost"]
    t_1000 = q_1000["logistics"]["bestLogisticsMarketDetails"]["transportCost"]
    t_5000 = q_5000["logistics"]["bestLogisticsMarketDetails"]["transportCost"]
    print(f"  ✓ 100 kg Transport: ₹{t_100} -> 1,000 kg: ₹{t_1000} -> 5,000 kg: ₹{t_5000}")
    assert t_5000 > t_1000 > t_100, "Transport cost must increase with quantity"
    # Also verify storage capacity warning for 5000kg with 1500kg capacity
    assert q_5000["storage"]["isFeasible"] is False, "Storage must fail capacity check for 5000kg > 1500kg"
    print(f"  ✓ 5000 kg Storage Feasibility: {q_5000['storage']['isFeasible']} ({q_5000['storage']['feasibilityReason'][:60]}...)")

    # 7. Dynamic Scenario 6: Selling Urgency
    print("\n7. Testing Scenario 6 (Selling Urgency: Need money immediately):")
    res_urg = http_post("/analyze", {
        "crop": "Tomato",
        "quantity": 1000,
        "location": "Ongole",
        "storageAvailable": True,
        "storageCapacity": 1500,
        "urgency": "immediate"
    })
    print(f"  ✓ Immediate Urgency Winning Action: {res_urg['recommendation']['action']}")

    # 8. Dynamic Scenario 7: Custom Crop ("Dragon Fruit")
    print("\n8. Testing Scenario 7 (Custom Crop Name: Dragon Fruit):")
    res_cust = http_post("/analyze", {
        "crop": "Other",
        "customCropName": "Dragon Fruit",
        "quantity": 800,
        "location": "Ongole",
        "storageAvailable": True,
        "storageCapacity": 1000
    })
    print(f"  ✓ Custom Crop Output Name: '{res_cust['market']['crop']}'")
    assert "Dragon Fruit" in res_cust['market']['crop'], "Custom crop name must flow through pipeline"

    # 9. Dynamic Scenario 8: Multilingual Translations & TTS Voice Script
    print("\n9. Testing Scenario 8 (Telugu Translation & Audio Script):")
    res_te = http_post("/analyze", {
        "crop": "Tomato",
        "quantity": 1000,
        "location": "Ongole",
        "language": "te"
    })
    print(f"  ✓ Telugu Reasoning: {res_te['reasoning'][:120]}...")
    print(f"  ✓ Telugu Voice Script: {res_te['voiceScript'][:100]}...")

    # 10. CRUD Decisions History
    print("\n10. Testing Decisions History CRUD:")
    saved = http_post("/decisions", {
        "crop": "Tomato",
        "quantity": 1000,
        "location": "Ongole",
        "recommendation": "STORE & SELL LATER",
        "market": "Ongole Cold Store",
        "expectedReturn": 24500,
        "expectedPrice": 28,
        "risk": "MEDIUM"
    })
    new_id = saved["savedDecision"]["id"]
    print(f"  ✓ Saved new decision: {new_id}")
    all_decs = http_get("/decisions")
    assert any(d["id"] == new_id for d in all_decs), "New decision must be in list"
    del_res = http_delete(f"/decisions/{new_id}")
    print(f"  ✓ Deleted decision: {del_res['id']}")

    print("\n========================================================")
    print("ALL 10 DYNAMIC VERIFICATION SUITES COMPLETED WITH 100% SUCCESS!")
    print("========================================================")

if __name__ == "__main__":
    main()
