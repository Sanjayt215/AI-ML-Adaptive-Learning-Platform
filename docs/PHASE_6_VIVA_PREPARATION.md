# AutoLearn KT-RL Academic Viva & Oral Defense Preparation

**Project:** Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection  
**Platform:** AutoLearn AI Adaptive Learning Platform  
**Research Team:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)  
**Date:** October 2026  

---

## 1. Core Viva Questions & Model Answers

### Q1: Why combine Knowledge Tracing with Reinforcement Learning?
**Answer:**
Standard recommendation systems (collaborative filtering or matrix factorization) treat exercise recommendation as static item preference matching. In education, learning is a dynamic, non-stationary cognitive process: practicing an item changes the student's latent knowledge state.
- **Knowledge Tracing (BKT)** estimates the hidden cognitive state $P(L_t)$ from sequential observations of correct and incorrect responses.
- **Reinforcement Learning (RL)** models pedagogical sequencing as a Markov Decision Process (MDP), learning long-term policies that select exercises to maximize cumulative pedagogical value over a multi-step learning trajectory.

---

### Q2: What is Bayesian Knowledge Tracing (BKT), and how does it update mastery?
**Answer:**
BKT is a two-state Hidden Markov Model where a Knowledge Component (KC) is either learned ($L=1$) or unlearned ($L=0$). It is parameterized by four probabilities:
- $P(L_0)$: Prior probability of knowing the KC before practice (default: $0.10$).
- $P(T)$: Probability of transitioning from unlearned to learned state after a practice opportunity (default: $0.15$).
- $P(G)$: Probability of correctly guessing despite not knowing the KC (default: $0.20$).
- $P(S)$: Probability of slipping (making an error) despite knowing the KC (default: $0.10$).

Upon observing response $Y_t \in \{0, 1\}$, the posterior mastery is updated using Bayes' theorem:
$$P(L_t \mid Y_t = 1) = \frac{P(L_{t-1})(1 - P(S))}{P(L_{t-1})(1 - P(S)) + (1 - P(L_{t-1}))P(G)}$$
$$P(L_t \mid Y_t = 0) = \frac{P(L_{t-1})P(S)}{P(L_{t-1})P(S) + (1 - P(L_{t-1}))(1 - P(G))}$$
Then the transition step for the next opportunity is applied:
$$P(L_{t+1}) = P(L_t \mid Y_t) + (1 - P(L_t \mid Y_t)) P(T)$$

---

### Q3: Why use a Dueling Deep Q-Network (Dueling DQN)?
**Answer:**
In many educational states, the general quality of the learning state (e.g., student being in an active, receptive Zone of Proximal Development) is more critical than the fine-grained choice among several equivalent exercises.
A standard DQN estimates $Q(s, a)$ directly, requiring extensive samples to update state representations for each action. The Dueling architecture decouples state evaluation from action advantages:
$$Q(s, a) = V(s; \theta, \beta) + \left( A(s, a; \theta, \alpha) - \frac{1}{|\mathcal{A}|} \sum_{a'} A(s, a'; \theta, \alpha) \right)$$
- $V(s)$: Scalar value of being in learner state $s$.
- $A(s, a)$: Relative advantage of choosing exercise $a$.
This reduces gradient variance, accelerates learning, and stabilizes Q-value estimates across large action spaces.

---

### Q4: What are the State, Action, and Reward in this project?
**Answer:**
- **State Space (99 continuous dimensions):**
  - Slices `[0:30]`: BKT estimated mastery for all 30 curriculum KCs.
  - Slices `[30:60]`: Normalized practice counts per KC ($\min(1.0, \text{attempts}/10)$).
  - Slices `[60:90]`: Prerequisite readiness binary flags ($1.0$ if all prerequisites $\ge 0.60$).
  - Slices `[90:95]`: Sliding window of last 5 question indices.
  - Slice `[95]`: Consecutive topic failure count ($\min(1.0, \text{streak}/5)$).
  - Slice `[96]`: Last item difficulty ($0.25, 0.50, 1.0$).
  - Slice `[97]`: Episode progress fraction ($t / T_{\text{max}}$).
  - Slice `[98]`: Global curriculum mean mastery.
- **Action Space:** Discrete choice of 52 canonical exercises (`Discrete(52)`).
- **Reward Function:** Multi-objective composite formulation:
  $$r_t = 2.0 \, \Delta m_t + 0.5 \, R_{\text{zpd}} + 0.3 \, \Delta H_t + 0.1 \, R_{\text{acc}} - 0.3 \, R_{\text{rep}} - 1.0 \, R_{\text{prereq}}$$

---

### Q5: How is Prerequisite Action Masking implemented, and why is it necessary?
**Answer:**
A question is eligible if and only if all prerequisite KCs for its topic have an estimated BKT mastery $\ge 0.60$.
During action selection, invalid actions are masked by setting their policy logits to a large negative constant ($-10^9$):
$$Q_{\text{masked}}(s, a) = Q(s, a) \quad \text{if } a \in \mathcal{A}_{\text{valid}} \quad \text{else} \quad -10^9$$
During training, the Double DQN target calculation also masks future actions so the agent never backs up Q-values from illegal transitions.
**Why necessary:** In our Phase 5 ablation study, unmasked selection resulted in **93 prerequisite violations** per evaluation run and caused cumulative reward to collapse from $33.27$ to $18.46$. Action masking guarantees **0 prerequisite violations**.

---

### Q6: What are the Forgetting, Uncertainty, and Frustration-Risk indicators?
**Answer:**
1. **Longitudinal Forgetting Decay ($R(t)$):**
   $$R(t) = m_{\text{floor}} + (P(K) - m_{\text{floor}}) \cdot e^{-\lambda \Delta t}$$
   Models memory retention using an exponential decay bounded by a cognitive floor ($0.10$).
2. **Posterior Uncertainty via Shannon Entropy ($H(p)$):**
   $$H(p) = -p \log_2(p) - (1-p) \log_2(1-p)$$
   Measures diagnostic uncertainty, peaking at $p = 0.50$ (maximum entropy $1.0$).
3. **Frustration-Risk Detector:**
   Sequentially tracks consecutive errors on a topic. When consecutive failures $\ge 2$, it flags disengagement risk and triggers a difficulty downgrade (e.g., `hard` $\to$ `medium`) and prerequisite remediation.

---

### Q7: Why did the Dueling DQN not outperform the heuristic baseline?
**Answer:**
This is an important scientific finding from Phase 5 and Phase 6:
1. **Reward Function Proxy Exploitation:** The agent optimized cumulative reward ($32.22$) by repeatedly sampling items that maximize the Shannon entropy bonus ($+0.3 \Delta H$) and the ZPD Gaussian bonus ($+0.5 R_{\text{zpd}}$), rather than driving net true knowledge acquisition.
2. **Sparse Horizon:** In fixed 25-step simulated sessions across 30 KCs, the greedy heuristic `prereq_aware_weakest` systematically targets the exact lowest foundational gaps, producing $+2.28$ gross learning vs $+2.16$ for DQN.
3. **Exploration Inefficiency:** Deep RL requires thousands of environment steps to generalize across 4 diverse archetypes; a rule-based prerequisite tree operates optimally from step 1.

---

### Q8: What does negative net mastery gain mean in the simulator?
**Answer:**
In the synthetic simulator environment, latent knowledge decays continuously over time across all 30 KCs due to simulated forgetting ($\Delta t$). While the learner gains $+2.16$ units of gross knowledge on practiced topics, the remaining 29 unpracticed topics experience natural passive decay during the 25-step session.
The negative net gain ($-0.029$ across all 30 KCs) simply reflects the net balance between active practice gains and passive macro-curriculum decay over the simulated time window.

---

### Q9: Why is gross learning different from net mastery gain?
**Answer:**
- **Gross Learning ($\Delta M_{\text{gross}} = \sum \max(0, m_{t+1} - m_t)$):** Sums only the positive knowledge increases directly caused by practice interventions.
- **Net Mastery Gain ($\Delta M_{\text{net}} = \bar{M}_{\text{end}} - \bar{M}_{\text{start}}$):** Evaluates overall curriculum mastery change, which includes the subtractive effect of simulated forgetting across unpracticed topics.

---

### Q10: How do the automated tests establish software correctness?
**Answer:**
The test suite consists of **59 automated tests** covering:
- Unit tests for BKT formulas with hand-calculated expected values.
- Monotonicity checks verifying that response accuracy increases with mastery.
- Checkpoint saving/reloading roundtrip validation.
- Replay determinism verifying identical mastery from the same event history.
- Dynamic action masking verification guaranteeing zero illegal action selections.
- Live HTTP integration tests asserting API contracts, status codes, and schema compliance.

---

### Q11: Why are simulation results not proof of real-world educational effectiveness?
**Answer:**
A synthetic simulator relies on idealized mathematical assumptions (logistic probability of success, stationary transition probabilities, exponential forgetting). Human students exhibit complex affective factors, motivation shifts, fatigue, prior background knowledge, and diverse learning speeds.
Therefore, simulation benchmarks demonstrate **algorithmic convergence, policy properties, and software correctness**, but **do not prove real-world pedagogical efficacy**.

---

### Q12: Why is the experimental DQN policy disabled by default (`KT_RL_EXPERIMENT_ENABLED=0`)?
**Answer:**
Responsible AI engineering principles dictate that an AI model should only be deployed to live users if it has demonstrated statistically significant superiority over established baselines.
Because Dueling DQN did not outperform `prereq_aware_weakest` in true learning gains, deploying it to production would risk degrading student learning. Keeping it disabled by default protects student learning while allowing researchers to evaluate the model safely in sandbox mode.

---

### Q13: What would be required for a valid real-learner evaluation?
**Answer:**
1. **Institutional Review Board (IRB) / Ethics Approval** for educational research on human subjects.
2. **Randomized Controlled Trial (A/B Test)**: Randomly assigning consenting learners to a control group (prerequisite baseline) vs an experimental group (adaptive policy).
3. **Pre-test and Post-test Assessments** measuring genuine learning gain using identical standardized test items before and after the learning intervention.
4. **Affective & Usability Surveys** evaluating learner engagement, self-reported frustration, and perceived challenge.
5. **Statistical Significance Testing** (e.g., paired t-tests or Mann-Whitney U tests) to confirm that observed learning differences did not occur by chance.
