# Phase 5 Policy Comparison & Empirical Benchmark Report

**Project:** Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection  
**Application:** AutoLearn AI Adaptive Learning Platform  
**Research Team:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)  
**Evaluation Protocol:** 100 Held-Out Evaluation Episodes (25 seeds $\times$ 4 synthetic learner archetypes, 25 steps per episode = 2,500 decision steps per policy)  
**Date:** October 19, 2026  

---

## 1. Overall Policy Performance Summary

All policies were evaluated under identical frozen conditions with deterministic action selection where applicable ($\epsilon = 0.0$ for Dueling DQN):

| Policy / Model | Mean Cumulative Reward | 95% Confidence Interval | Net True Mastery Gain | Net Gain 95% CI | Gross Learning ($\sum \Delta m$) | Accuracy (%) | Unique Items (/52) | Action Entropy (bits) | Invalid Actions | BKT MAE |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`dueling_dqn` (Trained)** | 32.22 | $\pm 1.93$ | -0.0314 | $\pm 0.0079$ | +2.16 | 50.0% | 34 | 4.474 | **0** | 0.1580 |
| **`random_eligible`** | **33.72** | $\pm 1.72$ | -0.0292 | $\pm 0.0080$ | +2.23 | 46.1% | 52 | 5.679 | **0** | 0.1601 |
| **`prereq_aware_weakest`** | 30.38 | $\pm 2.45$ | **-0.0278** | $\pm 0.0085$ | **+2.28** | 50.6% | 19 | 3.522 | **0** | 0.1668 |
| **`weakest_bkt_kc`** | 25.43 | $\pm 2.54$ | -0.0305 | $\pm 0.0081$ | +2.16 | 47.2% | 17 | 3.267 | **0** | 0.1607 |
| **`difficulty_ladder`** | 11.52 | $\pm 0.58$ | -0.0619 | $\pm 0.0051$ | +1.01 | **70.5%** | 1 | 0.000 | **0** | **0.0880** |

---

## 2. Granular Archetype Breakdown

Evaluation was stratified across 4 distinct learner archetypes (25 episodes each):

### A. Fast Learner ($\alpha = 0.28, \lambda = 0.01$)
- **`prereq_aware_weakest`**: Net Gain **+0.0318**, Reward 41.59, Accuracy 60.3%
- **`random_eligible`**: Net Gain +0.0298, Reward 45.47, Accuracy 54.7%
- **`dueling_dqn`**: Net Gain +0.0264, Reward 43.55, Accuracy 58.6%
- **`weakest_bkt_kc`**: Net Gain +0.0286, Reward 35.53, Accuracy 56.5%
- **`difficulty_ladder`**: Net Gain -0.0436, Reward 13.57, Accuracy 79.4%

### B. Typical Learner ($\alpha = 0.16, \lambda = 0.03$)
- **`prereq_aware_weakest`**: Net Gain **-0.0319**, Reward 31.96, Accuracy 50.2%
- **`random_eligible`**: Net Gain -0.0333, Reward 35.15, Accuracy 46.1%
- **`dueling_dqn`**: Net Gain -0.0354, Reward 33.67, Accuracy 49.9%
- **`weakest_bkt_kc`**: Net Gain -0.0350, Reward 26.85, Accuracy 46.7%
- **`difficulty_ladder`**: Net Gain -0.0680, Reward 10.83, Accuracy 70.1%

### C. Struggling Learner ($\alpha = 0.08, \lambda = 0.06$)
- **`prereq_aware_weakest`**: Net Gain **-0.0321**, Reward 26.24, Accuracy 43.7%
- **`random_eligible`**: Net Gain -0.0338, Reward 29.83, Accuracy 39.5%
- **`dueling_dqn`**: Net Gain -0.0366, Reward 27.95, Accuracy 43.8%
- **`weakest_bkt_kc`**: Net Gain -0.0352, Reward 21.65, Accuracy 40.8%
- **`difficulty_ladder`**: Net Gain -0.0664, Reward 10.84, Accuracy 62.7%

### D. Inconsistent Learner ($\alpha = 0.14, \lambda = 0.04$)
- **`random_eligible`**: Net Gain **-0.0795**, Reward 24.42, Accuracy 44.0%
- **`prereq_aware_weakest`**: Net Gain -0.0792, Reward 21.72, Accuracy 48.0%
- **`dueling_dqn`**: Net Gain -0.0801, Reward 23.70, Accuracy 47.8%
- **`weakest_bkt_kc`**: Net Gain -0.0805, Reward 17.68, Accuracy 44.8%
- **`difficulty_ladder`**: Net Gain -0.0694, Reward 10.84, Accuracy 69.8%

---

## 3. Reward Decomposition Breakdown

Mean reward component values per 25-step episode:

| Policy | Mastery Reward ($10 \Delta m$) | Entropy Reward ($0.5 H$) | ZPD Match ($0.4 e^{-gap^2}$) | Failure Penalty ($-0.8 n$) | Step Cost ($-0.05$) | Net Cumulative Reward |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`dueling_dqn`** | 21.58 | 9.32 | 6.99 | -4.42 | -1.25 | **32.22** |
| **`random_eligible`** | 22.34 | 8.87 | 5.92 | -2.16 | -1.25 | **33.72** |
| **`prereq_aware_weakest`** | 22.75 | 8.70 | 8.25 | -8.07 | -1.25 | **30.38** |
| **`weakest_bkt_kc`** | 21.63 | 8.71 | 6.27 | -9.93 | -1.25 | **25.43** |
| **`difficulty_ladder`** | 10.09 | 0.99 | 1.69 | 0.00 | -1.25 | **11.52** |

---

## 4. Key Findings & Empirical Verdict

1. **Failure to Outperform Heuristic Baselines:**  
   The trained Dueling DQN policy achieves a mean net true mastery gain of **-0.0314**, failing to exceed the pedagogical baseline `prereq_aware_weakest` (**-0.0278**) or even `random_eligible` (**-0.0292**).
2. **Reward Proxy Optimization over True Learning:**  
   Dueling DQN inflates its cumulative reward (32.22) through higher information entropy rewards (9.32) and ZPD challenge matching bonuses (6.99) while avoiding consecutive failure penalties (-4.42 vs -8.07). However, this does not yield higher true ground-truth learning gains.
3. **Decisive Integration Decision:**  
   In accordance with the pre-established research decision rules, **the Dueling DQN policy must NOT be deployed to replace the production recommender**. It is integrated strictly as an opt-in, disabled-by-default experimental demonstration and shadow evaluation endpoint (`/api/experimental/recommendation`), with automatic fallback to `prereq_aware_weakest`.
