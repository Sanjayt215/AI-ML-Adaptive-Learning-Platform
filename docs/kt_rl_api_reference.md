# AutoLearn KT-RL REST API Reference

**Application:** AutoLearn AI Adaptive Learning Platform  
**Base URL:** `http://localhost:5000` (or configured host)  
**Content-Type:** `application/json`  

---

## 1. Learning Interaction & Event Store Endpoints

### 1.1 Create Session
Create an isolated learning or quiz session record in the persistent event store.

- **Endpoint:** `POST /api/learning/sessions`
- **Request Body:**
  ```json
  {
    "user_id": "usr_stu_001",
    "topic": "Python Basics",
    "session_type": "quiz"
  }
  ```
- **Response `(200 OK)`:**
  ```json
  {
    "session_id": "sess_89f02c6114b04",
    "user_id": "usr_stu_001",
    "topic": "Python Basics",
    "session_type": "quiz",
    "started_at": "2026-10-20T12:00:00Z",
    "completed_at": null,
    "event_count": 0
  }
  ```

---

### 1.2 Get Session Details
Retrieve an existing session by ID, including duration and event counts.

- **Endpoint:** `GET /api/learning/sessions/<session_id>`
- **Response `(200 OK)`:**
  ```json
  {
    "session_id": "sess_89f02c6114b04",
    "user_id": "usr_stu_001",
    "topic": "Python Basics",
    "session_type": "quiz",
    "started_at": "2026-10-20T12:00:00Z",
    "completed_at": "2026-10-20T12:15:30Z",
    "duration_seconds": 930.0,
    "event_count": 10
  }
  ```
- **Error `(404 Not Found)`:** If session does not exist.

---

### 1.3 Complete Session
Mark an open learning session as finished.

- **Endpoint:** `POST /api/learning/sessions/<session_id>/complete`
- **Response `(200 OK)`:** Returns updated session record with `completed_at` populated.

---

### 1.4 Log Learning Event
Record an atomic student response event into `learner_events` and automatically trigger a BKT posterior update.

- **Endpoint:** `POST /api/learning/events`
- **Request Body:**
  ```json
  {
    "session_id": "sess_89f02c6114b04",
    "user_id": "usr_stu_001",
    "item_id": "py_syntax_01",
    "kc_id": "syntax_variables",
    "correct": 1,
    "response_time_ms": 4200,
    "attempt_number": 1,
    "hint_used": 0
  }
  ```
- **Response `(201 Created)`:**
  ```json
  {
    "event_id": 142,
    "status": "recorded",
    "updated_mastery": {
      "kc_id": "syntax_variables",
      "p_mastery": 0.3241,
      "p_transit": 0.15,
      "updated_at": "2026-10-20T12:02:15Z"
    }
  }
  ```

---

### 1.5 Get Learner Interaction Events
Retrieve historical interaction events for a learner.

- **Endpoint:** `GET /api/learning/events/<learner_id>?limit=50`
- **Query Parameters:**
  - `limit` (optional, default: 100): Maximum events to return.
- **Response `(200 OK)`:**
  ```json
  {
    "learner_id": "usr_stu_001",
    "total_events": 24,
    "events": [
      {
        "event_id": 1,
        "session_id": "sess_89f02c6114b04",
        "item_id": "py_syntax_01",
        "kc_id": "syntax_variables",
        "correct": 1,
        "response_time_ms": 4200,
        "timestamp": "2026-10-20T12:02:15Z"
      }
    ]
  }
  ```

---

### 1.6 Canonical Question Bank Items
List the full canonical question catalog (52 items) with primary KCs, secondary KCs, difficulty, and Bloom taxonomy ratings.

- **Endpoint:** `GET /api/learning/items`
- **Response `(200 OK)`:**
  ```json
  {
    "total": 52,
    "items": [
      {
        "item_id": "py_syntax_01",
        "topic": "Python Basics",
        "primary_kc": "syntax_variables",
        "secondary_kcs": [],
        "difficulty": "easy",
        "bloom_level": "remember",
        "question": "Which of the following is a valid variable name in Python?"
      }
    ]
  }
  ```

---

## 2. Knowledge Tracing & Mastery Endpoints

### 2.1 Get Current Learner Mastery Profile
Retrieve estimated mastery across all 30 curriculum Knowledge Components.

- **Endpoint:** `GET /api/learning/mastery/<learner_id>`
- **Response `(200 OK)`:**
  ```json
  {
    "learner_id": "usr_stu_001",
    "masteries": {
      "syntax_variables": 0.852,
      "data_types": 0.741,
      "loops_iteration": 0.420,
      "neural_network_basics": 0.100
    },
    "mean_mastery": 0.485,
    "mastered_kcs_count": 8,
    "total_kcs": 30
  }
  ```

---

### 2.2 Replay & Reconstruct Mastery History
Recompute BKT masteries from scratch by replaying the chronological event log.

- **Endpoint:** `POST /api/learning/mastery/<learner_id>/replay`
- **Response `(200 OK)`:**
  ```json
  {
    "learner_id": "usr_stu_001",
    "replayed_events": 24,
    "final_masteries": { ... },
    "execution_time_ms": 12.4
  }
  ```

---

### 2.3 Get Specific KC Mastery
Retrieve detailed state, attempt count, and last updated timestamp for a single KC.

- **Endpoint:** `GET /api/learning/mastery/<learner_id>/<kc_id>`
- **Response `(200 OK)`:**
  ```json
  {
    "learner_id": "usr_stu_001",
    "kc_id": "loops_iteration",
    "mastery": 0.420,
    "attempts": 4,
    "success_rate": 0.50,
    "last_updated": "2026-10-20T12:10:00Z"
  }
  ```

---

## 3. Production Adaptive Recommendation Endpoints

### 3.1 Get Next Adaptive Exercise Recommendation
Recommends the pedagogically optimal next question using forgetting decay, posterior uncertainty, and frustration-risk heuristics.

- **Endpoint:** `GET /api/adaptive/recommendation` or `POST /api/adaptive/recommendation`
- **Request Parameters / Body:**
  - `user_id` (optional, default: current session user or `"anonymous"`).
  - `strategy` (optional, default: `"composite_adaptive"`):
    - `"composite_adaptive"` (multi-objective recommended default)
    - `"prereq_aware_weakest"` (lowest mastery with prerequisites met)
    - `"forgetting_revision"` (skills with highest elapsed time decay)
    - `"confidence_exploration"` (highest posterior entropy / uncertainty)
    - `"frustration_remedial"` (difficulty fallback for struggling topics)
    - `"experimental_dqn"` (sandboxed neural policy)
  - `topic` (optional): Filter to specific topic (e.g., `"Python Basics"`).
- **Response `(200 OK)`:**
  ```json
  {
    "strategy_used": "composite_adaptive",
    "recommended_item": {
      "item_id": "py_loops_02",
      "question": "What is the output of `[x**2 for x in range(3)]`?",
      "topic": "Python Basics",
      "difficulty": "medium",
      "primary_kc": "loops_iteration",
      "options": ["[0, 1, 4]", "[1, 4, 9]", "[0, 1, 2]", "[1, 2, 3]"],
      "correct_answer": "[0, 1, 4]"
    },
    "pedagogical_rationale": "Recommended because mastery on loops_iteration is 0.42 (ZPD target) with high uncertainty (entropy: 0.98).",
    "metrics": {
      "target_kc": "loops_iteration",
      "estimated_mastery": 0.420,
      "predicted_retention": 0.385,
      "evidence_confidence": 0.650,
      "entropy": 0.981,
      "frustration_risk": false,
      "prerequisites_met": true
    }
  }
  ```

---

### 3.2 Adaptive Diagnostic State
Inspect the internal cognitive parameters, active frustration flags, and forgetting states for a learner.

- **Endpoint:** `GET /api/adaptive/diagnostics?user_id=<user_id>`
- **Response `(200 OK)`:**
  ```json
  {
    "user_id": "usr_stu_001",
    "active_frustration_topics": [],
    "top_decayed_kcs": [
      {"kc_id": "data_types", "elapsed_days": 18.2, "retention": 0.45, "bkt_mastery": 0.74}
    ],
    "high_entropy_kcs": [
      {"kc_id": "loops_iteration", "entropy": 0.981, "attempts": 2}
    ],
    "prerequisite_ready_count": 14,
    "blocked_kcs_count": 16
  }
  ```

---

## 4. Experimental Sandbox Endpoints (Flag-Guarded)

These endpoints are strictly governed by the environment variable `KT_RL_EXPERIMENT_ENABLED=0` (disabled by default).

### 4.1 Experimental RL Recommendation
Direct inference using the trained Dueling Double DQN network.

- **Endpoint:** `POST /api/experimental/recommendation`
- **When Flag Disabled (`KT_RL_EXPERIMENT_ENABLED=0`):**
  - **Response `(403 Forbidden)`:**
    ```json
    {
      "error": "KT-RL experimental recommendation endpoint is disabled in production.",
      "flag": "KT_RL_EXPERIMENT_ENABLED",
      "current_value": "0",
      "guidance": "To enable for offline research or sandbox validation, set KT_RL_EXPERIMENT_ENABLED=1."
    }
    ```
- **When Flag Enabled (`KT_RL_EXPERIMENT_ENABLED=1`):**
  - **Response `(200 OK)`:**
    ```json
    {
      "strategy_used": "dueling_dqn_final",
      "model_checkpoint": "dueling_dqn_final.pt",
      "recommended_item": {
        "item_id": "py_control_01",
        "topic": "Python Basics",
        "primary_kc": "control_flow_conditionals"
      },
      "q_values": {
        "max_q": 4.12,
        "mean_valid_q": 2.45
      },
      "prerequisite_mask_applied": true
    }
    ```
