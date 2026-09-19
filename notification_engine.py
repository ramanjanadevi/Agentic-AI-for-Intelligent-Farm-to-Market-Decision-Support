"""
AgriSell AI - Dynamic Notification & Price Alert Engine
Continuously monitors agents and application state to generate actionable notifications:
Price hikes, target thresholds, market arbitrage opportunities, weather storm warnings,
storage limits, and strategic recommendation shifts.
"""

from typing import Dict, Any, List
from datetime import datetime

class NotificationEngine:
    def __init__(self):
        self.state_cache = {}

    def generate_alerts_and_notifications(
        self,
        crop_name: str,
        location_name: str,
        quantity: float,
        target_price: float,
        market_res: Dict[str, Any],
        weather_res: Dict[str, Any],
        storage_res: Dict[str, Any],
        logistics_res: Dict[str, Any],
        decision_res: Dict[str, Any],
        previous_state: Dict[str, Any] = None
    ) -> List[Dict[str, Any]]:
        notifications = []
        now_str = datetime.now().strftime("%I:%M %p")

        local_price = market_res.get("localPrice", 20.0)
        best_market = market_res.get("bestNearbyMarket", "")
        best_market_price = market_res.get("bestMarketPrice", local_price)
        best_net = market_res.get("bestMarketNetReturn", 0.0)
        local_net = decision_res["allOptions"][0]["netReturn"]
        future_price = market_res.get("expectedFuturePrice", local_price)

        weather_risk = weather_res.get("weatherRisk", "LOW")
        rain_prob = weather_res.get("rainProbabilityVal", 20)

        winning_id = decision_res["winningOption"]["id"]
        winning_title = decision_res["winningOption"]["title"]

        # 1. TARGET PRICE THRESHOLD ALERT
        if target_price and target_price > 0:
            if local_price >= target_price or best_market_price >= target_price:
                achieved_price = max(local_price, best_market_price)
                notifications.append({
                    "id": f"notif_target_{crop_name.lower()}",
                    "type": "TARGET_PRICE_REACHED",
                    "severity": "success",
                    "crop": crop_name,
                    "location": location_name,
                    "title": "🎯 Target Price Reached!",
                    "message": f"{crop_name} reached ₹{achieved_price}/kg, matching or exceeding your target price of ₹{target_price}/kg.",
                    "currentValue": achieved_price,
                    "previousValue": target_price,
                    "timestamp": now_str,
                    "read": False,
                    "action": "VIEW_ANALYSIS"
                })

        # 2. MARKET ARBITRAGE OPPORTUNITY
        arbitrage_gain = best_net - local_net
        if arbitrage_gain > 500 and best_market and best_market.lower() != location_name.lower():
            notifications.append({
                "id": f"notif_opp_{crop_name.lower()}",
                "type": "BETTER_MARKET_OPPORTUNITY",
                "severity": "success",
                "crop": crop_name,
                "location": location_name,
                "title": "🟢 Better Market Opportunity Detected",
                "message": f"{best_market} is offering ₹{best_market_price:,.1f}/kg compared with ₹{local_price:,.1f}/kg locally. After estimated freight costs, your expected additional gain is +₹{arbitrage_gain:,.0f}.",
                "timestamp": now_str,
                "read": False,
                "action": "VIEW_ANALYSIS"
            })

        # 3. WEATHER ADVISORY ALERT
        if weather_risk == "HIGH" or rain_prob >= 60:
            notifications.append({
                "id": f"notif_weather_{crop_name.lower()}",
                "type": "WEATHER_ALERT",
                "severity": "danger",
                "crop": crop_name,
                "location": location_name,
                "title": "🔴 Weather Alert: Heavy Rain Hazard",
                "message": f"{rain_prob}% rain probability detected in {location_name}. Severe risk for open highway transport and unprotected produce storage.",
                "timestamp": now_str,
                "read": False,
                "action": "VIEW_ANALYSIS"
            })

        # 4. STORAGE WARNINGS
        if storage_res.get("storageAvailable"):
            cap = storage_res.get("storageCapacity", 0)
            if cap < quantity:
                notifications.append({
                    "id": f"notif_storage_cap_{crop_name.lower()}",
                    "type": "STORAGE_CAPACITY_WARNING",
                    "severity": "warning",
                    "crop": crop_name,
                    "location": location_name,
                    "title": "🟠 Storage Capacity Warning",
                    "message": f"Your storage capacity ({cap:,.0f} kg) is insufficient for the full harvest of {quantity:,.0f} kg. Excess {quantity - cap:,.0f} kg requires immediate liquidation.",
                    "timestamp": now_str,
                    "read": False,
                    "action": "VIEW_ANALYSIS"
                })
            elif storage_res.get("expectedSpoilagePercent", 0) > 10:
                notifications.append({
                    "id": f"notif_spoilage_{crop_name.lower()}",
                    "type": "SPOILAGE_WARNING",
                    "severity": "warning",
                    "crop": crop_name,
                    "location": location_name,
                    "title": "🟠 High Spoilage Curve",
                    "message": f"Estimated spoilage rate is {storage_res.get('expectedSpoilagePercent')}% during holding. Consider selling sooner to avert spoilage loss.",
                    "timestamp": now_str,
                    "read": False,
                    "action": "VIEW_ANALYSIS"
                })

        # 5. FUTURE PRICE OPPORTUNITY
        if future_price > local_price * 1.15 and storage_res.get("isFeasible"):
            notifications.append({
                "id": f"notif_future_{crop_name.lower()}",
                "type": "POSSIBLE_PRICE_OPPORTUNITY",
                "severity": "info",
                "crop": crop_name,
                "location": location_name,
                "title": "🟡 Future Price Upside Potential",
                "message": f"Forward projections indicate {crop_name} may reach ₹{future_price}/kg in coming weeks. Holding produce may increase gross realization.",
                "timestamp": now_str,
                "read": False,
                "action": "VIEW_ANALYSIS"
            })

        # 6. PRICE TREND NOTIFICATION
        trend = market_res.get("trend", "Stable")
        if trend == "Increasing":
            notifications.append({
                "id": f"notif_price_trend_{crop_name.lower()}",
                "type": "PRICE_INCREASE",
                "severity": "success",
                "crop": crop_name,
                "location": location_name,
                "title": "📈 Mandi Prices Trending Upward",
                "message": f"{crop_name} spot prices are rising in key terminal markets due to tight regional supply.",
                "timestamp": now_str,
                "read": False,
                "action": "VIEW_ANALYSIS"
            })
        elif trend == "Decreasing":
            notifications.append({
                "id": f"notif_price_drop_{crop_name.lower()}",
                "type": "PRICE_DECREASE",
                "severity": "danger",
                "crop": crop_name,
                "location": location_name,
                "title": "📉 Mandi Prices Softening",
                "message": f"{crop_name} wholesale prices are dipping under arrival pressure. Locking in immediate sales prevents further price dilution.",
                "timestamp": now_str,
                "read": False,
                "action": "VIEW_ANALYSIS"
            })

        # 7. RECOMMENDATION SHIFT ALERT (If state changed from previous)
        if previous_state and previous_state.get("winningId"):
            prev_id = previous_state["winningId"]
            if prev_id != winning_id:
                notifications.insert(0, {
                    "id": f"notif_rec_change_{int(datetime.now().timestamp())}",
                    "type": "DECISION_UPDATED",
                    "severity": "info",
                    "crop": crop_name,
                    "location": location_name,
                    "title": "🔔 Recommendation Updated",
                    "message": f"Market dynamics or inputs shifted. AgriSell AI now recommends: {winning_title}.",
                    "timestamp": now_str,
                    "read": False,
                    "action": "VIEW_ANALYSIS"
                })

        return notifications
