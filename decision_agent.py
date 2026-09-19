"""
AgriSell AI - Decision Agent (AI Decision Engine)
The central intelligence engine that synthesizes Market, Weather, Storage, and Logistics
agents, scores all feasible strategic options, and identifies the optimal choice.
"""

from typing import Dict, Any, List

class DecisionAgent:
    def evaluate(
        self,
        market_res: Dict[str, Any],
        weather_res: Dict[str, Any],
        storage_res: Dict[str, Any],
        logistics_res: Dict[str, Any],
        quantity: float,
        urgency: str = "few_days",
        weights: Dict[str, float] = None
    ) -> Dict[str, Any]:
        if not weights:
            weights = {
                "market": 35.0,
                "demand": 20.0,
                "weather": 15.0,
                "logistics": 15.0,
                "storage": 15.0
            }

        w_market = weights.get("market", 35.0) / 100.0
        w_demand = weights.get("demand", 20.0) / 100.0
        w_weather = weights.get("weather", 15.0) / 100.0
        w_logistics = weights.get("logistics", 15.0) / 100.0
        w_storage = weights.get("storage", 15.0) / 100.0

        local_price = market_res.get("localPrice", 20.0)
        demand_str = market_res.get("demand", "MEDIUM")
        price_trend = market_res.get("trend", "Stable")
        future_price = market_res.get("expectedFuturePrice", local_price * 1.1)

        weather_risk = weather_res.get("weatherRisk", "LOW")
        rain_prob = weather_res.get("rainProbabilityVal", 20)

        storage_feasible = storage_res.get("isFeasible", False)
        storage_life_days = storage_res.get("storageLife", "7 days")

        # -------------------------------------------------------------
        # OPTION A: SELL NOW (Local Mandi)
        # -------------------------------------------------------------
        opt_a_gross = round(quantity * local_price, 2)
        opt_a_transport = round(min(500.0, quantity * 0.35), 2)
        opt_a_storage = 0.0
        opt_a_spoilage = round(opt_a_gross * 0.005, 2)  # minimal immediate handling loss
        opt_a_net = round(opt_a_gross - opt_a_transport - opt_a_storage - opt_a_spoilage, 2)
        opt_a_risk = "LOW"

        # -------------------------------------------------------------
        # OPTION B: SELL AT ANOTHER MARKET (Remote Mandi with best net return)
        # -------------------------------------------------------------
        # Find best remote market from routes (> 20 km)
        routes = logistics_res.get("routes", [])
        remote_routes = [r for r in routes if r["distanceKm"] > 20]
        if not remote_routes:
            remote_routes = routes

        best_remote = max(remote_routes, key=lambda r: r["netReturn"]) if remote_routes else None

        if best_remote:
            opt_b_market_name = best_remote["city"]
            opt_b_mkt_full = best_remote["marketName"]
            opt_b_price = best_remote["pricePerKg"]
            opt_b_gross = best_remote["grossRevenue"]
            opt_b_transport = best_remote["transportCost"]
            opt_b_storage = 0.0
            opt_b_spoilage = best_remote["transitSpoilage"]
            opt_b_net = round(opt_b_gross - opt_b_transport - opt_b_storage - opt_b_spoilage, 2)
            opt_b_risk = best_remote["transportRisk"]
            opt_b_dist = best_remote["distanceKm"]
        else:
            opt_b_market_name = "Regional Hub"
            opt_b_mkt_full = "Regional Mandi"
            opt_b_price = round(local_price * 1.15, 2)
            opt_b_gross = round(quantity * opt_b_price, 2)
            opt_b_transport = round(quantity * 1.8, 2)
            opt_b_storage = 0.0
            opt_b_spoilage = round(opt_b_gross * 0.015, 2)
            opt_b_net = round(opt_b_gross - opt_b_transport - opt_b_storage - opt_b_spoilage, 2)
            opt_b_risk = "MEDIUM"
            opt_b_dist = 120

        # -------------------------------------------------------------
        # OPTION C: STORE & SELL LATER
        # -------------------------------------------------------------
        if storage_feasible:
            opt_c_feasible = True
            opt_c_reason = "Capacity verified; holding period viable."
            opt_c_gross = storage_res.get("futureSellingValue", round(quantity * future_price, 2))
            opt_c_storage = storage_res.get("storageCost", 500.0)
            opt_c_spoilage = storage_res.get("spoilageLoss", 600.0)
            opt_c_transport = round(min(600.0, quantity * 0.4), 2)  # Transport after storage
            opt_c_net = round(opt_c_gross - opt_c_storage - opt_c_spoilage - opt_c_transport, 2)
            opt_c_price = future_price

            # Risk depends on weather & shelf life
            if weather_risk == "HIGH" or storage_res.get("expectedSpoilagePercent", 0) > 12:
                opt_c_risk = "HIGH"
            elif storage_res.get("expectedSpoilagePercent", 0) > 6:
                opt_c_risk = "MEDIUM"
            else:
                opt_c_risk = "LOW"
        else:
            opt_c_feasible = False
            opt_c_reason = storage_res.get("feasibilityReason", "Storage not available.")
            opt_c_gross = 0.0
            opt_c_storage = 0.0
            opt_c_spoilage = 0.0
            opt_c_transport = 0.0
            opt_c_net = -99999.0
            opt_c_price = future_price
            opt_c_risk = "HIGH"

        # -------------------------------------------------------------
        # OPTION D: MONITOR MARKET (Hold 2-3 days on-farm / short wait)
        # -------------------------------------------------------------
        # Short hold option to wait for higher mandi arrivals / price inflection
        short_price_mult = 1.05 if price_trend == "Increasing" else 0.96 if price_trend == "Decreasing" else 1.01
        opt_d_price = round(local_price * short_price_mult, 2)
        opt_d_gross = round(quantity * opt_d_price, 2)
        opt_d_transport = opt_a_transport
        opt_d_storage = round(quantity * 0.15, 2)
        opt_d_spoilage = round(opt_d_gross * 0.02, 2)
        opt_d_net = round(opt_d_gross - opt_d_transport - opt_d_storage - opt_d_spoilage, 2)
        opt_d_risk = "MEDIUM" if weather_risk != "LOW" else "LOW"

        # -------------------------------------------------------------
        # MULTI-FACTOR SCORING
        # -------------------------------------------------------------
        # Normalize Net Returns against base Option A
        base_net = max(1.0, opt_a_net)

        def calc_score(option_key, net_val, risk_str, is_remote=False, is_storage=False):
            if option_key == "STORE_LATER" and not opt_c_feasible:
                return -100.0  # Disqualified

            # Economic Return Score (0 to 100)
            return_ratio = (net_val / base_net)
            fin_score = min(100.0, max(20.0, return_ratio * 70.0))

            # Demand score
            demand_score = 90.0 if demand_str == "HIGH" or demand_str == "VERY HIGH" else 65.0 if demand_str == "MEDIUM" else 40.0

            # Weather resistance score
            weather_score = 90.0 if weather_risk == "LOW" else 60.0 if weather_risk == "MEDIUM" else 30.0
            if is_remote and weather_risk == "HIGH":
                weather_score -= 25.0  # Transporting during heavy rain is penalized

            # Logistics viability score
            if is_remote:
                dist_penalty = min(35.0, opt_b_dist * 0.15)
                logistics_score = max(30.0, 90.0 - dist_penalty)
            else:
                logistics_score = 95.0

            # Storage viability score
            if is_storage:
                storage_score = 90.0 if opt_c_feasible else 0.0
            else:
                storage_score = 70.0

            # Urgency Multipliers
            urgency_mod = 0.0
            if urgency == "immediate":
                if option_key == "SELL_NOW":
                    urgency_mod = +25.0
                elif option_key == "STORE_LATER":
                    urgency_mod = -40.0
                elif option_key == "MONITOR_MARKET":
                    urgency_mod = -20.0
            elif urgency == "weeks":
                if option_key == "STORE_LATER" and opt_c_feasible:
                    urgency_mod = +20.0
                elif option_key == "SELL_NOW":
                    urgency_mod = -10.0

            composite = (
                fin_score * w_market +
                demand_score * w_demand +
                weather_score * w_weather +
                logistics_score * w_logistics +
                storage_score * w_storage +
                urgency_mod
            )
            return round(composite, 2)

        score_a = calc_score("SELL_NOW", opt_a_net, opt_a_risk, False, False)
        score_b = calc_score("OTHER_MARKET", opt_b_net, opt_b_risk, True, False)
        score_c = calc_score("STORE_LATER", opt_c_net, opt_c_risk, False, True)
        score_d = calc_score("MONITOR_MARKET", opt_d_net, opt_d_risk, False, False)

        options = [
            {
                "id": "SELL_NOW",
                "title": "SELL NOW",
                "subtitle": f"Local Market ({market_res.get('bestNearbyMarket', 'Local')})",
                "feasible": True,
                "pricePerKg": local_price,
                "revenue": opt_a_gross,
                "transportCost": opt_a_transport,
                "storageCost": opt_a_storage,
                "spoilageLoss": opt_a_spoilage,
                "netReturn": opt_a_net,
                "risk": opt_a_risk,
                "score": score_a,
                "timeframe": "Today / Immediate",
                "why": "Avoids highway transport charges, zero storage risk, and unlocks immediate cash liquidity."
            },
            {
                "id": "OTHER_MARKET",
                "title": "SELL AT ANOTHER MARKET",
                "subtitle": f"{opt_b_market_name} ({opt_b_dist} km)",
                "feasible": True,
                "pricePerKg": opt_b_price,
                "revenue": opt_b_gross,
                "transportCost": opt_b_transport,
                "storageCost": opt_b_storage,
                "spoilageLoss": opt_b_spoilage,
                "netReturn": opt_b_net,
                "risk": opt_b_risk,
                "score": score_b,
                "timeframe": "Today / Tomorrow",
                "targetCity": opt_b_market_name,
                "targetMandi": opt_b_mkt_full,
                "why": f"Higher wholesale mandi price at {opt_b_market_name} (₹{opt_b_price}/kg vs local ₹{local_price}/kg) outpaces freight transit expenses."
            },
            {
                "id": "STORE_LATER",
                "title": "STORE & SELL LATER",
                "subtitle": f"Recommended hold: {storage_res.get('recommendedDurationDays', 0)} days",
                "feasible": opt_c_feasible,
                "feasibilityNote": opt_c_reason,
                "pricePerKg": opt_c_price,
                "revenue": opt_c_gross,
                "transportCost": opt_c_transport,
                "storageCost": opt_c_storage,
                "spoilageLoss": opt_c_spoilage,
                "netReturn": opt_c_net if opt_c_feasible else 0.0,
                "risk": opt_c_risk,
                "score": score_c,
                "timeframe": f"{storage_res.get('recommendedDurationDays', 0)} days holding",
                "why": f"Capitalizes on expected price increase to ₹{opt_c_price}/kg after holding in {storage_res.get('storageType', 'facility')}." if opt_c_feasible else opt_c_reason
            },
            {
                "id": "MONITOR_MARKET",
                "title": "MONITOR MARKET",
                "subtitle": "Short 2-3 Day Wait",
                "feasible": True,
                "pricePerKg": opt_d_price,
                "revenue": opt_d_gross,
                "transportCost": opt_d_transport,
                "storageCost": opt_d_storage,
                "spoilageLoss": opt_d_spoilage,
                "netReturn": opt_d_net,
                "risk": opt_d_risk,
                "score": score_d,
                "timeframe": "2 - 3 Days",
                "why": "Track mandi arrival volumes and price trajectory for 48 hours before committing to a long route."
            }
        ]

        # Determine winning recommendation based on highest valid score
        feasible_options = [o for o in options if o["feasible"]]
        winning = max(feasible_options, key=lambda x: x["score"])

        # Calculate confidence (65% to 94%)
        sorted_scores = sorted([o["score"] for o in feasible_options], reverse=True)
        if len(sorted_scores) > 1:
            margin = sorted_scores[0] - sorted_scores[1]
            confidence = min(94, max(68, int(72 + margin * 1.5)))
        else:
            confidence = 85

        # Detailed step-by-step action plan
        action_plan = []
        if winning["id"] == "SELL_NOW":
            action_plan = [
                f"Contact local commission agent or APMC yard at {market_res.get('bestNearbyMarket', 'Local')}.",
                f"Pack crop in standard crates/gunny bags to preserve grade quality.",
                f"Deliver early morning (5:00 AM - 8:00 AM) to capture maximum buyer arrival bidding.",
                f"Settle payment on delivery to eliminate receivables and market volatility risk."
            ]
        elif winning["id"] == "OTHER_MARKET":
            action_plan = [
                f"Book a {logistics_res.get('vehicleType', 'commercial truck')} for delivery to {winning.get('targetCity', 'regional hub')}.",
                f"Confirm current spot buying rates at {winning.get('targetMandi', 'APMC Mandi')} before dispatch.",
                f"Use weatherproof tarpaulin covers to protect produce against {weather_risk.lower()} weather risk during the {best_remote.get('transitHours', 3)} hr transit.",
                f"Time arrival for night or pre-dawn auctions to maximize net return of ₹{winning['netReturn']:,.0f}."
            ]
        elif winning["id"] == "STORE_LATER":
            action_plan = [
                f"Inspect harvest batch and reject bruised or over-ripe units to prevent microbial spread.",
                f"Transport to {storage_res.get('storageType', 'verified storage facility')} with proper pre-cooling.",
                f"Set target sell price at ₹{opt_c_price}/kg and monitor daily spot rate alerts.",
                f"Prepare to unload immediately if storage duration approaches {storage_life_days} days."
            ]
        else: # MONITOR_MARKET
            action_plan = [
                "Keep harvest stored in a shaded, well-ventilated on-farm area.",
                "Turn on AgriSell AI target price notifications for real-time market shifts.",
                "Re-evaluate selling decision within 48-72 hours before spoilage accelerates.",
                "Be prepared to sell immediately if weather conditions deteriorate."
            ]

        return {
            "winningOption": winning,
            "allOptions": options,
            "weights": weights,
            "confidence": confidence,
            "risk": winning["risk"],
            "actionPlan": action_plan
        }
