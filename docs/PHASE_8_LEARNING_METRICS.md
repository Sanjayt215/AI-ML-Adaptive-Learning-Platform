# Phase 8: Formal Learning Progress & Evaluation Metrics Specification

**Project:** Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection  
**Platform:** AutoLearn AI Adaptive Learning Platform  
**Authors:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)  
**Standard Version:** 1.0 (Phase 8 Formal Release)

---

## 1. Purpose & Scope

This specification establishes the mathematical foundations, edge-case handlers, and standardized measurement procedures for evaluating learner knowledge acquisition, retention, and instructional efficiency.

These metrics govern:
1. Synthetic benchmark evaluations across simulated learner archetypes.
2. Offline shadow evaluation comparing recommendation policies.
3. Future authorized human pilot evaluations with pre/post assessment workflows.

---

## 2. Mathematical Formulations

Let:
- $\mathcal{K} = \{1, 2, \dots, K\}$ denote the set of Knowledge Components under evaluation ($|\mathcal{K}| = K$).
- $P(L_{k, pre}) \in [0, 1]$ denote the estimated mastery probability for KC $k$ at pre-assessment.
- $P(L_{k, post}) \in [0, 1]$ denote the estimated mastery probability for KC $k$ immediately following the learning sequence.
- $P(L_{k, delayed}) \in [0, 1]$ denote the estimated mastery probability at a delayed retention assessment.
- $\bar{P}(L) = \frac{1}{|\mathcal{K}|} \sum_{k \in \mathcal{K}} P(L_k)$ denote the macro-averaged mastery probability across the target curriculum.
- $\tau \in [0.75, 0.95]$ denote the binary mastery threshold (canonical default: $\tau = 0.80$).
- $N_{exercises} \in \mathbb{N}_{\ge 0}$ denote the total number of practice exercises completed between pre- and post-assessment.
- $\Delta t_{min} > 0$ denote the total learning time elapsed in active practice (in minutes).

---

### 2.1 Gross Learning Gain ($g_{gross}$)

The absolute change in average mastery probability:

$$g_{gross} = \bar{P}(L_{post}) - \bar{P}(L_{pre})$$

- **Domain:** $[-1.0, +1.0]$
- **Interpretation:** Positive values indicate knowledge growth; negative values indicate forgetting or deterioration.
- **Edge cases:** If pre and post are identical, $g_{gross} = 0.0$.

---

### 2.2 Normalized Learning Gain ($g_{norm}$ — Hake's Gain)

Quantifies the proportion of potential mastery headroom realized by the learner:

$$g_{norm} = \begin{cases}
\frac{\bar{P}(L_{post}) - \bar{P}(L_{pre})}{1.0 - \bar{P}(L_{pre})}, & \text{if } \bar{P}(L_{pre}) < 1.0 - \epsilon \text{ and } \bar{P}(L_{post}) \ge \bar{P}(L_{pre}) \\
\frac{\bar{P}(L_{post}) - \bar{P}(L_{pre})}{\bar{P}(L_{pre})}, & \text{if } \bar{P}(L_{pre}) > \epsilon \text{ and } \bar{P}(L_{post}) < \bar{P}(L_{pre}) \\
0.0, & \text{otherwise}
\end{cases}$$

- **Numerical Tolerance:** $\epsilon = 10^{-6}$.
- **Safe Divisor Rule:** If $|1.0 - \bar{P}(L_{pre})| < \epsilon$, headroom is zero; return $0.0$ to prevent floating-point division by zero.
- **Interpretation:**
  - High gain: $g_{norm} \ge 0.7$
  - Medium gain: $0.3 \le g_{norm} < 0.7$
  - Low gain: $g_{norm} < 0.3$

---

### 2.3 Net Binary Mastery Delta ($\Delta M$)

Measures the increase in the number of discrete KCs meeting or exceeding the mastery threshold $\tau$:

$$M_k(t) = \begin{cases} 1, & P(L_k(t)) \ge \tau \\ 0, & P(L_k(t)) < \tau \end{cases}$$

$$M_{total}(t) = \sum_{k \in \mathcal{K}} M_k(t)$$

$$\Delta M = M_{total, post} - M_{total, pre}$$

The normalized fractional mastery rate shift is:

$$\Delta m = \frac{\Delta M}{K} \in [-1.0, +1.0]$$

---

### 2.4 Retention Metrics ($R_{retention}$ and $g_{ret}$)

Evaluates retention stability after a retention interval (e.g., 24 hours, 7 days):

#### Retention Rate ($R_{retention}$)

$$R_{retention} = \begin{cases}
\frac{\bar{P}(L_{delayed})}{\bar{P}(L_{post})}, & \text{if } \bar{P}(L_{post}) > \epsilon \\
1.0, & \text{if } \bar{P}(L_{post}) \le \epsilon \text{ and } \bar{P}(L_{delayed}) \le \epsilon \\
0.0, & \text{otherwise}
\end{cases}$$

#### Retained Mastery Gain ($g_{ret}$)

$$g_{ret} = \bar{P}(L_{delayed}) - \bar{P}(L_{pre})$$

#### Normalized Retained Gain ($g_{ret\_norm}$)

$$g_{ret\_norm} = \begin{cases}
\frac{\bar{P}(L_{delayed}) - \bar{P}(L_{pre})}{1.0 - \bar{P}(L_{pre})}, & \text{if } \bar{P}(L_{pre}) < 1.0 - \epsilon \\
0.0, & \text{otherwise}
\end{cases}$$

---

### 2.5 Instructional Efficiency Metrics ($\eta_{ex}, \eta_{time}$)

Measures mastery acquired per unit of learner effort:

#### Exercise Efficiency ($\eta_{ex}$)

$$\eta_{ex} = \begin{cases}
\frac{g_{gross}}{N_{exercises}}, & \text{if } N_{exercises} > 0 \\
0.0, & \text{otherwise}
\end{cases}$$

#### Time Efficiency ($\eta_{time}$)

$$\eta_{time} = \begin{cases}
\frac{g_{gross}}{\Delta t_{min}}, & \text{if } \Delta t_{min} > 0 \\
0.0, & \text{otherwise}
\end{cases}$$

---

### 2.6 Frustration & Remediation Performance

#### Frustration Incidence Rate ($r_{frust}$)

A frustration event is triggered when a learner experiences $C \ge 3$ consecutive incorrect responses.

$$r_{frust} = \frac{N_{frustration\_triggers}}{N_{total\_episodes}}$$

#### Remediation Success Rate ($r_{remed}$)

For episodes where the Recovery Controller entered `CAUTION` or `RECOVERY`, the proportion where the learner regained mastery/correctness within $\le 2$ practice steps:

$$r_{remed} = \begin{cases}
\frac{N_{successful\_recoveries}}{N_{remediation\_episodes}}, & \text{if } N_{remediation\_episodes} > 0 \\
1.0, & \text{if } N_{remediation\_episodes} = 0 \text{ (zero failures)}
\end{cases}$$

---

## 3. Summary of Edge-Case Safeguards

| Metric | Trigger Condition | Handled Return Value | Safety Justification |
| :--- | :--- | :--- | :--- |
| **Normalized Gain** | $P(L_{pre}) = 1.0$ | $0.0$ | Ceiling effect: no further headroom to improve |
| **Normalized Gain** | $P(L_{post}) < P(L_{pre})$ | $(P_{post} - P_{pre}) / P_{pre}$ | Negative gain correctly reflects relative skill loss |
| **Retention Rate** | $P(L_{post}) = 0.0$ | $1.0$ (if $P_{delayed}=0$), else $0.0$ | Eliminates division by zero; unlearned material retained at zero |
| **Exercise Efficiency** | $N_{exercises} = 0$ | $0.0$ | Learner completed no exercises; undefined efficiency sets to zero |
| **Time Efficiency** | $\Delta t_{min} \le 0$ | $0.0$ | Zero duration records return safe zero |
| **Remediation Success** | $N_{remediation} = 0$ | $1.0$ (or null if flagged) | Zero frustration is optimal educational outcome |

---

## 4. Benchmark Metric Validation Reference Table

The mathematical formulas defined in this document are verified against test vectors codified in `reports/phase8_metric_validation.json`.
