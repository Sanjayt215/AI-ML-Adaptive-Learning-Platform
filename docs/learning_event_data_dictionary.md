# AutoLearn Learning Event & Session Data Dictionary

## 1. Overview
This document specifies the relational data model, schemas, field types, validation constraints, and serialization formats for the persistent learner interaction storage introduced in **Phase 1 of the Knowledge-Tracing-Guided Reinforcement Learning (KT-RL) Upgrade**.

The interaction infrastructure persists fine-grained behavioral interactions to standard-library SQLite (`autolearn_fullstack/data/autolearn_learning.db`) while keeping full backward compatibility with the existing diagnostic quiz, scoring pipeline, and AutoML models.

---

## 2. Table: `learning_sessions`

Represents an individual student practice session or diagnostic assessment block.

| Column Name | SQLite Type | Python Type | Nullable | Description / Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `session_id` | `TEXT` | `str` | NO | Primary Key. Formatted as `sess_<uuid12>`. Unique session identifier. |
| `learner_id` | `TEXT` | `str` | NO | Indexed. Pseudonymous learner identifier (e.g. `learner_<uuid12>`). |
| `started_at` | `TEXT` | `str` | NO | ISO 8601 UTC timestamp of session creation (e.g. `2026-10-13T16:00:00.000000+00:00`). |
| `ended_at` | `TEXT` | `str` | YES | ISO 8601 UTC timestamp of session completion or termination. `NULL` while in progress. |
| `session_type` | `TEXT` | `str` | NO | Type descriptor: `quiz`, `diagnostic`, `practice`, `review`. Default: `quiz`. |
| `status` | `TEXT` | `str` | NO | State lifecycle: `in_progress`, `completed`, `abandoned`. |
| `questions_presented` | `INTEGER` | `int` | NO | Number of questions presented in this session. Default: `0`. |
| `questions_answered` | `INTEGER` | `int` | NO | Number of submitted responses recorded. Default: `0`. |
| `metadata_json` | `TEXT` | `str` | YES | JSON object storing target topics, quiz seed, syllabus context, or client metadata. |

### Indexes
- `idx_sessions_learner`: `ON learning_sessions(learner_id)`
- `idx_sessions_started`: `ON learning_sessions(started_at)`

---

## 3. Table: `learning_events`

Represents an individual question-level interaction or exercise attempt.

| Column Name | SQLite Type | Python Type | Nullable | Description / Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `event_id` | `TEXT` | `str` | NO | Primary Key. Formatted as `evt_<uuid14>`. Unique event identifier. |
| `session_id` | `TEXT` | `str` | NO | Foreign Key -> `learning_sessions(session_id)`. Active learning session. |
| `learner_id` | `TEXT` | `str` | NO | Indexed. Pseudonymous learner identifier matching session learner. |
| `item_id` | `TEXT` | `str` | NO | Indexed. Stable question identifier (e.g., `q_py_01`, `q_linreg_02`, `gen_svm_prereq`). |
| `knowledge_components` | `TEXT` | `str` | NO | JSON array of canonical KC strings (e.g., `["python"]`, `["linear regression"]`). |
| `submitted_answer` | `TEXT` | `str` | NO | Exact verbatim answer text chosen by learner. |
| `is_correct` | `INTEGER` | `int` | NO | Binary flag: `1` for correct, `0` for incorrect. Evaluated server-side against canonical item bank. |
| `response_time_ms` | `INTEGER` | `int` | YES | Response duration in milliseconds. Valid bounds: `[50, 3600000]`. Filtered to `NULL` if outside range. |
| `attempt_number` | `INTEGER` | `int` | NO | Sequential attempt counter on this item within this session (starts at 1). |
| `difficulty` | `INTEGER` | `int` | NO | Initial ordinal heuristic difficulty level: `1` (introductory) to `5` (advanced). |
| `event_timestamp` | `TEXT` | `str` | NO | ISO 8601 UTC timestamp when the answer was recorded. |
| `source` | `TEXT` | `str` | NO | Origin of event: `classic_quiz`, `api`, `practice_session`, `synthetic_seed`. |
| `metadata_json` | `TEXT` | `str` | YES | JSON object storing raw rejected response times, client timing metrics, and variant IDs. |

### Indexes
- `idx_events_learner`: `ON learning_events(learner_id)`
- `idx_events_session`: `ON learning_events(session_id)`
- `idx_events_item`: `ON learning_events(item_id)`
- `idx_events_timestamp`: `ON learning_events(event_timestamp)`

---

## 4. Idempotency & Duplicate Protection
The storage layer enforces idempotency on `(session_id, item_id, attempt_number)` tuples. If a client submits duplicate events due to network retries, double-clicking, or re-render loops, the store detects the existing record, preserves original timestamps, and returns the existing event payload with `"duplicate": true` without inserting duplicate rows.

---

## 5. Response Time Sanitization Rules
1. **Plausible Bounds:** \(50\,\text{ms} \le \text{duration} \le 3\,600\,000\,\text{ms}\) (1 hour).
2. **Implausibly Fast:** Times \(< 50\,\text{ms}\) (indicating automated script or browser artifact) are stored as `response_time_ms = NULL`, with the raw number preserved in `metadata_json.raw_rejected_response_time_ms`.
3. **Implausibly Slow:** Times \(> 3\,600\,000\,\text{ms}\) (indicating idle browser tab overnight) are set to `response_time_ms = NULL`.
4. **Missing / Unrecorded:** Stored as `NULL` without error.

---

## 6. Question Metadata Standards

All questions defined across `QUIZ_QUESTIONS`, `ADDITIONAL_QUIZ_QUESTIONS`, and `MORE_QUIZ` conform to the following schema:

```json
{
  "item_id": "q_py_01",
  "question": "Which library is mainly used for numerical arrays in Python?",
  "options": ["NumPy", "Flask", "OpenCV", "NLTK"],
  "correct_answer": "NumPy",
  "knowledge_components": ["python"],
  "difficulty": 1,
  "prerequisite_components": [],
  "source": "autolearn_static_curated"
}
```

- `item_id`: Stable identifier guaranteed not to change across restarts.
- `difficulty`: Ordinal heuristic rating (1 = Beginner, 2 = Elementary, 3 = Intermediate, 4 = Advanced, 5 = Mastery).
- `knowledge_components`: Aligned with syllabus `TOPIC_CATALOG` keys.
