# Model Card Addendum: Phase 7 Advanced RL Improvements & Verification

**Model Identifier:** `dueling_dqn_final.pt`  
**Evaluation Phase:** Phase 7 Policy Audit, Advanced RL Improvements & Verified Integration  
**Date:** October 2026  
**Authors:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)  
**Parent Document:** [`reports/kt_rl_model_card.md`](file:///c:/Users/sanja/Downloads/autolearn_llm_ml_upgrade_ready/autolearn_fullstack/reports/kt_rl_model_card.md)  

---

## 1. Executive Summary & Gating Reconfirmation

During Phase 7, the Dueling Double DQN model was subjected to:
1. Long-horizon retention evaluation (7-day simulated dormant interval).
2. Counterfactual reward alignment and entropy-harvesting decomposition.
3. Out-of-distribution (OOD) generalization testing across 4 diverse scenarios (unseen seeds, $T=40$ steps, struggling cohort shift, fast cohort shift).
4. Head-to-head comparison against 9 competitor policies including a newly implemented LinUCB Contextual Bandit.

### Deployment Gate Verdict:
**STATUS: NOT CLEARED FOR PRODUCTION DEPLOYMENT (`KT_RL_EXPERIMENT_ENABLED=0` REMAINS MANDATORY).**
The model is strictly preserved as an offline research benchmark artifact. Production recommendations continue to be served by the verified `AdaptiveRecommender` (`composite_adaptive` / `prereq_aware_weakest`).

---

## 2. Phase 7 Empirical Findings & Insights

### 2.1 Reward Proxy Exploitation Confirmed
Decomposition of the RL reward signal revealed that **$27.9\%$ of Dueling DQN's cumulative reward** was derived purely from static prior Shannon entropy ($r_{\text{info}}$), rather than true knowledge acquisition or information reduction.
When evaluated under the counterfactual aligned reward:
- `dueling_dqn` reward drops from $32.2$ to $29.5$.
- `prereq_aware_weakest` reward increases from $31.5$ to $32.3$ ($r = +0.78$ with true learning gain).

### 2.2 Long-Horizon Retention Outcomes (7 Days Inactivity)
- `prereq_aware_weakest`: Net Retained Gain **$-0.0459 \pm 0.0188$**, Gross Learning **$+2.09$**, Retention Rate $87.3\%$.
- `dueling_dqn`: Net Retained Gain $-0.0500 \pm 0.0174$, Gross Learning $+1.90$, Retention Rate $87.4\%$.
The heuristic baseline generated $+10\%$ more durable learning than the neural policy.

### 2.3 Out-of-Distribution Generalization Robustness
| Generalization Condition | `prereq_aware_weakest` Net Gain | `dueling_dqn` Net Gain | Winner |
| :--- | :---: | :---: | :---: |
| **Unseen Seeds (2001..2005)** | $\mathbf{-0.0401}$ | $-0.0448$ | `prereq_aware_weakest` ($+11\%$ better) |
| **Extended Horizon ($T=40$)** | $\mathbf{-0.0241}$ | $-0.0393$ | `prereq_aware_weakest` ($+39\%$ better) |
| **Struggling-Heavy Cohort Shift** | $\mathbf{-0.0429}$ | $-0.0449$ | `prereq_aware_weakest` ($+5\%$ better) |
| **Fast-Learner Skew** | $\mathbf{+0.0222}$ | $+0.0123$ | `prereq_aware_weakest` ($+80\%$ better) |

---

## 3. Comparison with Contextual Bandit (LinUCB)

A Linear Upper Confidence Bound (LinUCB) contextual bandit baseline was trained online with prerequisite masking:
- `linucb_bandit` achieved cumulative reward $11.13 \pm 1.94$ and gross learning $+0.89$.
- In short 25-step sessions with 52 discrete actions, an uninitialized linear bandit under-explores compared to domain-structured pedagogical policies. Dueling DQN ($32.23$) significantly outperformed the Contextual Bandit ($11.13$), validating that Deep Q-learning effectively learned action advantages over the state space even though it did not beat domain-specific heuristic trees.

---

## 4. Operational Boundaries

1. **Safety Feature Gate:** `KT_RL_EXPERIMENT_ENABLED` must default strictly to `0`.
2. **Action Masking Requirement:** Dueling DQN must never be queried without the dynamic prerequisite mask; unmasked actions violate curriculum prerequisites.
3. **Sandbox Storage:** The model checkpoint is stored at `autolearn_fullstack/models/dqn/dueling_dqn_final.pt` for reproducible research only.
