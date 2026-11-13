# Learner Simulator & Reinforcement Learning Environment Specification

## 1. Overview
This specification details the architecture, mathematical formulation, action and observation spaces, prerequisite action masking, reward function, and evaluation protocol for the Reinforcement Learning environment implemented in **Phase 3 of the KT-RL Research Upgrade**.

The environment models personalized exercise selection as a Partially Observable Markov Decision Process (POMDP), where:
- The **true learner knowledge** is hidden inside the synthetic simulator.
- The **policy's observation** is derived from observable interaction history and Bayesian Knowledge Tracing (BKT) belief states.
- The **action space** represents selection from the canonical question bank.
- **Prerequisite constraints** dynamically mask ineligible actions to prevent pedagogical violations.

---

## 2. Synthetic Learner Simulator (`learner_simulator.py`)

### 2.1 Learner Archetypes
Four distinct synthetic learner profiles are modeled:

| Archetype Name | Learning Rate (\(\alpha\)) | Base Sensitivity (\(k\)) | Slip (\(P_S\)) | Guess (\(P_G\)) | Forgetting (\(\lambda\)) | Noise (\(\sigma_{\text{noise}}\)) | Description |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **`fast_learner`** | `0.28` | `3.5` | `0.04` | `0.15` | `0.01` | `0.05` | Rapid acquisition, high retention, low lapse. |
| **`typical_learner`** | `0.16` | `2.5` | `0.09` | `0.20` | `0.03` | `0.08` | Moderate learning and forgetting dynamics. |
| **`struggling_learner`** | `0.08` | `2.0` | `0.18` | `0.18` | `0.06` | `0.12` | Vulnerable to difficulty spikes, lower learning rate. |
| **`inconsistent_learner`** | `0.14` | `1.8` | `0.22` | `0.28` | `0.04` | `0.22` | High variability, lucky guesses, careless slips. |

### 2.2 Response Probability Model
Given an exercise requiring Knowledge Components \(\text{KCs}\) with difficulty \(d \in [1, 5]\):
1. Aggregated ground-truth mastery:
   \[
   m = \frac{1}{|\text{KCs}|} \sum_{kc \in \text{KCs}} m_{\text{true}}(kc)
   \]
2. Normalized item difficulty:
   \[
   d_{\text{norm}} = \frac{d}{5.5} \in [0.18, 0.91]
   \]
3. Base logit with archetype noise \(\epsilon \sim \mathcal{N}(0, \sigma_{\text{noise}}^2)\):
   \[
   z = k \cdot (m - d_{\text{norm}}) + \epsilon
   \]
4. Sigmoidal activation adjusted for slip and guess:
   \[
   P(\text{Correct}) = P_G + (1 - P_G - P_S) \cdot \frac{1}{1 + e^{-z}}
   \]
5. Response \(y \in \{0, 1\}\) sampled via seeded pseudo-random generator.

### 2.3 Learning Transition
When an exercise is attempted:
\[
m_{\text{new}} = m_{\text{old}} + \alpha_{\text{eff}} \cdot (1 - m_{\text{old}})
\]
where \(\alpha_{\text{eff}} = \alpha\) if \(y = 1\), and \(\alpha_{\text{eff}} = 0.5 \cdot \alpha\) if \(y = 0\) (reflecting instructional feedback/solution review).

### 2.4 Forgetting Model
Over simulated elapsed time \(\Delta t\):
\[
m(t + \Delta t) = m_{\min} + (m(t) - m_{\min}) \cdot e^{-\lambda \Delta t}
\]
where \(m_{\min} = 0.05\) is the retention floor.

---

## 3. RL Environment Interface (`rl_env.py`)

### 3.1 Action Space
- **Type:** Discrete(52)
- **Mapping:** Discrete index \(a \in \{0, 1, \dots, 51\}\) maps directly to the canonical question bank stably sorted by `item_id`.
- **Invariance:** Deterministic mapping preserved across all episodes and restarts.

### 3.2 Observation Space (`rl_state_encoder.py`)
- **Type:** Box(low=0.0, high=1.0, shape=(99,), dtype=float32)
- **Feature Vector Layout:**
  - `[0:30]`: Observable BKT estimated mastery \(P(K)\) for all 30 syllabus topics.
  - `[30:60]`: Normalized observation counts \(\min(n / 10, 1.0)\).
  - `[60:90]`: Binary prerequisite readiness flags (1.0 = ready, 0.0 = locked).
  - `[90:95]`: Recent correctness history window (last 5 responses; 0.5 default).
  - `[95]`: Repeated consecutive failure indicator (\(\ge 2\) failures on same topic = 1.0).
  - `[96]`: Normalized last question difficulty (\(d / 5.0\)).
  - `[97]`: Episode progress ratio (\(t / t_{\max}\)).
  - `[98]`: Global average BKT mastery across syllabus.

### 3.3 Strict Information Isolation
Hidden ground-truth simulator mastery is **never included in the observation vector**. The policy only observes BKT estimates calculated from visible response history.

### 3.4 Prerequisite Action Masking
An action mask array \(\mathbf{M} \in \{0, 1\}^{52}\) is dynamically generated:
- If an exercise's required prerequisite topics have been assessed and their observable BKT mastery \(P(K) < 0.50\), the item is **masked out (\(M_a = 0\))**.
- Foundational level-1 items remain eligible as safety recovery pathways.
- Invalid actions receive an immediate penalty reward of \(-2.0\).

---

## 4. Multi-Objective Reward Function (`rl_reward.py`)

\[
R_t = R_{\text{mastery}} + R_{\text{info}} + R_{\text{match}} + R_{\text{penalty}} + R_{\text{invalid}} + R_{\text{step}}
\]

| Component | Formula | Default Weight | Pedagogical Purpose |
| :--- | :--- | :--- | :--- |
| **Mastery Gain** | \(w_m \cdot \sum \Delta m_{\text{true}}\) | `10.0` | Primary objective: Maximizing student knowledge growth. |
| **Information Value** | \(w_i \cdot H(p)\) where \(H(p) = -p\log_2 p - (1-p)\log_2(1-p)\) | `0.5` | Encourages diagnostic exploration on uncertain topics (\(p \approx 0.5\)). |
| **ZPD Calibration** | \(w_c \cdot \exp(-(\text{prior}_m - d_{\text{norm}})^2 / 0.15)\) | `0.4` | Rewards keeping difficulty in the Zone of Proximal Development. |
| **Frustration Penalty** | \(-w_f \cdot (n_{\text{fail}} - 1)\) if \(n_{\text{fail}} \ge 2 \land y = 0\) | `0.8` | Discourages repeatedly failing a struggling student on the same topic. |
| **Invalid Penalty** | \(-w_{\text{inv}}\) if action masked | `2.0` | Enforces prerequisite constraint adherence. |
| **Step Cost** | \(-w_{\text{step}}\) | `0.05` | Encourages learning efficiency over endless repetition. |

---

## 5. Baseline Policy Diagnostics

The environment was evaluated across 4 heuristic baseline policies over 20 episodes (5 random seeds \(\times\) 4 archetypes) up to 25 steps per episode:

| Baseline Policy | Mean Mastery Gain | Mean Cumulative Reward | Accuracy | Prerequisite Violations | BKT MAE vs Hidden Truth |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`random_eligible`** | `-0.0260` | `+32.73` | `42.8%` | `0` | `0.1983` |
| **`weakest_bkt_kc`** | `-0.0273` | `+25.73` | `45.8%` | `0` | `0.1665` |
| **`difficulty_ladder`** | `-0.0587` | `+11.82` | `66.2%` | `0` | `0.2224` |
| **`prereq_aware_weakest`**| **`-0.0245`** | `+31.48` | `50.2%` | `0` | `0.1796` |

*Note: Forgetting decay (\(\lambda\)) causes passive skill decay across unexercised topics during 25-step sessions, demonstrating that focused review is required to outpace forgetting.*
