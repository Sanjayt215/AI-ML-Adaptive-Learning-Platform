# AutoLearn KT-RL: Final Policy Comparison Benchmark Report

**Project:** Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection  
**Application:** AutoLearn AI Adaptive Learning Platform  
**Research Team:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)  
**Evaluation Protocol:** 100 Held-Out Evaluation Episodes (25 seeds $\times$ 4 synthetic learner archetypes, 25 steps per episode = 2,500 decision steps per policy)  
**Date:** October 20, 2026  

---

## 1. Overall Comparative Benchmark Table

| Policy / Algorithm | Mean Cumulative Reward | 95% Confidence Interval | Net True Mastery Gain | Net Gain 95% CI | Gross Learning ($\sum \Delta m$) | Accuracy (%) | Unique Items Selected (/52) | Action Selection Entropy | Prerequisite Violations | BKT MAE |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`dueling_dqn`** | 32.22 | $\pm 1.93$ | -0.0314 | $\pm 0.0079$ | +2.16 | 50.0% | 34 | 4.474 | **0** | 0.1580 |
| **`random_eligible`** | **33.72** | $\pm 1.72$ | -0.0292 | $\pm 0.0080$ | +2.23 | 46.1% | 52 | 5.679 | **0** | 0.1601 |
| **`prereq_aware_weakest`** | 30.38 | $\pm 2.45$ | **-0.0278** | $\pm 0.0085$ | **+2.28** | 50.6% | 19 | 3.522 | **0** | 0.1668 |
| **`weakest_bkt_kc`** | 25.43 | $\pm 2.54$ | -0.0305 | $\pm 0.0081$ | +2.16 | 47.2% | 17 | 3.267 | **0** | 0.1607 |
| **`difficulty_ladder`** | 11.52 | $\pm 0.58$ | -0.0619 | $\pm 0.0051$ | +1.01 | **70.5%** | 1 | 0.000 | **0** | **0.0880** |

---

## 2. Research Findings & Decision Integrity

1. **Prerequisite Safety Guarantee:** Across all 12,500 evaluated decisions across all five policies, action masking guaranteed **strictly 0 prerequisite violations**.
2. **True Mastery Comparison:** The heuristic baseline `prereq_aware_weakest` achieved the highest net true mastery gain ($-0.0278$), outperforming the trained Dueling DQN ($-0.0314$).
3. **Formal Deployment Decision:** Dueling DQN is **NOT cleared for production quiz replacement**. The production recommendation system uses the newly implemented `UnifiedAdaptiveRecommender` (`composite_adaptive`), with Dueling DQN retained exclusively as an opt-in experimental research artifact.
