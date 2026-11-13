# Model Card: Knowledge-Tracing-Guided Dueling Deep Q-Network (KT-RL)

**Model Identifier:** `dueling_dqn_final.pt`  
**Model Architecture:** Dueling Double Deep Q-Network with Prerequisite Action Masking  
**Version:** `kt_rl_dueling_dqn_v1.0-final`  
**Authors:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)  
**Affiliation:** AutoLearn AI Adaptive Learning Platform  
**Date:** October 2026  
**License / Access:** Internal Academic Research / Experimental Sandbox  

---

## 1. Executive Summary & Production Status

| Metric / Dimension | Specification / Value |
| :--- | :--- |
| **Model Type** | Dueling Double Deep Q-Network with Dynamic Prerequisite Masking |
| **Primary Task** | Sequential Exercise Item Selection for Personalized Learning Paths |
| **Observation Space** | 99-dimensional continuous feature vector (BKT mastery, attempts, readiness, recent history, entropy, frustration flags) |
| **Action Space** | Discrete(52) canonical question items covering 30 Knowledge Components |
| **Training Scheme** | 120 episodes (3,000 interaction steps), 4 synthetic learner archetypes |
| **Deployment Gate Status** | **RESTRICTED TO SANDBOX / SHADOW MODE (`KT_RL_EXPERIMENT_ENABLED=0`)** |
| **Recommended Production Recommender** | `AdaptiveRecommender` (`composite_adaptive` / `prereq_aware_weakest`) |

### Deployment Decision Rationale
In accordance with pre-established empirical safety and gating criteria:
1. **True Mastery Superiority:** In the rigorous 100-episode held-out benchmark, Dueling DQN achieved a net true mastery gain of $-0.0314 \pm 0.0079$, failing to surpass the heuristic baseline `prereq_aware_weakest` ($-0.0278 \pm 0.0085$).
2. **Gross Learning Gain:** The baseline generated $+2.28 \pm 0.44$ units of simulated gross knowledge acquisition, compared to $+2.16 \pm 0.42$ for Dueling DQN.
3. **Reward Exploitation:** Dueling DQN achieved higher cumulative reward ($32.22$ vs $30.38$) primarily by optimizing state entropy diagnostic bonuses and ZPD Gaussian proximity rather than driving superior true learning.
4. **Safety & Zero-Disruption Mandate:** The model is permanently safeguarded behind `KT_RL_EXPERIMENT_ENABLED=0` to ensure real student accounts on `/api/quiz` receive zero untrusted policy interventions.

---

## 2. Intended Use & Boundaries

### 2.1 Intended Use Cases
- **Research Benchmarking:** Offline comparison of RL-guided vs heuristic-guided pedagogical sequencing.
- **Shadow Mode Evaluation:** Comparing offline recommendation choices of RL vs classical rules without student impact.
- **Diagnostics Sandbox:** Simulating learner trajectories across diverse student personas (`fast_learner`, `typical_learner`, `struggling_learner`, `inconsistent_learner`).

### 2.2 Out-of-Scope & Prohibited Uses
- **Direct Unsupervised Production Routing:** The model must **NOT** replace standard quiz selection or learning path progression for real students.
- **High-Stakes Assessment:** Must not be used for grading, placement decisions, or formal evaluation.
- **Unconstrained Action Selection:** Must never be queried without the dynamic prerequisite mask; unmasked evaluation leads to curriculum invalidity (4.65 violations/episode).

---

## 3. Network Architecture & Mathematical Formulation

### 3.1 Network Topology
```
                  Observation Vector s in R^99
                               |
                   Dense Linear(99 -> 128)
                               |
                       LayerNorm + ReLU
                               |
                   Dense Linear(128 -> 128)
                               |
                       LayerNorm + ReLU
                               |
              +----------------+----------------+
              |                                 |
     State-Value Stream                 Advantage Stream
    Linear(128 -> 64)                  Linear(128 -> 64)
           ReLU                              ReLU
    Linear(64 -> 1)                    Linear(64 -> 52)
           |                                 |
         V(s)                              A(s, a)
           |                                 |
           +----------------+----------------+
                            |
                 Dueling Aggregation Layer
                            |
           Q(s, a) = V(s) + [A(s, a) - (1/|A|) sum(A)]
                            |
               Action Masking Layer (-10^9)
                            |
                 Masked Q-Values Q_m(s, a)
```

### 3.2 Dueling Q-Value Aggregation
The dueling architecture decouples the scalar value of the student state from the advantage of each individual exercise:
$$Q(s, a; \theta, \alpha, \beta) = V(s; \theta, \beta) + \left( A(s, a; \theta, \alpha) - \frac{1}{|\mathcal{A}|} \sum_{a' \in \mathcal{A}} A(s, a'; \theta, \alpha) \right)$$
where $\theta$ denotes shared representation parameters, $\beta$ denotes value stream parameters, and $\alpha$ denotes advantage stream parameters.

### 3.3 Double Q-Learning Bellman Target
To mitigate positive maximization bias in standard Q-learning, Double DQN targets are computed using the online network for action selection and the target network for action evaluation:
$$a^* = \arg\max_{a' \in \mathcal{A}_{\text{valid}}} Q(s_{t+1}, a'; \theta)$$
$$y_t = r_t + \gamma \, Q(s_{t+1}, a^*; \theta^-) \, (1 - d_t)$$
where $\theta^-$ denotes the periodic frozen target network parameters and $\mathcal{A}_{\text{valid}}$ is the set of prerequisite-eligible questions.

---

## 4. Training Specifications & Hyperparameters

| Hyperparameter | Value | Description |
| :--- | :--- | :--- |
| **Optimizer** | Adam | Standard adaptive moment estimation |
| **Learning Rate** | $3 \times 10^{-4}$ | Constant throughout training |
| **Batch Size** | 64 | Uniform mini-batch sampling from replay buffer |
| **Replay Capacity** | 20,000 transitions | Ring buffer storing $(s, a, r, s', d, \text{mask})$ |
| **Warmup Transitions** | 375 steps (15 episodes) | Random eligible exploratory actions before gradient steps |
| **Discount Factor ($\gamma$)** | 0.99 | Long-term horizon for multi-step mastery growth |
| **Target Update Period** | 150 training steps | Hard parameter sync ($\theta^- \leftarrow \theta$) |
| **Gradient Clipping** | Max norm 1.0 | Prevents gradient explosion during reward spikes |
| **Loss Function** | Smooth L1 (Huber Loss) | Linear for large errors, quadratic for small errors |
| **Epsilon Schedule** | $1.0 \to 0.05$ | Linear decay over 2,000 training steps |
| **Episode Length** | 25 steps | Maximum questions presented per simulated session |
| **Total Episodes** | 120 | 3,000 environment interaction steps |

---

## 5. Multi-Objective Reward Formulation

The step reward $r_t$ balances 6 educational and diagnostic objectives:
$$r_t = w_{\text{gain}} \Delta m_t + w_{\text{zpd}} R_{\text{zpd}}(s, a) + w_{\text{ent}} \Delta H_t + w_{\text{acc}} R_{\text{acc}} + w_{\text{rep}} R_{\text{rep}} + w_{\text{prereq}} R_{\text{prereq}}$$

1. **Mastery Gain ($\Delta m_t$):** Change in the primary KC's BKT probability: $\Delta m_t = P(L_{t+1}) - P(L_t)$. Weight: $+2.0$.
2. **Zone of Proximal Development ($R_{\text{zpd}}$):** Gaussian bonus peaking at student mastery $= 0.55$:
   $$R_{\text{zpd}} = \exp\left( - \frac{(P(L_t) - 0.55)^2}{2 \times 0.20^2} \right) - 0.20$$
   Weight: $+0.5$.
3. **Entropy / Diagnostic Reduction ($\Delta H_t$):** Reduction in posterior knowledge uncertainty:
   $$\Delta H_t = H(P(L_t)) - H(P(L_{t+1}))$$
   where $H(p) = -p \log_2(p) - (1-p) \log_2(1-p)$. Weight: $+0.3$.
4. **Accuracy / Success Incentive ($R_{\text{acc}}$):** $+0.1$ for correct answers, $-0.1$ for incorrect answers.
5. **Repetition Penalty ($R_{\text{rep}}$):** $-0.3$ per repeated selection of the identical question within the sliding history window.
6. **Prerequisite Violation Penalty ($R_{\text{prereq}}$):** $-1.0$ (never triggered when action masking is active).

---

## 6. Comprehensive Benchmark & Evaluation Results

### 6.1 100-Episode Held-Out Benchmark (25 Seeds $\times$ 4 Archetypes)

| Evaluation Metric | Dueling DQN | `prereq_aware_weakest` | `random_eligible` | `weakest_bkt_kc` | `difficulty_ladder` |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Cumulative Reward** | $32.22 \pm 1.93$ | $30.38 \pm 2.45$ | $\mathbf{33.72 \pm 1.72}$ | $27.91 \pm 2.48$ | $13.56 \pm 1.54$ |
| **Net True Mastery Gain** | $-0.0314 \pm 0.0079$ | $\mathbf{-0.0278 \pm 0.0085}$ | $-0.0292 \pm 0.0080$ | $-0.0289 \pm 0.0082$ | $-0.0612 \pm 0.0041$ |
| **Gross Learning (Units)** | $+2.16 \pm 0.42$ | $\mathbf{+2.28 \pm 0.44}$ | $+2.08 \pm 0.40$ | $+2.24 \pm 0.43$ | $+1.42 \pm 0.31$ |
| **Response Accuracy** | $50.0\% \pm 3.1\%$ | $\mathbf{50.6\% \pm 3.5\%}$ | $46.1\% \pm 3.2\%$ | $49.2\% \pm 3.4\%$ | $67.4\% \pm 2.8\%$ |
| **Prerequisite Violations** | **0** | **0** | **0** | **0** | **0** |
| **BKT State MAE** | $0.1524 \pm 0.012$ | $0.1610 \pm 0.014$ | $0.1582 \pm 0.013$ | $0.1645 \pm 0.015$ | $\mathbf{0.1120 \pm 0.010}$ |

### 6.2 Ablation Study Analysis

| Ablation Condition | Mean Reward | Net Mastery Gain | Prerequisite Violations | Key Insight |
| :--- | :---: | :---: | :---: | :--- |
| **Full Dueling DQN + Double DQN** | **32.22** | -0.0314 | **0** | Lowest Q-value overestimation bias; stable policy. |
| **Standard DQN (No Double Q)** | 27.15 | -0.0335 | **0** | Vulnerable to overoptimistic action value estimates. |
| **Unmasked Action Selection** | 18.46 | -0.0410 | **93** (4.65/ep) | Demonstrates absolute necessity of prerequisite masking. |
| **Zero Entropy Reward ($w_{\text{ent}} = 0$)** | 29.80 | -0.0320 | **0** | Reduces exploration of uncertain KCs. |
| **Zero ZPD Reward ($w_{\text{zpd}} = 0$)** | 28.45 | -0.0352 | **0** | Leads to poor challenge-level matching for students. |

---

## 7. Artifacts & Checkpoints

- **Model Weights:** `autolearn_fullstack/models/dqn/dueling_dqn_final.pt` (PyTorch state dict).
- **Training Code:** `autolearn_fullstack/train_dqn.py`.
- **Environment & State Encoder:** `autolearn_fullstack/rl_env.py`, `autolearn_fullstack/rl_state_encoder.py`.
- **Evaluation Scripts:** `autolearn_fullstack/phase5_ablation.py`, `autolearn_fullstack/eval_benchmark_100ep.py`.
- **Diagnostics & Results:** `autolearn_fullstack/reports/kt_rl_final_benchmark.json`, `autolearn_fullstack/reports/phase5_ablation_results.json`.
