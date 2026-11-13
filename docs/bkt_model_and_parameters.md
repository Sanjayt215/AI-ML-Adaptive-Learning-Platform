# Bayesian Knowledge Tracing (BKT) Model & Parameter Specification

## 1. Mathematical Foundation
Bayesian Knowledge Tracing (BKT; Corbett & Anderson, 1995) models learner knowledge as a set of distinct, binary latent variables (one per Knowledge Component, KC):

\[
K \in \{0, 1\} \quad (0 = \text{not known}, 1 = \text{known})
\]

The engine maintains a belief state representing the posterior probability that the learner has mastered the skill given their interaction history up to time step \(t\):

\[
P(K_t = 1 \mid \text{Responses}_{1:t})
\]

---

## 2. Standard Model Parameters
The single-skill BKT model is parameterized by four distinct probabilities:

| Parameter | Symbol | Initial Baseline | Description & Valid Bounds |
| :--- | :--- | :--- | :--- |
| **Initial Knowledge** | \(P(L_0)\) | `0.20` | Prior probability that a learner knows the KC prior to any assessment (\(0 \le P(L_0) \le 1\)). |
| **Learning Transition** | \(P(T)\) | `0.15` | Probability of transitioning from unmastered to mastered state after a learning opportunity (\(0 \le P(T) \le 1\)). |
| **Guess Probability** | \(P(G)\) | `0.20` | Probability that an unmastered learner answers a question correctly (\(0 \le P(G) \le 1\)). |
| **Slip Probability** | \(P(S)\) | `0.10` | Probability that a mastered learner makes an error on an exercise (\(0 \le P(S) \le 1\)). |

### Identifiability Constraint
To ensure that correct responses provide positive informational value about skill mastery and to avoid model degeneracy, the engine enforces:

\[
P(G) + P(S) < 1.0
\]

If \(P(G) + P(S) \ge 1.0\), an error would imply greater mastery than a correct response, which violates cognitive assumptions.

---

## 3. Bayesian Update Equations

### Step 1: Observation Update (Posterior Calculation)
Given the prior probability of mastery \(p = P(K_t)\):

- **If the observed response is correct (\(C\)):**
  \[
  P(K_t \mid C) = \frac{p \cdot (1 - P(S))}{p \cdot (1 - P(S)) + (1 - p) \cdot P(G)}
  \]

- **If the observed response is incorrect (\(I\)):**
  \[
  P(K_t \mid I) = \frac{p \cdot P(S)}{p \cdot P(S) + (1 - p) \cdot (1 - P(G))}
  \]

### Step 2: Learning Transition (Next Prior Calculation)
Knowledge is assumed to be an absorbing state without forgetting in standard BKT (i.e., \(P(\text{unlearn}) = 0\)):

\[
P(K_{t+1}) = P(K_t \mid \text{response}) + \left(1 - P(K_t \mid \text{response})\right) \cdot P(T)
\]

---

## 4. Multi-KC Question Approximation
When an exercise maps to multiple Knowledge Components (\(\text{KCs} = [k_1, k_2, \dots, k_m]\)):
- Each KC's mastery belief is updated **independently** using that KC's current prior and the item correctness.
- **Cognitive Limitation:** An observed error on a multi-skill item does not isolate which skill was missing, nor does a correct answer guarantee mastery of all skills (it could involve conjunctive guessing). In Phase 2, this independent update is implemented as a well-documented, testable first-order approximation.

---

## 5. Evidence Quality & Assessment Status

Mastery probability is **never presented as statistical certainty**. To prevent misleading representations:
1. **Assessment Status:**
   - `not_assessed`: 0 learner responses recorded. Mastery is shown as `—` (with prior \(P(L_0)\) shown in secondary context).
   - `assessed`: \(\ge 1\) valid responses observed.
2. **Evidence Quality Tiers:**
   - `none`: 0 observations.
   - `limited`: 1 to 4 observations (indicative trend, high sensitivity to heuristic parameters).
   - `moderate`: 5 to 9 observations.
   - `solid`: \(\ge 10\) observations.

---

## 6. Parameter Calibration Status
The current parameter set is designated as:
- **Version ID:** `bkt-heuristic-v1`
- **Calibration Status:** `is_calibrated = False` (Heuristic starting assumptions, not empirically fitted).

In future phases, parameter fitting can be executed via Expectation-Maximization (Baum-Welch algorithm) or grid-search minimization of cross-entropy on historical sequence logs.
