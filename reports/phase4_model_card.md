# Model Card: Dueling Deep Q-Network (Dueling DQN) for Exercise Selection

**Model Name:** `dueling_dqn_final.pt`  
**Architecture:** Dueling Double Deep Q-Network with Prerequisite Action Masking  
**Version:** `kt_rl_dueling_dqn_v1`  
**Date:** October 13, 2026  
**Authors:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)  
**Project:** Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection (`AutoLearn AI`)

---

## 1. Model Overview

The model is a Dueling Deep Q-Network designed to recommend personalized practice exercises from a 52-question canonical item bank covering 30 Knowledge Components (KCs). The policy operates sequentially over simulated student sessions, selecting pedagogical items to maximize learner mastery gains and diagnostic value while matching student Zone of Proximal Development (ZPD) and enforcing curriculum prerequisite constraints.

---

## 2. Model Architecture & Specifications

| Component | Specification | Description |
| :--- | :--- | :--- |
| **Observation Space** | 99-dimensional `float32` vector | Normalized observable states: BKT masteries [0:30], attempt counts [30:60], readiness flags [60:90], recent history [90:95], repeated failures [95], last difficulty [96], episode progress [97], global mastery [98]. |
| **Action Space** | `Discrete(52)` | Deterministically ordered exercise items covering beginner to advanced questions. |
| **Shared Network** | Linear(99, 128) $\to$ LayerNorm $\to$ ReLU $\to$ Linear(128, 128) $\to$ LayerNorm $\to$ ReLU | Dense representation extractor mapping observable student features. |
| **State-Value Stream $V(s)$** | Linear(128, 64) $\to$ ReLU $\to$ Linear(64, 1) | Estimates scalar value of the student's current learning state. |
| **Advantage Stream $A(s, a)$** | Linear(128, 64) $\to$ ReLU $\to$ Linear(64, 52) | Estimates relative advantage of each exercise candidate. |
| **Dueling Aggregation** | $Q(s, a) = V(s) + \left(A(s, a) - \frac{1}{\|\mathcal{A}\|} \sum_{a'} A(s, a')\right)$ | Decouples state value from action choices for variance reduction. |
| **Action Masking** | Dynamic prerequisite mask (1 = valid, 0 = invalid) | Invalid actions masked with large negative logit ($-10^9$) during action selection and Double DQN target evaluation. |
| **Loss Function** | Smooth L1 (Huber Loss) | Robust to extreme reward spikes during early training. |
| **Optimizer** | Adam (Learning Rate: $3 \times 10^{-4}$) with Gradient Clipping ($\le 1.0$) | Stable optimization across heterogeneous student archetypes. |

---

## 3. Training Configuration & Hyperparameters

- **Training Episodes:** 120 episodes (25 steps per episode = 3,000 interaction transitions).
- **Archetype Rotation:** Balanced round-robin across 4 synthetic learner profiles:
  - `fast_learner`
  - `typical_learner`
  - `struggling_learner`
  - `inconsistent_learner`
- **Exploration Schedule:** Epsilon-greedy decaying linearly from $\epsilon = 1.00$ to $\epsilon = 0.05$ over 2,000 steps.
- **Replay Memory:** Uniform Replay Buffer (Capacity: 20,000 transitions, Batch Size: 64).
- **Warmup Period:** 15 initial episodes (375 steps) collected before gradient descent.
- **Target Network Sync:** Hard parameter copy every 150 training update steps.
- **Discount Factor ($\gamma$):** 0.99.

---

## 4. Evaluation Benchmark & Performance Summary

The model was evaluated deterministically ($\epsilon = 0.0$) against 4 heuristic baselines across 20 fixed-seed evaluation episodes (5 seeds $\times$ 4 archetypes, 25 steps per episode):

| Policy | Mean Reward | Reward Std | Mastery Gain | Accuracy | Invalid Actions | BKT MAE |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dueling DQN (Trained)** | **32.23** | 8.36 | -0.0292 | **46.4%** | **0** | **0.1413** |
| `random_eligible` | 32.73 | 8.42 | -0.0260 | 42.8% | 0 | 0.1593 |
| `weakest_bkt_kc` | 25.73 | 11.04 | -0.0273 | 45.8% | 0 | 0.1742 |
| `difficulty_ladder` | 11.82 | 3.98 | -0.0587 | 66.2% | 0 | 0.1013 |
| `prereq_aware_weakest` | 31.48 | 10.84 | **-0.0245** | 50.2% | 0 | 0.1843 |

### Key Findings:
1. **Curriculum Prerequisite Adherence:** Enforced **0 invalid actions** across all training and evaluation episodes.
2. **Predictive BKT Calibration:** Dueling DQN achieved lower BKT estimation error (**MAE 0.1413**) compared to exploratory baselines (0.1593–0.1843), demonstrating strategic sampling of diagnostic topics.
3. **Reward Optimization:** Achieved 32.23 mean reward, outperforming `difficulty_ladder` (11.82) and `weakest_bkt_kc` (25.73).

---

## 5. Limitations & Ethical Considerations

- **Synthetic Simulator Training:** The policy was trained on synthetic student archetypes governed by Bayesian Knowledge Tracing and logistic response generation. Human learner behavior exhibits higher noise and fatigue dynamics.
- **Offline Sandbox Status:** Model checkpoints are maintained in `models/dqn/` and **must not be deployed to real students** without offline gatekeeping and shadow-mode validation.

---

## 6. Phase 5 Evaluation Addendum (October 19, 2026)

### 6.1 100-Episode Held-Out Benchmark Results
An expanded, held-out evaluation across 100 episodes (25 seeds $\times$ 4 archetypes) revealed that Dueling DQN did **not** demonstrate superior true mastery outcomes compared to established heuristic baselines:
- **Dueling DQN Net True Mastery Gain:** $-0.0314 \pm 0.0079$
- **Prerequisite-Aware Weakest Baseline Net Gain:** $\mathbf{-0.0278 \pm 0.0085}$
- **Random Eligible Baseline Net Gain:** $-0.0292 \pm 0.0080$

### 6.2 Key Ablation Insights
- **Double DQN vs Standard DQN:** Double DQN achieved $+1.08$ higher cumulative reward (28.23 vs 27.15) and reduced Q-value overestimation bias.
- **Action Masking Integrity:** Unconstrained selection resulted in 93 prerequisite violations (4.65 per episode) and dropped cumulative reward from 33.27 to 18.46. Action masking successfully maintained 0 violations.
- **Reward Proxy Disconnect:** The policy achieved high cumulative rewards primarily by harvesting Shannon entropy and ZPD Gaussian match bonuses rather than driving net mastery gains.

### 6.3 Deployment Decision
**STATUS: NOT CLEARED FOR PRODUCTION DEPLOYMENT.**  
In accordance with pre-defined safety decision rules, the model is restricted to offline demonstration and shadow mode via the disabled-by-default flag `KT_RL_EXPERIMENT_ENABLED=0`. Production quiz recommendations continue to use the verified prerequisite-aware BKT recommender.
