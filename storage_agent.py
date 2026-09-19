"""
AgriSell AI - Storage Agent
Evaluates warehouse and cold-storage feasibility, accumulated holding costs,
biological shelf life, spoilage curves, and net profitability of holding produce.
"""

import json
import os
from datetime import datetime, date
from typing import Dict, Any

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

def load_json(filename: str):
    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
        return json.load(f)

class StorageAgent:
    def __init__(self):
        self.crops = {c["id"]: c for c in load_json("crops.json")}
        self.storage_config = load_json("storage.json")

    def analyze(
        self,
        crop_name: str,
        quantity: float,
        storage_available: bool,
        storage_capacity: float,
        storage_cost_per_day: float,
        harvest_date_str: str = "",
        expected_future_price: float = 0.0,
        current_local_price: float = 0.0
    ) -> Dict[str, Any]:
        crop_key = crop_name.lower().replace(" ", "_")
        crop_info = self.crops.get(crop_key, {})

        storage_life_days = int(crop_info.get("storageLifeDays", 14))
        base_spoilage_rate = float(crop_info.get("spoilageRate", 0.02))
        rec_type = crop_info.get("recommendedStorageType", "Standard Dry Storage")

        # Elapsed days check
        days_elapsed = 0
        if harvest_date_str:
            try:
                h_date = datetime.strptime(harvest_date_str, "%Y-%m-%d").date()
                days_elapsed = max(0, (date.today() - h_date).days)
            except Exception:
                days_elapsed = 0

        remaining_shelf_life = max(1, storage_life_days - days_elapsed)

        # If storage unavailable
        if not storage_available:
            return {
                "storageAvailable": False,
                "isFeasible": False,
                "feasibilityReason": "No on-site or contracted storage facility available.",
                "storageCapacity": 0,
                "requiredQuantity": quantity,
                "storageLife": f"{remaining_shelf_life} days",
                "recommendedDurationDays": 0,
                "storageCost": 0.0,
                "expectedSpoilagePercent": 0,
                "spoilageLoss": 0.0,
                "futureSellingValue": 0.0,
                "netStorageGain": 0.0,
                "profitabilityStatus": "NOT FEASIBLE",
                "storageType": "None",
                "status": "COMPLETED ✓"
            }

        # Check capacity vs quantity
        if storage_capacity < quantity:
            shortage = quantity - storage_capacity
            return {
                "storageAvailable": True,
                "isFeasible": False,
                "feasibilityReason": f"Storage capacity ({storage_capacity:,.0f} kg) is smaller than harvest ({quantity:,.0f} kg). Shortage of {shortage:,.0f} kg.",
                "storageCapacity": storage_capacity,
                "requiredQuantity": quantity,
                "storageLife": f"{remaining_shelf_life} days",
                "recommendedDurationDays": 0,
                "storageCost": 0.0,
                "expectedSpoilagePercent": 0,
                "spoilageLoss": 0.0,
                "futureSellingValue": 0.0,
                "netStorageGain": 0.0,
                "profitabilityStatus": "INSUFFICIENT CAPACITY",
                "storageType": rec_type,
                "status": "COMPLETED ✓"
            }

        # Recommended holding window:
        # Perishables (Tomato, Okra, Banana): maximum 3-5 days
        # Semi-perishables (Onion, Potato): 14-21 days
        # Non-perishables (Grains, Pulses): 30-60 days
        if remaining_shelf_life <= 7:
            rec_duration = min(remaining_shelf_life, 3)
        elif remaining_shelf_life <= 30:
            rec_duration = min(remaining_shelf_life, 10)
        else:
            rec_duration = 21

        total_storage_cost = round(storage_cost_per_day * rec_duration, 2)

        # Expected spoilage over holding duration
        # Compound rate + aging
        spoilage_pct = min(0.35, round(base_spoilage_rate * rec_duration + (days_elapsed * 0.005), 3))
        spoiled_qty = round(quantity * spoilage_pct, 1)
        salable_qty = max(0.0, quantity - spoiled_qty)

        # Economic outcomes
        spoilage_loss_rupees = round(spoiled_qty * (expected_future_price or current_local_price), 2)
        future_gross_revenue = round(salable_qty * expected_future_price, 2)
        # Net value after storage cost & spoilage
        # (Assuming local transport after storage or local delivery)
        net_stored_return = round(future_gross_revenue - total_storage_cost, 2)
        immediate_revenue = round(quantity * current_local_price, 2)
        net_gain_over_immediate = round(net_stored_return - immediate_revenue, 2)

        is_economically_viable = (net_gain_over_immediate > 0) and (spoilage_pct <= 0.18)

        return {
            "storageAvailable": True,
            "isFeasible": True,
            "feasibilityReason": "Facility verified and capacity covers harvest quantity.",
            "storageCapacity": storage_capacity,
            "requiredQuantity": quantity,
            "storageLife": f"{remaining_shelf_life} days",
            "recommendedDurationDays": rec_duration,
            "storageCost": total_storage_cost,
            "expectedSpoilagePercent": round(spoilage_pct * 100, 1),
            "spoiledQuantityKg": spoiled_qty,
            "salableQuantityKg": salable_qty,
            "spoilageLoss": spoilage_loss_rupees,
            "futureSellingValue": future_gross_revenue,
            "netStoredReturn": net_stored_return,
            "netStorageGain": net_gain_over_immediate,
            "profitabilityStatus": "PROFITABLE" if is_economically_viable else "UNPROFITABLE / HIGH SPOILAGE",
            "storageType": rec_type,
            "status": "COMPLETED ✓"
        }
