# Phase 8: Learner Data Privacy, Minimization & Research Governance

**Project:** Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection  
**Platform:** AutoLearn AI Adaptive Learning Platform  
**Authors:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)

---

## 1. Ethical & Regulatory Principles

Educational data collection requires adherence to institutional standards (FERPA, GDPR Recitals, Institutional Review Board guidelines).

To enable ethical validation of reinforcement learning and knowledge tracing policies, AutoLearn implements a **Privacy by Design** framework:
1. **Principle of Minimization:** Only cognitive and instructional interaction data required to evaluate mastery trajectories are preserved in research exports.
2. **Cryptographic Pseudonymization:** Learner identifiers are mapped to irreversible pseudonyms (`subj_<hex16>`) using HMAC-SHA256 with a salt known only to the authorized investigator.
3. **Temporal De-identification:** Absolute wall-clock timestamps (which could permit correlation with campus networks or login records) are converted to relative seconds from session origin.
4. **Zero Live Human Interventions without Consent:** RL models run only in synthetic simulation or offline shadow evaluation unless formal human subjects approval has been obtained.

---

## 2. Pseudonymization Architecture

```
+------------------+         +-------------------------------+
|  Raw Learner ID  | ------> | HMAC-SHA256(Salt, Learner_ID) |
| (e.g. "student1")|         +-------------------------------+
+------------------+                        |
                                            v
                                 +-----------------------+
                                 | Research Pseudonym    |
                                 | "subj_4f2a9c8b71d0e341"|
                                 +-----------------------+
```

### Properties:
- **Deterministic:** The same raw ID within an experiment cohort hashes to the same pseudonym, preserving longitudinal tracking across pre-, post-, and delayed retention assessments.
- **Irreversible:** Without knowledge of `AUTOLEARN_RESEARCH_SALT`, mapping the pseudonym back to an individual student identity is computationally infeasible.
- **Separation of Keys:** The salt is stored in environment variables, completely segregated from research publication datasets.

---

## 3. Data Schema: Research Export Specification

When exporting data via `services.privacy_service.export_anonymized_research_dataset()`, the resulting structure includes:

```json
{
  "dataset_name": "AutoLearn KT-RL Anonymized Research Dataset",
  "version": "1.0",
  "compliance": {
    "ferpa_compliant": true,
    "data_minimization_applied": true,
    "pseudonymization_method": "HMAC-SHA256",
    "pii_fields_retained": false,
    "temporal_deidentification": "Relative session seconds"
  },
  "participants": [
    {
      "participant_id": "subj_a7c8194b32de",
      "has_pre_post_comparison": true,
      "metrics": {
        "gross_learning_gain": 0.40,
        "normalized_learning_gain": 0.571429,
        "net_mastery_delta": 3,
        "retention_rate": 0.95
      },
      "event_sequence": [
        {
          "step_index": 1,
          "relative_time_seconds": 0.0,
          "item_id": "py_var_01",
          "knowledge_components": ["py_var_types"],
          "is_correct": 1,
          "response_time_ms": 3200,
          "difficulty": 1,
          "recommendation_source": "composite_adaptive"
        }
      ]
    }
  ]
}
```

---

## 4. PII Exclusion Audit Matrix

| Field Name | Category | Status in Research Export | Handling Method |
| :--- | :--- | :--- | :--- |
| `name`, `full_name` | Direct PII | **Strictly Excluded** | Stripped at ingestion |
| `email` | Direct PII | **Strictly Excluded** | Stripped at ingestion |
| `ip_address` | Indirect PII | **Strictly Excluded** | Not captured |
| `student_id` | Institutional ID | **Strictly Excluded** | Replaced with HMAC pseudonym |
| `event_timestamp` | Quasi-Identifier | **De-identified** | Normalized to relative session seconds |
| `submitted_answer` | Cognitive Data | **Retained (Sanitized)** | Kept for error analysis |
| `is_correct` | Cognitive Data | **Retained** | Required for BKT/RL evaluation |
| `bkt_mastery` | Model Estimate | **Retained** | Required for research reporting |
