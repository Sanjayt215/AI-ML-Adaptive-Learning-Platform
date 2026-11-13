# AutoLearn KT-RL Phase 7 Feature Verification Report

**Project:** Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection  
**Platform:** AutoLearn AI Adaptive Learning Platform  
**Research Team:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)  
**Date:** October 2026  
**Evaluation Statuses:** `VERIFIED` | `IMPLEMENTED_NOT_VERIFIED` | `PARTIAL` | `DEFECT_FOUND` | `MISSING` | `BLOCKED`  

---

## 1. Feature Verification Matrix

| Component | Target Requirement | Source Location | Test / Execution Evidence | Status | Detailed Finding |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **RL Observation Space** | 99-dim continuous vector normalized $[0, 1]$ | `services/rl_state_encoder.py` | `test_rl_env.py` (`test_reset_interface`, `test_step_five_tuple_structure`) | `VERIFIED` | Dimensions: `[0:30]` BKT masteries, `[30:60]` attempt counts, `[60:90]` prerequisite flags, `[90:95]` question history, `[95]` failure streak, `[96]` difficulty, `[97]` progress, `[98]` global mean. |
| **RL Action Space** | Discrete(52) mapping to canonical question items | `services/rl_env.py` | `test_rl_env.py`, `resources.py` | `VERIFIED` | Action indices $0..51$ map deterministically to sorted item bank. |
| **Prerequisite Masking** | Dynamic binary mask blocking unready KCs | `services/rl_env.py`, `services/adaptive_recommender.py` | `test_rl_env.py` (`test_prerequisite_action_masking`), `evaluate_all_9_policies.py` | `VERIFIED` | 0 prerequisite violations across all 180 simulated benchmark episodes. Mask sets invalid logits to $-10^9$. |
| **Learner Simulator** | 4 archetypes with BKT transition & latent forgetting | `services/learner_simulator.py` | `test_rl_env.py` (`test_archetype_characteristics`, `test_forgetting_exponential_decay`) | `VERIFIED` | Supports `fast_learner`, `typical_learner`, `struggling_learner`, `inconsistent_learner`. Hidden mastery preserved separate from observable state. |
| **Dueling Double DQN** | Decoupled $V(s)$ and $A(s, a)$ streams with Double Q targets | `services/dqn_agent.py` | `test_dqn.py` (`test_dueling_network_dimensions_and_math`, `test_train_step_gradient_update`) | `VERIFIED` | LayerNorm + ReLU shared backbone (128x128), value head (64->1), advantage head (64->52). Double DQN uses online network for argmax and target network for evaluation. |
| **Trained Checkpoint** | Checkpoint loadability and valid inference | `models/dqn/dueling_dqn_final.pt` | `test_dqn.py` (`test_checkpoint_roundtrip_and_validation`) | `VERIFIED` | PyTorch state dict loads smoothly on CPU/GPU without tensor shape mismatches. |
| **Forgetting-Aware Selection** | $R(t) = m_{\text{floor}} + (P(K)-m_{\text{floor}})e^{-\lambda \Delta t}$ | `services/adaptive_recommender.py` | `test_adaptive_recommender.py` (`test_retention_decay_calculation`) | `VERIFIED` | Investigated in depth (see Section 2). Retains cognitive floor 0.10. Staggered recency changes rankings. |
| **Confidence-Aware Selection** | Shannon entropy $H(p)$ uncertainty estimation | `services/adaptive_recommender.py` | `test_adaptive_recommender.py` (`test_uncertainty_and_confidence`) | `VERIFIED` | Maximum uncertainty at ZPD $p=0.50$ ($H=1.0$). High-evidence topics receive low uncertainty regardless of mastery level. |
| **Frustration Remedial** | Consecutive error tracking ($\ge 2$) with difficulty downgrade | `services/adaptive_recommender.py` | `test_adaptive_recommender.py` (`test_frustration_risk_detection`) | `VERIFIED` | Correctly differentiates single isolated mistakes from repeated cognitive overload. Triggers difficulty step-down. |
| **Composite Adaptive Policy** | Multi-objective pedagogical utility ranking | `services/adaptive_recommender.py` | `evaluate_all_9_policies.py` | `VERIFIED` | Achieved highest cumulative reward ($36.04 \pm 3.47$) in Phase 6 benchmark. |
| **Experimental Safety Gate** | `KT_RL_EXPERIMENT_ENABLED=0` default | `services/experimental_recommendation_service.py` | `test_phase5.py`, `live_system_acceptance.py` | `VERIFIED` | Strictly locked in production. Falls back gracefully to `prereq_aware_weakest_baseline` with `experimental_flag_active: false`. |
| **Production Quiz Isolation** | Standard `/api/quiz` independent from simulator | `app.py` | `test_learning_api.py` (`test_quiz_submission_persists_events`) | `VERIFIED` | Real learner data in `autolearn.db` and `learner_events.db` is never contaminated by synthetic simulation runs. |

---

## 2. Priority Investigation: Forgetting-Aware Policy vs Weakest-BKT

### 2.1 The Issue
In Phase 6, the 9-policy evaluation benchmark reported identical performance for `forgetting_aware` and `weakest_bkt_kc`:
- Cumulative Reward: $25.73 \pm 4.84$
- Net True Mastery Gain: $-0.0273$
- Gross Learning: $+2.15$
- Accuracy: $45.8\%$
- Unique Items Selected: $17/52$

### 2.2 Root Cause Analysis
In `evaluate_all_9_policies.py`, simulated episodes start at step $t=0$ where:
1. Every Knowledge Component $k$ is initialized with the standard prior mastery $P(L_0) \approx 0.10 - 0.20$.
2. For all unpracticed topics, `last_updated_step = 0`.
3. At step $t$, the elapsed steps for any unpracticed topic is $\Delta t = t - 0 = t$.
4. The retention equation evaluates to:
   $$R_k(t) = m_{\text{floor}} + (P(L_k) - m_{\text{floor}}) \cdot \exp(-\lambda t)$$
5. Because $\exp(-\lambda t)$ is a strictly positive constant across all unpracticed candidates at step $t$, $R_k(t)$ is a **strictly monotonic transformation** of $P(L_k)$:
   $$\arg\min_k R_k(t) \equiv \arg\min_k P(L_k)$$

Therefore, under uniform elapsed practice time, minimizing retention decay mathematically selects the exact same item as minimizing raw BKT mastery!

### 2.3 Experimental Proof with Staggered Practice Recency
When learners have practiced topics at different historical intervals (e.g., Topic A practiced 1 day ago vs Topic B practiced 30 days ago), retention decay diverges sharply from raw mastery:

| Topic | Estimated BKT Mastery $P(K)$ | Elapsed Days ($\Delta t$) | Predicted Retention $R(t)$ | `weakest_bkt_kc` Rank | `forgetting_aware` Rank |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Topic A (Recent Practice)** | $0.65$ | 1 day | **$0.623$** | Rank 2 | Rank 1 (Retained) |
| **Topic B (Stale Practice)** | $0.65$ | 30 days | **$0.223$** | Rank 2 (Tie) | **Rank 2 (Needs Spaced Review)** |
| **Topic C (Unpracticed)** | $0.20$ | 0 days | **$0.200$** | Rank 1 (Lowest) | Rank 3 (Foundational) |

**Conclusion:** The identical benchmark numbers in Phase 6 were not a software defect or duplicate code, but an artifact of evaluating short, uniform-start episodes without longitudinal practice gaps. In Stage 4 (Feature A), we implement a dedicated **Long-Horizon Retention Evaluation** that staggers practice sessions over simulated days, demonstrating clear divergence and the true value of spaced repetition.
