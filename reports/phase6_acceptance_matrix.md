# AutoLearn KT-RL Phase 6 Acceptance Matrix

**Research Title:** Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection  
**Platform:** AutoLearn AI Adaptive Learning Platform  
**Research Team:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)  
**Date:** October 2026  
**Status Key:** `PASS` | `FAIL` | `BLOCKED` | `NOT TESTED`  

---

## 1. Acceptance Criteria & Verification Matrix

| ID | Category | Acceptance Criterion | Test Procedure | Expected Outcome | Observed Result | Evidence | Status |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **AC-01** | **Baseline Integrity** | All 59 unit & integration tests pass with zero failures. | Run `unittest discover -s autolearn_fullstack/tests` with PYTHONPATH set. | 59 tests run and pass without errors. | 59 tests ran in 7.40s; 0 failures, 0 errors. | `test_adaptive_recommender.py`, `test_bkt_service.py`, `test_dqn.py`, etc. | `PASS` |
| **AC-02** | **Item Bank Invariant** | Canonical question bank contains 52 validated items across 30 KCs. | Query `GET /api/learning/items` on running backend. | HTTP 200 with `count: 52` and valid schema. | HTTP 200; `count: 52`; 0 duplicate item IDs. | `live_system_acceptance.py` (Item 2) | `PASS` |
| **AC-03** | **Session Lifecycle** | Learning sessions can be created, tracked, and completed in SQLite. | Execute `POST /api/learning/sessions` and `POST /complete`. | HTTP 201 on create; status updated to `completed`. | Session created (`sess_...`), ended with ISO timestamp. | `live_system_acceptance.py` (Items 3, 4, 12) | `PASS` |
| **AC-04** | **Event Logging & BKT** | Student interaction events update latent BKT mastery monotonically. | Log correct and incorrect events via `POST /api/learning/events`. | P(K) increases after correct; decreases after incorrect. | Initial P(L)=0.10 rose to 0.32 after correct answer. | `live_system_acceptance.py` (Item 5) | `PASS` |
| **AC-05** | **Mastery Replay** | Chronological event replay reproduces identical posterior mastery. | Execute `POST /api/learning/mastery/<user>/replay`. | Replayed mastery matches incremental state within $10^{-5}$. | Replayed 2 events; error $< 10^{-6}$. Deterministic. | `live_system_acceptance.py` (Item 8) | `PASS` |
| **AC-06** | **Forgetting Decay (D1)** | Inactive skills experience exponential decay bounded by retention floor. | Compute $R(t) = m_{\text{floor}} + (P(K) - m_{\text{floor}})e^{-\lambda \Delta t}$. | Retention decreases with elapsed days; never drops below 0.10. | Tested $\Delta t \in [0, 60]$; floor $0.10$ preserved. | `test_adaptive_recommender.py` (`test_retention_decay`) | `PASS` |
| **AC-07** | **Posterior Entropy (D2)** | Uncertainty quantified by Shannon entropy $H(p)$, peaking at ZPD $0.50$. | Evaluate $H(p) = -p\log_2 p - (1-p)\log_2(1-p)$. | $H(0.50) = 1.0$; $H(0) \to 0$; $H(1) \to 0$. Numerical safety. | Exactly matches theoretical entropy; boundaries handled. | `test_adaptive_recommender.py` (`test_uncertainty`) | `PASS` |
| **AC-08** | **Frustration Risk (D3)** | Consecutive failures $\ge 2$ trigger difficulty step-down and prerequisite repair. | Simulate error streak on single topic and evaluate recommender. | Flags `is_frustrated: True`, lowers recommended difficulty. | Consecutive errors $\ge 2$ triggered remedial backoff. | `test_adaptive_recommender.py` (`test_frustration_risk`) | `PASS` |
| **AC-09** | **Action Masking Invariant** | Prerequisite action mask strictly prevents unready question assignment. | Evaluate policy against topics whose prerequisites are unmastered. | Mask $= 0$ for unready KCs; 0 prerequisite violations. | 0 invalid actions across all 180 simulated benchmark episodes. | `evaluate_all_9_policies.py` | `PASS` |
| **AC-10** | **Adaptive Strategy Routing** | Recommender supports all 6 documented pedagogical strategies. | Query `GET /api/adaptive/recommendation` for each strategy. | HTTP 200 with structured rationale and diagnostics. | All 6 strategies returned valid canonical items. | `live_system_acceptance.py` (Item 9) | `PASS` |
| **AC-11** | **Composite Policy Superiority** | Multi-objective composite policy balances mastery, entropy, and ZPD. | Benchmark `composite_adaptive` against heuristic baselines. | High cumulative reward with balanced item diversity. | Highest cumulative reward ($36.04 \pm 3.47$) of all 9 policies. | `phase6_reproducibility_results.json` | `PASS` |
| **AC-12** | **DQN Safety Feature Gate** | `KT_RL_EXPERIMENT_ENABLED=0` strictly prevents neural policy deployment. | Call `/api/experimental/recommendation` with flag unset/0. | Gracefully falls back to baseline with `experimental_flag_active: false`. | Verified: HTTP 200 with fallback baseline, zero DQN claims. | `live_system_acceptance.py` (Item 11) | `PASS` |
| **AC-13** | **Production Flow Isolation** | Standard `/api/quiz` submission operates untouched. | Execute standard quiz submission flow. | Normal score calculation, no synthetic data contamination. | Production quiz flow verified intact and completely isolated. | `test_learning_api.py` (`test_quiz_submission`) | `PASS` |
| **AC-14** | **Frontend UI Build** | React frontend compiles cleanly with adaptive recommendation card. | Execute `npm run build` in `frontend/`. | Optimized bundle created without compilation errors. | Compiled successfully (184.22 kB gzip JS bundle). | `npm run build` console output | `PASS` |
| **AC-15** | **Research Reproducibility** | All benchmark results reproduce deterministically from fixed seeds. | Run `evaluate_all_9_policies.py` across 5 fixed seeds. | Reproduces metrics for all 4 archetypes and baselines. | 180 episodes executed in 11s; results saved to JSON. | `phase6_reproducibility_results.json` | `PASS` |
| **AC-16** | **Scientific Honesty** | Dueling DQN acknowledged as offline artifact due to non-superiority. | Compare Dueling DQN true mastery gain to `prereq_aware_weakest`. | Report $-0.0292$ vs $-0.0245$; retain DQN in offline sandbox. | Documented in Model Card, Viva Prep, and Audit reports. | `kt_rl_model_card.md`, `PHASE_6_VIVA_PREPARATION.md` | `PASS` |

---

## 2. Summary Statistics

- **Total Acceptance Criteria Evaluated:** 16
- **Passed:** 16 (100.0%)
- **Failed:** 0 (0.0%)
- **Blocked:** 0 (0.0%)
- **Not Tested:** 0 (0.0%)
- **System Acceptance Status:** **FULLY ACCEPTED FOR ACADEMIC VIVA & EXPERIMENTAL DEMONSTRATION**
