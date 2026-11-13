# AutoLearn KT-RL — Frontend Feature Matrix & Integration Plan

**Project:** Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection  
**Application:** AutoLearn AI Adaptive Learning Platform  
**Research Team:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)  
**Date:** October 2026

---

## 1. Executive Summary

This feature matrix provides a systematic mapping of all core adaptive learning and research capabilities across the AutoLearn full-stack system. It identifies the responsible frontend components, associated backend endpoints, current integration status, and required upgrades to achieve full pedagogical integration, zero fabricated numbers, real-time interactive practice, and empirical research validation.

---

## 2. Comprehensive Feature Matrix

| ID | Feature Capability | Frontend Component / View | Backend Endpoint(s) | Current State | Required Upgrades & Action Plan |
|---|---|---|---|---|---|
| **F-01** | **Overall Learner Progress & Mastery** | `DashboardPage.jsx` (`StatCards`, `ProgressRing`) | `GET /api/learning/mastery/<id>`, `GET /api/context` | Displays mock/quiz-based averages; does not explicitly distinguish BKT estimated mastery from observed quiz scores. | Wire directly to live BKT mastery API. Display unassessed state when learner has 0 attempts. Add clear indicator for estimated latent probability vs empirical scores. |
| **F-02** | **Bayesian Knowledge Tracing (BKT) Latent State** | `DashboardPage.jsx` (Tab `knowledge tracing`), `HeatmapGrid.jsx` | `GET /api/learning/mastery/<id>`, `GET /api/learning/events/<id>` | Displays BKT table with P(K) values; lacks per-KC detailed inspection modal, last-practiced timestamp, and explicit labeling distinguishing latent estimates from test scores. | Add per-KC inspection drawer/modal showing prior, transition, slip, guess, evidence quality, and chronological interaction history. Explicitly label BKT as *estimated* mastery. |
| **F-03** | **Curriculum Planner & Prerequisite DAG** | `LearningPathPage.jsx`, `DashboardPage.jsx` (Tab `curriculum`) | `GET /api/curriculum/plan` | Partially wired in Dashboard; `LearningPathPage.jsx` still used legacy step layout without direct integration with dynamic DAG frontier. | Fully integrate `GET /api/curriculum/plan` into both `DashboardPage` and `LearningPathPage`. Show 4 progression stages, prerequisite lock explanations (which prerequisite is below 60% mastery), and "Practice Now" direct action. |
| **F-04** | **Real-Time Adaptive Recommendation** | `DashboardPage.jsx` (`Adaptive Next Exercise Card`), `QuizPage.jsx` | `GET /api/adaptive/recommendation`, `POST /api/quiz`, `POST /api/learning/events` | Displays recommendation card with pedagogical rationale, but requires navigating to `/quiz` to answer; no in-place practice or instant recommendation update. | Implement in-place practice flow directly on recommendation card with instant submission, feedback, and seamless next-recommendation refresh without reloading the page. |
| **F-05** | **Spaced Repetition System (SRS) Revision Plan** | `DashboardPage.jsx` (Tab `revision` / modal), `RevisionCard.jsx` | `GET /api/revision/plan` (New), `services/spaced_repetition.py` | SRS engine exists in backend (`services/spaced_repetition.py`), but lacked a dedicated frontend view or REST endpoint. | Expose `GET /api/revision/plan` in `app.py`. Build Revision Plan UI tab displaying Due-Today queue ($R(t) \le 0.85$), upcoming reviews, memory stability metrics, and direct "Review Now" trigger. |
| **F-06** | **Diagnostic Pre/Post Assessment System** | `AssessmentModal.jsx`, `DashboardPage.jsx`, `QuizPage.jsx` | `POST /api/assessment/start`, `POST /api/assessment/submit`, `GET /api/assessment/compare/<id>` | Endpoints exist in `app.py` and `assessment_service.py`, but were not accessible via an interactive UI modal or test runner. | Build dedicated Diagnostic Assessment Modal/Page. Deliver answer-concealed questions, enforce timed completion, score submissions, and display Pre vs Post comparison card with Hake's normalized gain ($g_{norm}$). |
| **F-07** | **Research Lab & Policy Comparison** | `DashboardPage.jsx` (Tab `research`), `ResearchLabPage.jsx` | `GET /api/research/benchmark` (New), `GET /api/diagnostic/calibration`, `GET /api/research/shadow_metrics`, `GET /api/research/export` | Dashboard had a small governance status card; lacked comprehensive 10-policy comparison table, calibration curves, shadow metrics, and raw research export. | Add `/api/research/benchmark` endpoint in `app.py`. Build comprehensive Research Lab tab displaying 10-policy comparison table, reward vs gain correlation, ECE calibration metrics, shadow concordance, and FERPA/IRB anonymized export. |
| **F-08** | **Adaptive Exploration & Bandit Mode** | `DashboardPage.jsx` (Recommendation strategy selector) | `GET /api/adaptive/recommendation?strategy=...` | Recommender defaults to `composite_adaptive`; UI did not allow researcher or user to select or observe comparative strategy behaviors. | Expose strategy selector in UI (`composite_adaptive`, `prereq_aware_weakest`, `forgetting_revision`, `confidence_exploration`, `frustration_remedial`) with safety-shielded DQN gating. |
| **F-09** | **Learner Persistence & Pseudonymity** | `useFlaskData.js`, `api.js`, `Layout.jsx` | `localStorage`, SQLite `learners` store | Relies on basic `localStorage` key; lacked easy learner profile switching or new learner reset. | Support persistent pseudonymous ID, active session tracking, and seamless reset to test fresh-learner empty states without corrupting test data. |
| **F-10** | **Responsive Design & Empty State Handling** | All views (`Layout.jsx`, `DashboardPage.jsx`, etc.) | Client-side error/loading states | Some components broke or displayed zero/blank cards when backend returned empty data or was loading. | Implement robust loading spinners, glassmorphism skeleton loaders, error retry buttons, and descriptive empty states for new learners. |

---

## 3. Implementation Phasing Roadmap

1. **Phase A:** Architecture & Feature Audit (Completed).
2. **Phase B & C:** Student Dashboard & Knowledge Tracing Deep Integration (Estimated mastery, KC details, recent events, empty states).
3. **Phase D:** Dynamic Curriculum & Prerequisite Path Integration (`/api/curriculum/plan`).
4. **Phase E:** In-Place Adaptive Practice & Instant Feedback Card.
5. **Phase F:** Spaced Repetition Revision Plan View (`/api/revision/plan`).
6. **Phase G:** Interactive Diagnostic Assessment Runner (`/api/assessment/*`, Hake's gain).
7. **Phase H:** Research Lab & Empirical Policy Benchmark Visualizer (`/api/research/*`, calibration, export).
8. **Phase I:** Regression Testing, Build Verification, and Final Documentation.
