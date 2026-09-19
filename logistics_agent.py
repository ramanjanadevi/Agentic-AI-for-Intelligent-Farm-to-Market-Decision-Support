"""
AgriSell AI - Logistics Agent
Evaluates route distances, vehicle tonnage classes, dynamic fuel & freight rates,
travel transit hours, and net mandi realisations for nearby markets.
"""

import json
import os
from typing import Dict, Any, List

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def load_json(filename: str):
    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)

from market_agent import get_crop_market_multiplier

class LogisticsAgent:
    def __init__(self):
        self.crops = {c["id"]: c for c in load_json("crops.json")}
        self.markets_data = load_json("markets.json")
        self.markets_list = self.markets_data["markets"]
        self.distances = self.markets_data["distances"]

    def analyze(
        self,
        crop_name: str,
        quantity: float,
        location_name: str,
        weather_risk: str = "LOW"
    ) -> Dict[str, Any]:
        crop_key = crop_name.lower().replace(" ", "_")
        crop_info = self.crops.get(crop_key, {})
        base_price = float(crop_info.get("basePrice", 25.0))
        transport_sensitivity = crop_info.get("transportSensitivity", "Medium")

        loc_key = location_name.lower().replace(" ", "_")
        loc_distances = self.distances.get(loc_key, {})

        # Tonnage vehicle classification & rate adjustment
        # Small vehicle (<800kg): mini truck / auto rate ~ ₹0.015 per km-kg (min charge ₹600)
        # Medium vehicle (800-2500kg): pick-up truck ~ ₹0.011 per km-kg (min charge ₹1200)
        # Heavy truck (>2500kg): 6-wheeler / 10-wheeler ~ ₹0.0085 per km-kg (min charge ₹2200)
        if quantity < 800:
            vehicle_type = "Mini Light Commercial Vehicle (Tata Ace / Auto)"
            base_rate = 0.014
            min_charge = 500.0
        elif quantity <= 2500:
            vehicle_type = "Medium Pickup Freight (Bolero / 14ft Truck)"
            base_rate = 0.011
            min_charge = 1100.0
        else:
            vehicle_type = "Heavy Commercial Freight (6-Wheeler / 10-Ton Truck)"
            base_rate = 0.0085
            min_charge = 2000.0

        routes = []
        best_net_market = None
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

            # Compute route-specific transport cost
            if dist_km <= 15:
                transport_cost = round(min(min_charge, quantity * 0.5), 2)
            else:
                raw_transport = dist_km * quantity * base_rate
                transport_cost = round(max(min_charge, raw_transport), 2)

            m_mult = get_crop_market_multiplier(mkt, crop_name, crop_info.get("category", "General"))
            mkt_price = round(base_price * m_mult, 2)
            gross_revenue = round(quantity * mkt_price, 2)

            # In-transit transit spoilage (rough roads + transit hours + perishable sensitivity)
            sens_spoil_factor = 0.003 if transport_sensitivity == "High" else 0.001 if transport_sensitivity == "Medium" else 0.0002
            transit_spoilage_loss = round(gross_revenue * (sens_spoil_factor * transit_hours), 2)

            # Long-distance transit decay for highly perishable produce (e.g. Tomato, Banana, Grapes, Okra > 160km)
            is_perishable = crop_info.get("category", "").lower() in ["vegetables", "fruits"] or transport_sensitivity == "High"
            if is_perishable and dist_km > 160:
                perish_decay = round(gross_revenue * min(0.12, (dist_km - 160) * 0.0006), 2)
                transit_spoilage_loss += perish_decay

            net_return = round(gross_revenue - transport_cost - transit_spoilage_loss, 2)

            # Route composite risk
            if weather_risk == "HIGH" and dist_km > 100:
                composite_risk = "HIGH"
            elif road_risk == "High" or (weather_risk == "MEDIUM" and dist_km > 150):
                composite_risk = "MEDIUM"
            else:
                composite_risk = road_risk

            route_detail = {
                "marketId": mkt["id"],
                "marketName": mkt_name,
                "city": mkt["city"],
                "distanceKm": dist_km,
                "transitHours": transit_hours,
                "vehicleType": vehicle_type,
                "transportCost": transport_cost,
                "pricePerKg": mkt_price,
                "grossRevenue": gross_revenue,
                "transitSpoilage": transit_spoilage_loss,
                "netReturn": net_return,
                "transportRisk": composite_risk
            }
            routes.append(route_detail)

            # Check if best (excluding hyper-local to find distinct markets)
            if net_return > highest_net_return:
                highest_net_return = net_return
                best_net_market = route_detail

        # Sort routes by distance
        routes.sort(key=lambda r: r["distanceKm"])

        return {
            "vehicleType": vehicle_type,
            "bestLogisticsMarket": best_net_market["city"] if best_net_market else location_name,
            "bestLogisticsMarketDetails": best_net_market,
            "routes": routes,
            "status": "COMPLETED ✓"
        }
