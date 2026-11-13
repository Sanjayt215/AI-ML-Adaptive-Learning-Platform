# AutoLearn KT-RL Phase 7 Research & Experimentation Guide

**Project:** Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection  
**Platform:** AutoLearn AI Adaptive Learning Platform  
**Research Team:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)  
**Date:** October 2026  

---

## 1. Overview of Phase 7 Enhancements

Phase 7 introduces advanced research diagnostics, evaluation harnesses, and modular baseline policies:

1. **Long-Horizon Retention Evaluation Harness ([`services/long_horizon_eval.py`](file:///c:/Users/sanja/Downloads/autolearn_llm_ml_upgrade_ready/autolearn_fullstack/services/long_horizon_eval.py)):**  
   Simulates active learning trajectories followed by multi-day rest intervals (e.g. 7 days) to evaluate durable retained mastery.
2. **Reward Alignment & Counterfactual Diagnostics ([`services/reward_diagnostics.py`](file:///c:/Users/sanja/Downloads/autolearn_llm_ml_upgrade_ready/autolearn_fullstack/services/reward_diagnostics.py)):**  
   Decomposes raw reward components and evaluates Pearson correlation $r(\text{reward}, \Delta m_{\text{true}})$.
3. **Adaptive Exploration Controller ([`services/adaptive_exploration.py`](file:///c:/Users/sanja/Downloads/autolearn_llm_ml_upgrade_ready/autolearn_fullstack/services/adaptive_exploration.py)):**  
   Dynamically balances diagnostic assessment probes with pedagogical learning practice, strictly capping consecutive probes per KC.
4. **Contextual Bandit Baseline ([`services/contextual_bandit.py`](file:///c:/Users/sanja/Downloads/autolearn_llm_ml_upgrade_ready/autolearn_fullstack/services/contextual_bandit.py)):**  
   LinUCB linear contextual bandit with Sherman-Morrison rank-1 online updates and prerequisite action masking.
5. **Personalized Difficulty & Hysteresis Controller ([`services/recovery_controller.py`](file:///c:/Users/sanja/Downloads/autolearn_llm_ml_upgrade_ready/autolearn_fullstack/services/recovery_controller.py)):**  
   Finite state machine with anti-oscillation hysteresis (requiring 2 consecutive correct answers to step up, 2 consecutive errors to step down).
6. **Generalization & Robustness Suite ([`services/generalization_eval.py`](file:///c:/Users/sanja/Downloads/autolearn_llm_ml_upgrade_ready/autolearn_fullstack/services/generalization_eval.py)):**  
   Tests policies across unseen seeds, extended horizons ($T=40$), accelerated forgetting, and cohort shifts.

---

## 2. Research Reproduction Commands

Ensure `PYTHONPATH` points to the workspace root:
```powershell
$env:PYTHONPATH="C:\Users\sanja\Downloads\autolearn_llm_ml_upgrade_ready"
```

### 2.1 Run Full Test Suite (69 Tests)
```powershell
.\autolearn_fullstack\.venv\Scripts\python.exe -m unittest discover -s autolearn_fullstack/tests -p "test_*.py" -v
```

### 2.2 Run Long-Horizon Retention Benchmark
```powershell
.\autolearn_fullstack\.venv\Scripts\python.exe autolearn_fullstack\services\long_horizon_eval.py
```
*Outputs:* `reports/phase7_long_horizon_results.json`

### 2.3 Run Reward Alignment & Correlation Diagnostics
```powershell
.\autolearn_fullstack\.venv\Scripts\python.exe autolearn_fullstack\services\reward_diagnostics.py
```
*Outputs:* Real-time component contributions and Pearson correlations.

### 2.4 Run Generalization & Robustness Suite
```powershell
.\autolearn_fullstack\.venv\Scripts\python.exe autolearn_fullstack\services\generalization_eval.py
```
*Outputs:* `reports/phase7_generalization_results.json`

### 2.5 Run 10-Policy Comprehensive Comparison
```powershell
.\autolearn_fullstack\.venv\Scripts\python.exe autolearn_fullstack\services\evaluate_all_10_policies.py
```
*Outputs:* `reports/phase7_policy_comparison.json`

---

## 3. Key Research Conclusions

1. **Reward Alignment Insight:** Raw RL reward functions that reward static prior entropy ($H(p)$) encourage entropy-harvesting rather than true knowledge acquisition. Aligning the reward to true entropy reduction ($\Delta H$) restores a high correlation ($r = +0.78$) with learning gains.
2. **Long-Horizon Superiority:** Under longitudinal delays, prerequisite-structured baselines (`prereq_aware_weakest`) retain more durable mastery ($-0.0459$ vs $-0.0500$) than unconstrained neural policies.
3. **Out-of-Distribution Robustness:** Across all 4 perturbed environments (unseen seeds, $T=40$, struggling cohort, fast cohort), domain-structured heuristics consistently outperform unconstrained neural RL.
