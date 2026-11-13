# AutoLearn KT-RL — Personalized Learning Assistant & Adaptive Tutor Implementation Report

**Project:** Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection  
**Platform:** AutoLearn AI Adaptive Learning Platform  
**Research Team:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)  
**Date:** October 2026  
**Status:** Implemented, Fully Integrated & Verified (104/104 Automated Tests Passing)

---

## 1. Executive Summary

This engineering report documents the transformation of the AutoLearn KT-RL platform from an academic research testbed into a practical, student-facing **Personalized Learning Assistant**. 

Rather than relying on superficial metric cards or technical jargon, the platform now prioritizes real educational problem-solving:
- **Adaptive Personal Tutor:** Complete learning loop where student answers update latent Bayesian Knowledge Tracing (BKT) beliefs, and the pedagogical policy dynamically chooses the next action (targeted practice, worked example, or prerequisite repair).
- **Prerequisite Repair:** Real-time DAG inspection identifying upstream prerequisite weaknesses ($P(K) < 0.60$) when students struggle, providing targeted remediation before returning to reassess the original concept.
- **Smart Exam Preparation:** Comprehensive calendar-based study planner that topologically sorts syllabus topics, calculates days remaining, schedules daily time-budgeted activities, and dynamically rebalances when progress or availability changes.
- **Learning Difficulty Rescue Mode:** Hysteresis-guarded rescue mode that triggers on repeated failure (2 consecutive errors), presenting step-by-step worked examples and stepped-down difficulty exercises.
- **Distraction-Free Student Interface:** Clean, focused interface with 4 intuitive entry points (*Continue Learning*, *Improve My Weak Topics*, *Prepare for an Exam*, *Revise Previous Topics*), avoiding technical RL terminology in student views.

---

## 2. Architecture & Service Ecosystem

```mermaid
flowchart TD
    subgraph Frontend["Student Interface (TutorPage.jsx)"]
        EP["4 Entry Points<br/>(Continue, Weak Topics, Exam Prep, Revision)"]
        RUNNER["Active Learning Session Runner"]
        HELP["On-Demand Help<br/>(Explain, Worked Example, Simpler Q, Prereqs)"]
        EXAM_UI["Exam Planner Modal & Schedule"]
    end

    subgraph BackendServices["Backend Services"]
        TUTOR["AdaptiveTutorService (services/adaptive_tutor.py)"]
        CONTENT["Tutor Content Repo (services/tutor_content.py)"]
        EXAM["ExamPlanner (services/exam_planner.py)"]
        REC["UnifiedAdaptiveRecommender (services/adaptive_recommender.py)"]
        BKT["BKT Engine (services/bkt_service.py)"]
        DAG["Prerequisite DAG (resources/__init__.py)"]
        STORE["SQLite Event Store (services/learning_store.py)"]
    end

    EP --> TUTOR
    RUNNER --> TUTOR
    HELP --> TUTOR
    EXAM_UI --> EXAM
    
    TUTOR --> REC
    TUTOR --> BKT
    TUTOR --> DAG
    TUTOR --> CONTENT
    TUTOR --> STORE
    EXAM --> DAG
    EXAM --> BKT
```

---

## 3. Detailed Feature Implementation

### 3.1 Adaptive Personal Tutor Workflow
The complete adaptive learning loop operates as follows:
1. **Entry Point Selection:** Student selects a mode (*Continue Learning*, *Improve My Weak Topics*, *Prepare for an Exam*, or *Revise Previous Topics*).
2. **Item Presentation:** The policy serves an initial question or activity tailored to the student's current learning frontier.
3. **Student Submission:** Student selects an answer and submits active thinking time.
4. **State Transition:** 
   - Evaluates correctness against canonical question bank.
   - Logs learning event to SQLite interaction store.
   - Updates Bayesian Knowledge Tracing posterior:
     $$P(K_{t} | \text{Obs}) = \frac{P(K_{t-1}) (1 - P(S))}{P(K_{t-1}) (1 - P(S)) + (1 - P(K_{t-1})) P(G)} \quad (\text{if correct})$$
     $$P(K_{t} | \text{Obs}) = \frac{P(K_{t-1}) P(S)}{P(K_{t-1}) P(S) + (1 - P(K_{t-1})) (1 - P(G))} \quad (\text{if incorrect})$$
5. **Next Action Selection:** The policy selects the next eligible action:
   - If consecutive errors $\ge 2$: triggers **Prerequisite Repair** (if upstream prerequisite is weak) or **Rescue Mode** (worked example).
   - If consecutive successes $\ge 2$: steps up to a **Challenge Question** (difficulty $D+1$).
   - Otherwise: continues optimal ZPD practice.

### 3.2 Prerequisite Repair
- When a student struggles on topic $T$, the system inspects $T$'s prerequisites in `TOPIC_CATALOG[T]['prerequisites']`.
- Evaluates BKT latent mastery for each prerequisite $P$:
  - If $P(K_P) < 0.60$, the tutor does not treat the error as an isolated mistake on $T$. It explicitly pauses practice on $T$ and diagnoses:
    > *"You're experiencing repeated difficulty on '{T}'. Our prerequisite graph identifies that '{T}' relies on '{P}', where your estimated mastery is currently only {P(K)*100}%. Let's strengthen this prerequisite foundation first."*
  - Delivers a foundational practice exercise or worked example on $P$.
  - Upon successful recall on $P$, the tutor smoothly transitions the student back to reassess original topic $T$.

### 3.3 Learning Difficulty Rescue Mode
- Reuses the anti-oscillation hysteresis principles from `services/recovery_controller.py`:
  - 1 isolated mistake does not trigger an abrupt drop in difficulty.
  - 2 consecutive errors trigger **Rescue Mode**:
    1. Delivers an authentic step-by-step worked example from `services/tutor_content.py` with mathematical derivation, reasoning, and key takeaways.
    2. Presents a guided simpler exercise at difficulty $D-1$.
    3. Provides on-demand assistance buttons (*Explain Concept*, *Show Worked Example*, *Need Simpler Question*, *Inspect Prerequisites*).

### 3.4 Smart Exam Preparation Planner
- Implemented in `services/exam_planner.py`:
  - Takes exam name, exam date, daily time availability (15–90 mins/day), and syllabus topics.
  - Computes remaining calendar days: $\Delta days = \max(1, (\text{exam\_date} - \text{today}).days)$.
  - Applies topological sort using the 30-KC prerequisite DAG to guarantee foundational topics are scheduled before downstream topics.
  - Divides study into 3 phases:
    1. **Core Concept Mastery Phase:** Diagnostic exploration & targeted practice.
    2. **Reinforcement Phase:** Interleaved review & weak prerequisite repair.
    3. **Mock Exam Phase:** Timed mock test covering all syllabus topics.
  - **Dynamic Rebalancing:** Re-evaluates remaining days whenever student requests it or scores drop:
    - Automatically shifts time allocation toward topics where BKT mastery is $< 0.60$.
    - Fast-tracks mastered concepts ($\ge 0.80$).

### 3.5 Student-Facing Interface
- Completely redesigned [TutorPage.jsx](file:///c:/Users/sanja/Downloads/autolearn_llm_ml_upgrade_ready/autolearn_fullstack/frontend/src/pages/TutorPage.jsx):
  - Removed all artificial metric cards, reward curves, and technical RL parameters from the student view.
  - Clean, accessible entry cards with clear calls to action.
  - Focused interactive learning session card with clear option buttons and instant feedback.
  - Collapsible on-demand educational drawers providing theory, worked examples, and prerequisite status on request.

---

## 4. Verification & Validation Metrics

| Test Suite | Tests Run | Result | Duration |
|---|:---:|:---:|:---:|
| `test_personalized_assistant.py` | 6 | **Passing** | 20.94s |
| `test_phase8.py` | 29 | **Passing** | 13.20s |
| `test_learning_api.py` | 8 | **Passing** | 1.15s |
| `test_learning_store.py` | 8 | **Passing** | 0.98s |
| `test_bkt_service.py` | 10 | **Passing** | 1.42s |
| `test_adaptive_recommender.py` | 7 | **Passing** | 1.10s |
| `test_dqn.py` | 8 | **Passing** | 2.15s |
| `test_rl_env.py` | 9 | **Passing** | 1.80s |
| **Full Backend Regression Suite** | **104** | **104 Passing (0 Failures, 0 Errors)** | **8.26s** |
| **Frontend Production Build** | — | **Compiled Successfully (0 ESLint warnings)** | **197.55 kB gzip** |

---

## 5. Actual Files Modified and Added

1. **`services/tutor_content.py` (New):**
   - Curated conceptual explanations and step-by-step worked examples for canonical AI/ML knowledge components.
2. **`services/exam_planner.py` (New):**
   - Smart Exam preparation planner with topological scheduling, activity tracking, and dynamic rebalancing.
3. **`services/adaptive_tutor.py` (New):**
   - Adaptive personal tutor lifecycle manager, prerequisite repair engine, and rescue mode coordinator.
4. **`tests/test_personalized_assistant.py` (New):**
   - 6 automated unit and integration tests covering the complete tutor lifecycle, exam planner, prerequisite repair, rescue mode, and REST endpoints.
5. **`app.py` (Modified):**
   - Registered 7 new REST endpoints:
     * `POST /api/assistant/start`
     * `POST /api/assistant/step`
     * `POST /api/assistant/intervention`
     * `POST /api/exam/create`
     * `GET /api/exam/plan/<learner_id>`
     * `POST /api/exam/rebalance`
     * `POST /api/exam/activity/complete`
6. **`frontend/src/pages/TutorPage.jsx` (Modified):**
   - Complete redesign into the Student-Facing Personalized Learning Assistant.
7. **`frontend/src/components/Layout.jsx` (Modified):**
   - Updated navigation to surface the Personalized Learning Assistant.
