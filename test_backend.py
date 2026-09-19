"""
Quick verification script for backend agents and endpoints
"""
import sys
import os

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

from market_agent import MarketAgent
from weather_agent import WeatherAgent
from storage_agent import StorageAgent
from logistics_agent import LogisticsAgent
from decision_agent import DecisionAgent
from language_agent import LanguageAgent
from notification_engine import NotificationEngine

def run_tests():
    print("Testing Market Agent (Tomato, Ongole, 1000kg)...")
    m_agent = MarketAgent()
    m_res = m_agent.analyze("Tomato", "Ongole", 1000)
    assert m_res["localPrice"] > 0
    assert len(m_res["marketQuotes"]) > 0
    print(f"  -> Local Price: ₹{m_res['localPrice']}/kg, Best Market: {m_res['bestNearbyMarket']} (₹{m_res['bestMarketPrice']}/kg)")

    print("Testing Weather Agent (Tomato, Ongole)...")
    w_agent = WeatherAgent()
    w_res = w_agent.analyze("Tomato", "Ongole")
    assert w_res["weatherRisk"] in ["LOW", "MEDIUM", "HIGH"]
    print(f"  -> Rain Prob: {w_res['rainProbability']}, Weather Risk: {w_res['weatherRisk']}")

    print("Testing Storage Agent (Storage Available: True, Cap: 1500, Qty: 1000)...")
    s_agent = StorageAgent()
    s_res = s_agent.analyze("Tomato", 1000, True, 1500, 100, "", m_res["expectedFuturePrice"], m_res["localPrice"])
    assert s_res["isFeasible"] == True
    print(f"  -> Feasible: {s_res['isFeasible']}, Expected Spoilage: {s_res['expectedSpoilagePercent']}%, Spoilage Loss: ₹{s_res['spoilageLoss']}")

    print("Testing Storage Agent when Storage is NOT Available...")
    s_no = s_agent.analyze("Tomato", 1000, False, 0, 0, "", m_res["expectedFuturePrice"], m_res["localPrice"])
    assert s_no["isFeasible"] == False
    print(f"  -> Feasible when No Storage: {s_no['isFeasible']} ({s_no['feasibilityReason']})")

    print("Testing Logistics Agent...")
    l_agent = LogisticsAgent()
    l_res = l_agent.analyze("Tomato", 1000, "Ongole", w_res["weatherRisk"])
    assert len(l_res["routes"]) > 0
    print(f"  -> Vehicle: {l_res['vehicleType']}, Routes evaluated: {len(l_res['routes'])}")

    print("Testing Decision Engine...")
    d_agent = DecisionAgent()
    d_res = d_agent.evaluate(m_res, w_res, s_res, l_res, 1000)
    winning = d_res["winningOption"]
    print(f"  -> Winning Recommendation: {winning['title']} (Expected Return: ₹{winning['netReturn']:,.0f}, Risk: {winning['risk']})")

    print("Testing Decision Engine with Storage NOT Available...")
    d_res_no_store = d_agent.evaluate(m_res, w_res, s_no, l_res, 1000)
    store_opt = [o for o in d_res_no_store["allOptions"] if o["id"] == "STORE_LATER"][0]
    assert store_opt["feasible"] == False
    assert d_res_no_store["winningOption"]["id"] != "STORE_LATER"
    print(f"  -> Store Later option feasible when storage unavailable: {store_opt['feasible']}")

    print("Testing Language Agent...")
    lang_agent = LanguageAgent()
    expl = lang_agent.generate_explanation(winning, m_res, w_res, s_res, l_res, "Tomato", 1000, "en")
    print(f"  -> English Reasoning: {expl['explanation'][:120]}...")
    expl_te = lang_agent.generate_explanation(winning, m_res, w_res, s_res, l_res, "Tomato", 1000, "te")
    print(f"  -> Telugu Reasoning: {expl_te['explanation'][:120]}...")

    print("Testing Notification Engine...")
    notif_engine = NotificationEngine()
    notifs = notif_engine.generate_alerts_and_notifications("Tomato", "Ongole", 1000, 25.0, m_res, w_res, s_res, l_res, d_res)
    print(f"  -> Generated {len(notifs)} dynamic notifications.")
    for n in notifs[:2]:
        print(f"     * [{n['type']}] {n['title']}: {n['message'][:80]}...")

    print("\nALL BACKEND AGENT TESTS PASSED SUCCESSFULLY! ✓")

if __name__ == "__main__":
    run_tests()
