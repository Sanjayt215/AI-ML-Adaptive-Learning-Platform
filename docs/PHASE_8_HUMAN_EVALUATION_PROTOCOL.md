# Phase 8: Human Subjects Research Ethics, IRB Compliance & Safety Protocol

**Project:** Knowledge-Tracing-Guided Reinforcement Learning for Personalized Exercise Selection  
**Platform:** AutoLearn AI Adaptive Learning Platform  
**Research Team:** T. Sanjay (E0124009), M. Nithish Kumar (E0124027)

---

## 1. Institutional Review Board (IRB) Compliance Statement

This protocol adheres to the ethical standards for educational research involving human participants in accordance with the **Declaration of Helsinki**, the **Belmont Report**, and institutional Human Subjects Protection policies.

The core guiding principles:
1. **Respect for Persons:** Voluntary participation, full informed consent, and unrestricted right to withdraw at any stage without educational penalty.
2. **Beneficence:** Maximizing educational learning gains while minimizing cognitive frustration and emotional fatigue.
3. **Justice:** Equitable distribution of instructional benefits. If an adaptive RL policy is discovered to be superior to the control policy, control group students will be granted access to the optimal adaptive policy following study conclusion.

---

## 2. Informed Consent Workflow

Prior to accessing the initial Pre-Assessment, every participant must view and accept the digital Informed Consent document:
- **Title of Study:** Investigating Adaptive Artificial Intelligence & Knowledge Tracing for Personalized Practice.
- **Purpose:** To evaluate computational methods for sequencing practice exercises to help students learn programming more efficiently.
- **Activities:**
  - Complete a 10-question baseline pre-assessment (~10 min).
  - Practice 15–25 exercises on the AutoLearn platform (~20–30 min).
  - Complete a 10-question immediate post-assessment (~10 min).
  - Optional 10-question retention check 7 days later (~10 min).
- **Risks & Discomforts:** Minimal risk, equivalent to ordinary classroom homework.
- **Voluntary Participation:** Students are informed that participation has zero impact on course grades, academic standing, or faculty evaluations.
- **Data Confidentiality:** All interaction logs are pseudonymized using cryptographic hashing before analysis.

---

## 3. Educational Parity & Risk Minimization

### 3.1 Cognitive Frustration Safeguards:
- The system embeds the **Hysteretic Difficulty Recovery Controller** (`services/recovery_controller.py`). If a learner experiences consecutive errors, the system drops exercise difficulty and serves prerequisite scaffolding to prevent discouragement.
- An explicit **"Request Hint"** and **"Skip Question"** button is provided at all times.

### 3.2 Educational Parity Guarantee:
- Students in the control arm (Prerequisite Difficulty Ladder) receive standard, curriculum-aligned exercises.
- At the conclusion of the formal study period, all participating students are given full, unrestricted access to the best-performing adaptive model.

---

## 4. Debriefing & Feedback Mechanism

At the completion of the post-assessment:
1. Students are provided with their personal **Mastery Growth Summary**, detailing the specific Knowledge Components they mastered.
2. A short, optional 5-point Likert survey evaluates subjective perceptions of challenge, engagement, and perceived usefulness.
3. Students receive an option to download a copy of their anonymized practice summary.
