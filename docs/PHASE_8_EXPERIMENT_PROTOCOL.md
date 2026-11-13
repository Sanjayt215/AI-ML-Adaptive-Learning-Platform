# Phase 8: Controlled Human Pilot Evaluation Protocol

**Project:** Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection  
**Platform:** AutoLearn AI Adaptive Learning Platform  
**Authors:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)  
**Protocol Version:** 1.0 (Phase 8 Formal Standard)

---

## 1. Study Rationale & Background

Synthetic simulations (Phases 3–7) demonstrated that Knowledge-Tracing-Guided RL and composite adaptive policies can optimize practice exercise selection across simulated learner archetypes. However, synthetic learners make idealized behavioral assumptions (stationary slip/guess probabilities, deterministic forgetting half-lives).

This protocol defines the formal, IRB-ready methodology for conducting a **safe, prospective, randomized controlled trial (RCT)** with real student participants.

---

## 2. Study Design & Random Assignment

```
                                [ Enrolled Participants ]
                                           |
                                [ Baseline Pre-Assessment ]
                                           |
                    +----------------------+----------------------+
                    |                      |                      |
            (Random 1:1:1:1)       (Random 1:1:1:1)       (Random 1:1:1:1)
                    |                      |                      |
                    v                      v                      v
             [ Arm 0: Control ]    [ Arm 1: Composite ]   [ Arm 2: Dueling DQN ]
             (Prereq Ladder)       (Adaptive Rule-KT)     (Deep RL - Shadow/Pilot)
                    |                      |                      |
                    +----------------------+----------------------+
                                           |
                                 [ Post-Assessment ]
                                           |
                            [ 7-Day Delayed Retention ]
```

### 2.1 Arm Definitions:
1. **Control Arm 0 (Prerequisite Difficulty Ladder):** Practice exercises presented strictly following prerequisite order and stepping up difficulty upon correct answers.
2. **Experimental Arm 1 (Composite Adaptive):** Uses Bayesian Knowledge Tracing with forgetting decay, entropy uncertainty exploration, and hysteretic difficulty recovery.
3. **Experimental Arm 2 (Dueling Double DQN):** Selects exercises using the trained 99-dimensional Dueling Double DQN policy.
4. **Experimental Arm 3 (LinUCB Contextual Bandit):** Selects exercises using Upper Confidence Bound online contextual regression.

---

## 3. Inclusion & Exclusion Criteria

### 3.1 Inclusion Criteria:
- Enrolled undergraduate or graduate computer science / engineering students.
- Novice to intermediate familiarity with basic programming.
- Ability to access the web-based AutoLearn platform.
- Provision of written informed consent.

### 3.2 Exclusion Criteria:
- Prior advanced software engineering experience or extensive competitive programming background (to avoid extreme ceiling effects).
- Inability to complete the 3-stage protocol (Pre, Practice, Post).

---

## 4. Primary and Secondary Endpoints

### 4.1 Primary Endpoint:
- **Normalized Learning Gain ($g_{norm}$):**
  $$g_{norm} = \frac{\bar{P}(L_{post}) - \bar{P}(L_{pre})}{1.0 - \bar{P}(L_{pre})}$$

### 4.2 Secondary Endpoints:
1. **7-Day Retention Rate ($R_{retention}$):** Ratio of delayed assessment score to immediate post-assessment score.
2. **Instructional Efficiency ($\eta_{ex}$):** Net mastery gained per exercise attempted.
3. **Frustration Rate:** Percentage of learning episodes triggering $\ge 3$ consecutive errors.
4. **Learner Engagement:** Average time spent per exercise and task completion rate.

---

## 5. Statistical Analysis Plan

- **Sample Size:** $N = 33$ per arm ($N_{total} = 132$), providing 80% statistical power ($\beta = 0.20$) to detect a medium-to-large effect size (Cohen's $d = 0.70$) at $\alpha = 0.05$ (two-tailed).
- **Primary Hypothesis Test:** One-way Analysis of Variance (ANOVA) on normalized learning gain across the 4 arms, followed by Tukey's Honest Significant Difference (HSD) post-hoc comparisons.
- **Safety Interims:** Data and Safety Monitoring checks performed at $N=15$ per arm. If any arm induces adverse frustration rates ($>25\%$) or negative learning gains, that arm is paused.
