"""
AgriSell AI - Market Agent
Calculates local market prices, nearby market differentials, demand levels,
price trends, price volatility, and expected future prices.
"""

import json
import os
import math
from typing import Dict, Any, List

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def load_json(filename: str):
    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)

def get_crop_market_multiplier(mkt, crop_name, category):
    base_m = mkt.get("priceMultiplier", 1.0)
    mkt_city = mkt.get("city", "").lower()
    c_lower = crop_name.lower()
    cat_lower = category.lower()

    # 1. GUNTUR: World-renowned hub for Chilli, Spices, and Cotton
    if "guntur" in mkt_city:
        if "chilli" in c_lower or "spices" in cat_lower:
            return 1.35  # Guntur Mirchi Yard offers top premium for Chilli
        if "cotton" in c_lower or "turmeric" in c_lower:
            return 1.30
        return 1.14

    # 2. VIJAYAWADA (Gollapudi Mega Wholesale Market): Top hub for Vegetables & Commercial produce
    if "vijayawada" in mkt_city:
        if cat_lower in ["vegetables", "fruits"] or c_lower in [
            "tomato", "onion", "potato", "brinjal", "okra", "cabbage", "cauliflower", "carrot"
        ]:
            return 1.28  # Premier vegetable mandi
        return 1.20

    # 3. NELLORE: Premier coastal delta hub for Rice/Paddy and Black Gram
    if "nellore" in mkt_city:
        if "rice" in c_lower or "pulses" in cat_lower or c_lower in ["black_gram", "green_gram", "red_gram"]:
            return 1.26  # Nellore grain & produce yard premium
        return 1.10

    # 4. ANANTAPUR & KURNOOL: Leading hub for Groundnut, Oilseeds, and Banana
    if "anantapur" in mkt_city or "kurnool" in mkt_city:
        if c_lower in ["groundnut", "sunflower", "sesame", "banana", "maize"] or "oilseeds" in cat_lower:
            return 1.26  # Top groundnut & oilseeds market
        return 1.08

    # 5. HYDERABAD (Metropolitan terminal market): High for fruits/cash crops, but moderate for regional staples
    if "hyderabad" in mkt_city:
        if c_lower in ["grapes", "mango", "garlic", "soybean"]:
            return 1.32
        elif c_lower in ["tomato", "cabbage", "okra"]:
            return 1.18  # High supply in terminal market prevents extreme premiums
        return 1.22

    return base_m

class MarketAgent:
    def __init__(self):
        self.crops = {c["id"]: c for c in load_json("crops.json")}
        self.markets_data = load_json("markets.json")
        self.markets_list = self.markets_data["markets"]
        self.distances = self.markets_data["distances"]

    def analyze(self, crop_name: str, location_name: str, quantity: float, custom_crop_name: str = "") -> Dict[str, Any]:
        crop_key = crop_name.lower().replace(" ", "_")
        crop_info = self.crops.get(crop_key)

        # Handle custom crop
        if not crop_info or crop_key == "other":
            display_name = custom_crop_name.strip() if custom_crop_name else "Custom Crop"
            category = "General"
            base_price = 28.0
            demand = "Medium"
            price_trend = "Increasing"
            future_price = round(base_price * 1.15, 2)
            volatility = 12.0
            spoilage_rate = 0.02
        else:
            display_name = crop_info["name"]
            category = crop_info.get("category", "General")
            base_price = float(crop_info["basePrice"])
            demand = crop_info.get("demand", "Medium")
            price_trend = crop_info.get("priceTrend", "Stable")
            future_price = float(crop_info.get("futurePrice", base_price * 1.1))
            spoilage_rate = float(crop_info.get("spoilageRate", 0.01))
            volatility = 18.5 if crop_info.get("weatherSensitivity") == "High" else 8.2

        loc_key = location_name.lower().replace(" ", "_")
        loc_distances = self.distances.get(loc_key, {})

        # Compute local market price based on location
        local_multiplier = 1.0
        for mkt in self.markets_list:
            if mkt["city"].lower() in loc_key or loc_key in mkt["city"].lower():
                local_multiplier = get_crop_market_multiplier(mkt, display_name, category)
                break

        local_price = round(base_price * local_multiplier, 2)

        # Compute prices across all nearby reachable markets
        market_quotes = []
        best_market = None
        highest_net_return = -1e9

        for mkt in self.markets_list:
            mkt_name = mkt["name"]
            dist_info = loc_distances.get(mkt_name, {
                "distanceKm": 180,
                "transitHours": 4.0,
                "roadRisk": "Medium"
            })
            dist_km = dist_info["distanceKm"]
            transit_hours = dist_info["transitHours"]
            road_risk = dist_info["roadRisk"]

            m_mult = get_crop_market_multiplier(mkt, display_name, category)
            m_price = round(base_price * m_mult, 2)

            # Transport cost calculation based on weight & distance
            base_rate = mkt.get("baseTransportRatePerKmPerKg", 0.011)
            # Truck load economy of scale: cost per kg decreases slightly for large tonnage
            scale_factor = 1.0 if quantity <= 1000 else 0.85 if quantity <= 5000 else 0.75
            transport_cost = round(dist_km * quantity * base_rate * scale_factor, 2)
            if dist_km <= 15:
                transport_cost = round(quantity * 0.4, 2)  # Local minimal cartage

            gross_revenue = round(quantity * m_price, 2)

            # Perishable distance degradation for long transit (>160km)
            is_perishable = category.lower() in ["vegetables", "fruits"] or crop_info.get("transportSensitivity") == "High"
            transit_decay = 0.0
            if is_perishable and dist_km > 160:
                transit_decay = round(gross_revenue * min(0.12, (dist_km - 160) * 0.0006), 2)

            net_return = round(gross_revenue - transport_cost - transit_decay, 2)

            quote = {
                "marketId": mkt["id"],
                "marketName": mkt_name,
                "city": mkt["city"],
                "tier": mkt["tier"],
                "pricePerKg": m_price,
                "distanceKm": dist_km,
                "transitHours": transit_hours,
                "roadRisk": road_risk,
                "transportCost": transport_cost,
                "transitDecay": transit_decay,
                "grossRevenue": gross_revenue,
                "netReturn": net_return,
                "demand": "Very High" if m_mult >= 1.25 else "High" if m_mult >= 1.12 else "Normal"
            }
            market_quotes.append(quote)

            if dist_km > 15 and net_return > highest_net_return:
                highest_net_return = net_return
                best_market = quote

        # Fallback if no remote market found
        if not best_market and market_quotes:
            best_market = market_quotes[0]

        # 7-day price history simulation
        history = []
        base_fluctuation = [-2.5, -1.8, -0.9, 0.4, 1.2, 0.8, 0.0]
        if price_trend == "Decreasing":
            base_fluctuation = [3.0, 2.1, 1.5, 0.8, 0.2, -0.4, 0.0]
        elif price_trend == "Stable":
            base_fluctuation = [-0.5, 0.3, -0.2, 0.4, -0.1, 0.2, 0.0]

        for i, delta in enumerate(base_fluctuation):
            day_price = max(5.0, round(local_price + delta, 1))
            history.append({
                "day": f"Day {i-6 if i < 6 else 'Today'}",
                "price": day_price,
                "projected": False
            })

        # Projections for Day +3 and Day +7
        history.append({"day": "+3 Days", "price": round(local_price * 1.08, 1) if price_trend == "Increasing" else round(local_price * 0.95, 1), "projected": True})
        history.append({"day": "+7 Days", "price": round(future_price, 1), "projected": True})

        return {
            "crop": display_name,
            "localPrice": local_price,
            "bestNearbyMarket": best_market["city"] if best_market else location_name,
            "bestMarketFullName": best_market["marketName"] if best_market else "",
            "bestMarketPrice": best_market["pricePerKg"] if best_market else local_price,
            "bestMarketNetReturn": best_market["netReturn"] if best_market else round(local_price * quantity, 2),
            "demand": demand.upper(),
            "trend": price_trend,
            "volatility": f"{volatility}%",
            "expectedFuturePrice": round(future_price, 2),
            "marketQuotes": market_quotes,
            "priceHistory": history,
            "status": "COMPLETED ✓"
        }
