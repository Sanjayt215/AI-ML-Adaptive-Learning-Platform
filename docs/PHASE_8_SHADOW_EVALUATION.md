# Phase 8: Safe Shadow Evaluation Architecture & Operational Guide

**Project:** Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection  
**Platform:** AutoLearn AI Adaptive Learning Platform  
**Authors:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)

---

## 1. Executive Purpose

Directly exposing experimental Deep Reinforcement Learning agents (e.g. Dueling DQN, LinUCB) to human students introduces educational and ethical risks if policies produce unpedagogical exercise sequences or induce cognitive fatigue.

**Safe Shadow Evaluation** allows researchers to benchmark experimental RL policies in a live production environment **without altering the instructional experience** of any student:
1. The student interacts with the proven, pedagogically constrained production policy (`composite_adaptive` or `prerequisite_aware`).
2. Concurrently, the RL policy computes what exercise it *would have chosen* given the exact same learner state.
3. Both decisions, their agreement/divergence, and computational latencies are recorded asynchronously.
4. The student never sees the experimental decision, preventing adverse pedagogical exposure.

---

## 2. System Architecture & Information Flow

```
                           +--------------------------+
                           |  Student Practice Request|
                           +--------------------------+
                                        |
                                        v
                 +----------------------------------------------+
                 | Unified Adaptive Recommender (Production)    |
                 +----------------------------------------------+
                                        |
                 +----------------------+-----------------------+
                 |                                              |
                 v (Real-time Serve)                            v (If KT_RL_SHADOW_MODE=1)
    +-------------------------+                    +---------------------------+
    | Serves Production Item  |                    | Run Experimental Policies |
    | to Learner Client       |                    | (Dueling DQN, LinUCB)     |
    +-------------------------+                    +---------------------------+
                                                                |
                                                                v
                                                   +---------------------------+
                                                   | Record Shadow Decision &  |
                                                   | Measure Concordance Rate  |
                                                   +---------------------------+
```

---

## 3. Key Safety Properties

| Property | Implementation Mechanism | Safety Guarantee |
| :--- | :--- | :--- |
| **Strict Inactive Default** | `KT_RL_SHADOW_MODE=0` | Zero background computation or logging occurs unless explicitly commanded |
| **Complete Client Isolation** | Recommendation payload strictly ignores shadow output | The student's device only ever receives the verified production item |
| **Fault Isolation** | Comprehensive `try-except` blocks enclosing shadow calls | Any failure in experimental code is caught; live requests are never dropped |
| **Low Latency Impact** | Non-blocking execution / sub-50ms inference | Learner user experience remains snappy and unhindered |

---

## 4. REST API Endpoint: Shadow Metrics Inspection

- **Endpoint:** `GET /api/research/shadow_metrics`
- **Access:** Administrator / Researcher only
- **Response Format:**
  ```json
  {
    "status": "success",
    "metrics": {
      "total_evaluations": 142,
      "shadow_mode_enabled": true,
      "policies": {
        "dueling_dqn": {
          "evaluations": 142,
          "concordance_rate": 0.6408,
          "mean_latency_ms": 14.8
        },
        "linucb_bandit": {
          "evaluations": 142,
          "concordance_rate": 0.5845,
          "mean_latency_ms": 6.2
        }
      }
    }
  }
  ```
