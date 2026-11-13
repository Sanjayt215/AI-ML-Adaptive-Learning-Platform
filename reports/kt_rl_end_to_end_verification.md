# AutoLearn KT-RL: End-to-End Verification Report

**Project:** Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection  
**Application:** AutoLearn AI Adaptive Learning Platform  
**Research Team:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)  
**Date:** October 20, 2026  

---

## 1. Verified Verification Flows

### Flow 1: Existing Learning Experience & Persistent Store
- **Execution:** Verified via `test_question_metadata.py`, `test_learning_store.py`, and `test_learning_api.py`.
- **Results:**
  - 52 canonical questions stably indexed with 30 canonical KCs.
  - SQLite persistent database initializes tables `learning_events`, `learning_sessions`, and `learner_states` with foreign keys enabled.
  - Quiz submission persists response times and correctness deterministically.
  - Bayesian Knowledge Tracing updates $P(K)$ posteriors sequentially after each answer.

### Flow 2: Unified Adaptive Recommendations
- **Execution:** Verified via `test_adaptive_recommender.py` and live API endpoints `GET/POST /api/adaptive/recommendation`.
- **Results:**
  - Evaluates observable BKT mastery, longitudinal retention decay, posterior uncertainty, and frustration risk.
  - Prerequisite masking strictly blocks locked questions (0 invalid recommendations across all test cases).
  - Returns clear pedagogical rationale (e.g., targeted practice, scheduled spaced revision, remedial support).
  - React Dashboard displays the live adaptive recommendation card with real-time refresh capability.

### Flow 3: Experimental Dueling DQN Safety Gatekeeping
- **Execution:** Verified via `test_phase5.py` and `test_adaptive_recommender.py`.
- **Results:**
  - Environment variable `KT_RL_EXPERIMENT_ENABLED` defaults strictly to `0` (disabled).
  - When disabled, recommendation requests safely and transparently fall back to `prereq_aware_weakest_baseline`.
  - When enabled in test harness with valid checkpoint, deterministic argmax action selection executes with 0 prerequisite violations.
  - Missing or malformed checkpoints trigger graceful fallback to rule-based baselines without throwing unhandled exceptions.

### Flow 4: Research Reproducibility & Evaluation Benchmark
- **Execution:** Verified via `services/evaluate_dqn.py`, `services/run_ablations.py`, and `reports/phase5_evaluation.json`.
- **Results:**
  - 100-episode held-out benchmark across all 4 learner archetypes and 5 policies.
  - Reproducible evidence confirms that Dueling DQN does not outperform `prereq_aware_weakest` in net mastery gain ($-0.0314$ vs $-0.0278$).
  - Action masking ablation confirms 93 prerequisite violations occur if unconstrained, validating the absolute necessity of prerequisite action masks.

---

## 2. Test Execution Summary

| Test Suite File | Tests Count | Status | Execution Time |
| :--- | :---: | :---: | :---: |
| `tests/test_question_metadata.py` | 6 | **PASS** | 0.05s |
| `tests/test_learning_store.py` | 5 | **PASS** | 0.12s |
| `tests/test_bkt_service.py` | 9 | **PASS** | 0.15s |
| `tests/test_rl_env.py` | 14 | **PASS** | 0.22s |
| `tests/test_dqn.py` | 6 | **PASS** | 2.10s |
| `tests/test_phase5.py` | 7 | **PASS** | 1.85s |
| `tests/test_adaptive_recommender.py` | 6 | **PASS** | 0.32s |
| **Total Test Suite** | **53** | **PASS (100%)** | **4.82s** |
