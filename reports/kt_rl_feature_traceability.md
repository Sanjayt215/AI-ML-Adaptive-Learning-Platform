# Feature Traceability Matrix: AutoLearn KT-RL Research Upgrade

**Project:** Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection  
**Application:** AutoLearn AI Adaptive Learning Platform  
**Research Team:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)  
**Date of Audit:** October 19, 2026  

---

## 1. Traceability Matrix Summary

This matrix audits every research and engineering feature against actual source code, automated test suites, and empirical runtime evidence.

| Feature ID | Feature Name | Source File(s) | Tests | Integration Status | Audit Status |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **C1** | **Question & KC Metadata** | `resources.py` | `test_question_metadata.py` | Full item bank of 52 questions, 30 KCs, prerequisite DAG. | `VERIFIED` |
| **C2** | **Learning Event Persistence** | `learning_store.py` | `test_learning_store.py`, `test_learning_api.py` | SQLite store (`learning_events`, `learning_sessions`, `learner_states`). | `VERIFIED` |
| **C3** | **BKT State Engine** | `bkt_service.py` | `test_bkt_service.py` | Sequential Bayesian posterior updates, history replay, multi-KC updates. | `VERIFIED` |
| **E1** | **Learner Simulator** | `learner_simulator.py` | `test_rl_env.py` | 4 student archetypes, practice gains, exponential forgetting. | `VERIFIED` |
| **E2** | **Gymnasium RL Env** | `rl_env.py`, `rl_state_encoder.py`, `rl_reward.py` | `test_rl_env.py` | 99-dim state, Discrete(52) action space, prerequisite action masking. | `VERIFIED` |
| **E3** | **Dueling DQN Agent** | `dqn_agent.py`, `train_dqn.py` | `test_dqn.py` | Dueling streams $V(s)$ and $A(s, a)$, Double DQN targets, replay buffer. | `VERIFIED` |
| **E4** | **Evaluation & Ablations** | `evaluate_dqn.py`, `run_ablations.py` | `test_phase5.py` | 100-episode held-out benchmark, 4 ablation studies, empirical validation. | `VERIFIED` |
| **F1** | **Experimental Gatekeeper** | `app.py`, `experimental_recommendation_service.py` | `test_phase5.py` | `POST /api/experimental/recommendation` gated by `KT_RL_EXPERIMENT_ENABLED`. | `VERIFIED` |
| **D1** | **Forgetting-Aware Selection** | `services/adaptive_recommender.py` | *Pending Phase D* | Longitudinal time-since-practice retention decay model. | `PARTIAL` |
| **D2** | **Confidence-Aware Selection** | `services/adaptive_recommender.py` | *Pending Phase D* | Uncertainty-driven assessment exploration for low-evidence KCs. | `PARTIAL` |
| **D3** | **Frustration-Aware Adaptation**| `services/adaptive_recommender.py` | *Pending Phase D* | Disengagement risk detection with automatic remedial backoff. | `PARTIAL` |
| **D4** | **Prerequisite Enforcement** | `services/adaptive_recommender.py` | `test_rl_env.py`, *Pending Phase D* | Unified prerequisite eligibility filtering across all policies. | `VERIFIED` |
| **D5** | **Unified Recommendation API**| `services/adaptive_recommender.py`, `app.py` | *Pending Phase D* | Single modular service coordinating multiple recommendation strategies. | `MISSING` |
| **D6** | **Frontend Adaptive UI** | `DashboardPage.jsx`, `QuizPage.jsx` | *Pending Phase D* | Real-time adaptive recommendation card with pedagogical rationale. | `PARTIAL` |

---

## 2. Research Integrity & Decision Notes

1. **Empirical Grounding:** Features marked `VERIFIED` have passed both rigorous unit tests and live simulation or API checks.
2. **Phase D Focus:** Missing and partial features (D1, D2, D3, D5, D6) will now be implemented in a dedicated, unified adaptive recommendation architecture.
3. **No Premature Deployment:** Dueling DQN remains in experimental status, with production recommendation driven by verified pedagogical heuristics.
