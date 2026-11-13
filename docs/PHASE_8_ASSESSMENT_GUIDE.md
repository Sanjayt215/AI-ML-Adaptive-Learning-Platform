# Phase 8: Pre-Assessment & Post-Assessment Implementation Guide

**Project:** Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection  
**Platform:** AutoLearn AI Adaptive Learning Platform  
**Authors:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)

---

## 1. Overview & Purpose

The **Assessment Framework** provides an objective, scientifically rigorous mechanism to evaluate learner knowledge state prior to instruction (**Pre-Assessment**), immediately following adaptive practice (**Post-Assessment**), and after an extended retention interval (**Delayed Retention Assessment**).

This enables:
1. Valid estimation of baseline learner priors without relying exclusively on self-reporting.
2. Direct calculation of normalized learning gains (Hake's $g$) and net mastery shifts.
3. Verification of long-term knowledge retention.
4. Objective comparison of recommendation policies in future human trials.

---

## 2. Assessment Structure & Construction

### 2.1 Stratified Item Selection

Assessments are dynamically assembled from the canonical 52-question bank (`autolearn_fullstack/resources.py`) using stratified sampling across the curriculum:
- **Default Length:** 10 questions (configurable between 3 and 20).
- **Topic Coverage:** Items are selected round-robin across core topics (`python_basics`, `loops_control_flow`, `functions_modules`, `data_structures`, `algorithms_recursion`).
- **Answer Concealment:** The client payload strictly excludes `correct_answer` or internal flags. Solutions are evaluated server-side upon submission.

### 2.2 Lifecycle & Session States

Assessment sessions transition through a strict state machine:
```
[Start Session] ---> in_progress ---> (Student Submits) ---> completed
                           |
                           +--------> (Timeout > 60m) ------> abandoned
```

- **`in_progress`:** Session active, questions rendered to learner.
- **`completed`:** Answers received, scored, and persisted.
- **`abandoned`:** Session exceeded 60-minute cutoff or was superseded. Incomplete attempts never pollute BKT active history.

---

## 3. REST API Endpoints

### 3.1 Start Assessment
- **Endpoint:** `POST /api/assessment/start`
- **Request Body:**
  ```json
  {
    "user_id": "student_01",
    "assessment_type": "pre",
    "num_questions": 10
  }
  ```
- **Response:**
  ```json
  {
    "status": "success",
    "assessment": {
      "assessment_id": "asm_a1b2c3d4e5f6",
      "learner_id": "student_01",
      "assessment_type": "pre",
      "status": "in_progress",
      "num_questions": 10,
      "questions": [
        {
          "item_id": "py_var_01",
          "question": "What is the output of print(type(42))?",
          "options": ["<class 'int'>", "<class 'str'>", "<class 'float'>", "Error"],
          "difficulty": 1,
          "knowledge_components": ["py_var_types"],
          "topic": "python_basics"
        }
      ],
      "started_at": "2026-10-23T14:30:00Z",
      "timeout_minutes": 60
    }
  }
  ```

### 3.2 Submit Assessment
- **Endpoint:** `POST /api/assessment/submit`
- **Request Body:**
  ```json
  {
    "assessment_id": "asm_a1b2c3d4e5f6",
    "responses": [
      {
        "item_id": "py_var_01",
        "selected_option": "<class 'int'>",
        "time_spent_ms": 3200
      }
    ]
  }
  ```
- **Response:**
  ```json
  {
    "status": "success",
    "results": {
      "assessment_id": "asm_a1b2c3d4e5f6",
      "learner_id": "student_01",
      "score": 8,
      "total_questions": 10,
      "accuracy": 0.80,
      "duration_seconds": 184.2,
      "kc_scores": {
        "py_var_types": {
          "score": 1,
          "total": 1,
          "mastery_estimate": 1.0
        }
      }
    }
  }
  ```

### 3.3 Assessment Comparison & Progress
- **Endpoint:** `GET /api/assessment/compare/<learner_id>`
- **Response:**
  ```json
  {
    "status": "success",
    "comparison": {
      "has_comparison": true,
      "learner_id": "student_01",
      "metrics": {
        "gross_learning_gain": 0.40,
        "normalized_learning_gain": 0.571429,
        "net_mastery_delta": 3,
        "exercise_efficiency": 0.04
      },
      "explanation": "Learner 'student_01' demonstrated a gross accuracy gain of +40.0%, with a normalized learning gain (Hake's g) of 0.57..."
    }
  }
  ```

---

## 4. Integration with Bayesian Knowledge Tracing (BKT)

1. **Pre-Assessment Prior Calibration:** Pre-assessment accuracy across individual KCs can optionally initialize the $P(L_0)$ parameters for the learner, accelerating adaptive convergence.
2. **Post-Assessment Validation:** Post-assessment serves as an external, unassisted ground truth check on whether BKT model beliefs correspond to genuine unassisted student capability.
