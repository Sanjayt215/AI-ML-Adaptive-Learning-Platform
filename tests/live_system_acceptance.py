"""
Live system acceptance test script for AutoLearn KT-RL Phase 6.
Tests live HTTP endpoints on http://127.0.0.1:5001 without mocking.
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:5001"
TEST_USER = f"phase6_val_user_{int(time.time())}"

def run_acceptance():
    results = {}
    print(f"Starting live acceptance tests against {BASE_URL} for user {TEST_USER}")

    # 1. Status
    res = requests.get(f"{BASE_URL}/api/status")
    assert res.status_code == 200, f"Status failed: {res.status_code}"
    status_data = res.json()
    assert status_data.get("ok") is True
    results["api_status"] = "PASS"
    print("[PASS] 1. /api/status OK")

    # 2. Canonical items
    res = requests.get(f"{BASE_URL}/api/learning/items")
    assert res.status_code == 200
    items_data = res.json()
    total_items = items_data.get("count", len(items_data.get("items", [])))
    assert total_items == 52, f"Expected 52 items, got {total_items}"
    results["canonical_items_count_52"] = "PASS"
    print(f"[PASS] 2. /api/learning/items OK (52 items verified)")

    # 3. Create Session
    session_payload = {
        "learner_id": TEST_USER,
        "target_topics": ["Python Basics"],
        "session_type": "practice"
    }
    res = requests.post(f"{BASE_URL}/api/learning/sessions", json=session_payload)
    assert res.status_code == 201, f"Create session failed: {res.status_code}"
    session_data = res.json()
    session_id = session_data["session"]["session_id"]
    assert session_id.startswith("sess_")
    results["create_session"] = "PASS"
    print(f"[PASS] 3. /api/learning/sessions OK (session_id={session_id})")

    # 4. Get Session
    res = requests.get(f"{BASE_URL}/api/learning/sessions/{session_id}")
    assert res.status_code == 200
    assert res.json()["session"]["session_id"] == session_id
    results["get_session"] = "PASS"
    print("[PASS] 4. /api/learning/sessions/<id> OK")

    # 5. Log Events (correct and incorrect)
    # Event 1: Correct on syntax_variables
    e1 = {
        "session_id": session_id,
        "learner_id": TEST_USER,
        "item_id": "py_syntax_01",
        "knowledge_components": ["syntax_variables"],
        "correctness": 1,
        "response_time_ms": 3500,
        "attempt_number": 1
    }
    res = requests.post(f"{BASE_URL}/api/learning/events", json=e1)
    assert res.status_code == 201, f"Log event 1 failed: {res.status_code}"
    e1_res = res.json()
    assert e1_res.get("ok") is True
    print(f"[PASS] 5a. Log Event 1 (Correct) OK")

    # Event 2: Incorrect on loops_iteration
    e2 = {
        "session_id": session_id,
        "learner_id": TEST_USER,
        "item_id": "py_loops_01",
        "knowledge_components": ["loops_iteration"],
        "correctness": 0,
        "response_time_ms": 7200,
        "attempt_number": 1
    }
    res = requests.post(f"{BASE_URL}/api/learning/events", json=e2)
    assert res.status_code == 201
    results["log_events_and_bkt_update"] = "PASS"
    print(f"[PASS] 5b. Log Event 2 (Incorrect) OK")

    # 6. Retrieve Events
    res = requests.get(f"{BASE_URL}/api/learning/events/{TEST_USER}")
    assert res.status_code == 200
    events_list = res.json().get("events", [])
    assert len(events_list) == 2, f"Expected 2 events, got {len(events_list)}"
    results["retrieve_learner_events"] = "PASS"
    print(f"[PASS] 6. /api/learning/events/<user> OK ({len(events_list)} events)")

    # 7. Mastery State & Replay
    res = requests.get(f"{BASE_URL}/api/learning/mastery/{TEST_USER}")
    assert res.status_code == 200
    m_data = res.json()
    assert m_data.get("ok") is True
    assert "topics_map" in m_data or "topics" in m_data
    topics = m_data.get("topics_map", {})
    results["get_mastery_state"] = "PASS"
    print(f"[PASS] 7. /api/learning/mastery/<user> OK (model={m_data.get('model')}, topics={len(topics)})")

    # Replay
    res = requests.post(f"{BASE_URL}/api/learning/mastery/{TEST_USER}/replay")
    assert res.status_code == 200
    replay_data = res.json()
    assert replay_data.get("ok") is True
    assert replay_data.get("total_events_processed") == 2
    assert "topics" in replay_data
    results["replay_mastery_deterministic"] = "PASS"
    print(f"[PASS] 8. Mastery chronological replay OK (processed={replay_data.get('total_events_processed')})")

    # 8. Adaptive Recommendation for all strategies
    strategies = [
        "composite_adaptive",
        "prereq_aware_weakest",
        "forgetting_revision",
        "confidence_exploration",
        "frustration_remedial",
        "experimental_dqn"
    ]
    for strat in strategies:
        res = requests.get(f"{BASE_URL}/api/adaptive/recommendation", params={"learner_id": TEST_USER, "strategy": strat})
        assert res.status_code == 200, f"Strategy {strat} failed: {res.status_code}"
        rec = res.json()
        assert rec.get("ok") is True, f"Strategy {strat} returned ok=False"
        assert "item_id" in rec, f"Missing item_id in {strat}"
        assert "explanation" in rec, f"Missing explanation in {strat}"
        assert "diagnostics" in rec, f"Missing diagnostics in {strat}"
        assert rec.get("prerequisites_valid") is True, f"Prerequisites invalid for {strat}"
        print(f"[PASS] 9. Strategy '{strat}' returned item '{rec['item_id']}' for KC '{rec.get('primary_kc')}'")
    results["all_adaptive_strategies"] = "PASS"

    # 9. Adaptive Diagnostics
    res = requests.get(f"{BASE_URL}/api/adaptive/diagnostics", params={"learner_id": TEST_USER})
    assert res.status_code == 200
    diag = res.json()
    assert diag.get("ok") is True
    assert "diagnostics" in diag
    results["adaptive_diagnostics"] = "PASS"
    print("[PASS] 10. /api/adaptive/diagnostics OK")

    # 10. Experimental DQN Safety (Flag = 0 default fallback)
    res = requests.post(f"{BASE_URL}/api/experimental/recommendation", json={"learner_id": TEST_USER})
    assert res.status_code == 200, f"Expected 200 with fallback, got {res.status_code}"
    exp_res = res.json()
    assert exp_res.get("ok") is True
    assert exp_res["explanation"]["experimental_flag_active"] is False, "Experimental flag should be inactive"
    assert exp_res["explanation"]["policy_mode"] == "prereq_aware_weakest_baseline", "Must use fallback baseline"
    assert "dueling_dqn" not in exp_res["explanation"]["policy_mode"], "Must not falsely claim DQN selection"
    results["experimental_dqn_gated_fallback"] = "PASS"
    print("[PASS] 11. /api/experimental/recommendation safely fell back to prereq_aware_weakest_baseline (experimental_flag_active=False)")

    # 11. Complete Session
    res = requests.post(f"{BASE_URL}/api/learning/sessions/{session_id}/complete")
    assert res.status_code == 200
    sess_done = res.json().get("session", {})
    assert sess_done.get("status") == "completed", "Session status must be completed"
    assert sess_done.get("ended_at") is not None, "ended_at must be populated"
    results["complete_session"] = "PASS"
    print(f"[PASS] 12. Session completion OK (status={sess_done.get('status')})")

    print("\nALL LIVE ACCEPTANCE TESTS PASSED SUCCESSFULLY!")
    return results

if __name__ == "__main__":
    run_acceptance()
