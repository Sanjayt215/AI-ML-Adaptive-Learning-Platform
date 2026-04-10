from __future__ import annotations

from pathlib import Path
from typing import Tuple, Dict
import numpy as np
import pandas as pd

BASE_DIR = Path(__file__).resolve().parents[1]
RAW_DIR = BASE_DIR / "data" / "raw"

TOPIC_MAP = {
    "python": "python",
    "data preprocessing": "data preprocessing",
    "linear regression": "linear regression",
    "classification": "classification",
    "decision trees": "decision trees",
    "clustering": "clustering",
    "dimensionality reduction": "dimensionality reduction",
    "naive bayes": "naive bayes",
    "neural networks": "neural networks",
    "automl": "automl",
    "statistics": "statistics",
    "probability": "probability",
    "feature engineering": "feature engineering",
    "model evaluation": "model evaluation",
    "nlp": "nlp",
    "transformers": "transformers",
}


def _safe_read(path: Path, sep: str | None = None) -> pd.DataFrame:
    if path.exists():
        try:
            return pd.read_csv(path, sep=sep) if sep else pd.read_csv(path)
        except Exception:
            try:
                return pd.read_csv(path, sep=';')
            except Exception:
                return pd.DataFrame()
    return pd.DataFrame()


def _normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out.columns = [str(c).strip().replace(" ", "_") for c in out.columns]
    return out


def build_sample_learning_dataset(n: int = 420) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    topics = list(TOPIC_MAP.keys())
    selected = rng.choice(topics, size=n)
    prior_level = rng.choice(["beginner", "intermediate", "advanced"], p=[0.45, 0.35, 0.20], size=n)
    study_hours = rng.normal(6, 2.5, size=n).clip(1, 15)
    practice_tasks = rng.integers(0, 12, size=n)
    attendance = rng.normal(78, 12, size=n).clip(40, 100)
    video_completion = rng.normal(60, 20, size=n).clip(5, 100)
    quiz_score = (
        22 + (prior_level == "intermediate") * 18 + (prior_level == "advanced") * 36 + study_hours * 2.3
        + practice_tasks * 2.1 + attendance * 0.18 + video_completion * 0.15 + rng.normal(0, 8, size=n)
    ).clip(5, 100)
    target_level = pd.cut(quiz_score, bins=[0,45,75,100], labels=["beginner","intermediate","advanced"], include_lowest=True)
    exam_score = (quiz_score * 0.9 + rng.normal(4, 6, size=n)).clip(0, 100)
    return pd.DataFrame({
        "topic": selected,
        "prior_level": prior_level,
        "study_hours": study_hours.round(2),
        "practice_tasks": practice_tasks,
        "attendance": attendance.round(1),
        "video_completion": video_completion.round(1),
        "quiz_score": quiz_score.round(1),
        "exam_score": exam_score.round(1),
        "target_level": target_level.astype(str),
    })


def _map_oulad_dataset() -> pd.DataFrame:
    oulad_dir = RAW_DIR / 'oulad'
    student_info = _safe_read(oulad_dir / 'studentInfo.csv')
    student_assessment = _safe_read(oulad_dir / 'studentAssessment.csv')
    assessments = _safe_read(oulad_dir / 'assessments.csv')
    student_vle = _safe_read(oulad_dir / 'studentVle.csv')
    if student_info.empty:
        return pd.DataFrame()
    student_info = _normalize_columns(student_info)
    if not student_assessment.empty:
        student_assessment = _normalize_columns(student_assessment)
    if not assessments.empty:
        assessments = _normalize_columns(assessments)
    if not student_vle.empty:
        student_vle = _normalize_columns(student_vle)

    key_cols = [c for c in ['code_module','code_presentation','id_student'] if c in student_info.columns]
    if not key_cols:
        return pd.DataFrame()

    if not student_assessment.empty and 'score' in student_assessment.columns:
        merged = student_assessment
        if not assessments.empty and 'id_assessment' in merged.columns and 'id_assessment' in assessments.columns:
            merged = merged.merge(assessments[['id_assessment'] + [c for c in ['code_module','code_presentation','assessment_type','weight'] if c in assessments.columns]], on='id_assessment', how='left')
        assess_agg = merged.groupby([c for c in ['code_module','code_presentation','id_student'] if c in merged.columns], as_index=False).agg(
            quiz_score=('score','mean'),
            practice_tasks=('score','count'),
        )
    else:
        assess_agg = pd.DataFrame(columns=key_cols + ['quiz_score','practice_tasks'])

    if not student_vle.empty and 'sum_click' in student_vle.columns:
        vle_agg = student_vle.groupby([c for c in ['code_module','code_presentation','id_student'] if c in student_vle.columns], as_index=False).agg(
            video_completion=('sum_click','mean')
        )
        vle_agg['video_completion'] = (vle_agg['video_completion'] / max(vle_agg['video_completion'].max(), 1) * 100).clip(0,100)
    else:
        vle_agg = pd.DataFrame(columns=key_cols + ['video_completion'])

    df = student_info.merge(assess_agg, on=key_cols, how='left').merge(vle_agg, on=key_cols, how='left')
    df['quiz_score'] = pd.to_numeric(df.get('quiz_score', 55), errors='coerce').fillna(55).clip(0,100)
    df['practice_tasks'] = pd.to_numeric(df.get('practice_tasks', 2), errors='coerce').fillna(2)
    df['video_completion'] = pd.to_numeric(df.get('video_completion', 45), errors='coerce').fillna(45).clip(0,100)
    df['attendance'] = (df['video_completion'] * 0.6 + df['quiz_score'] * 0.4).clip(0,100)
    df['study_hours'] = (df['practice_tasks'] * 0.6 + 3).clip(1,15)
    if 'studied_credits' in df.columns:
        df['study_hours'] = (pd.to_numeric(df['studied_credits'], errors='coerce').fillna(60) / 10).clip(1,15)
    final_col = 'final_result' if 'final_result' in df.columns else None
    if final_col:
        mapped_level = df[final_col].astype(str).str.lower().map({
            'distinction': 'advanced',
            'pass': 'intermediate',
            'fail': 'beginner',
            'withdrawn': 'beginner',
        }).fillna('intermediate')
        exam_score = mapped_level.map({'beginner': 42, 'intermediate': 68, 'advanced': 88}).astype(float)
    else:
        exam_score = (df['quiz_score'] * 0.85 + df['video_completion'] * 0.15).clip(0,100)
        mapped_level = pd.cut(exam_score, bins=[0,45,75,100], labels=['beginner','intermediate','advanced'], include_lowest=True).astype(str)

    topic_cycle = list(TOPIC_MAP.keys())
    rows = len(df)
    out = pd.DataFrame({
        'topic': [topic_cycle[i % len(topic_cycle)] for i in range(rows)],
        'prior_level': mapped_level,
        'study_hours': df['study_hours'].round(2),
        'practice_tasks': df['practice_tasks'].round(0),
        'attendance': df['attendance'].round(1),
        'video_completion': df['video_completion'].round(1),
        'quiz_score': df['quiz_score'].round(1),
        'exam_score': pd.to_numeric(exam_score, errors='coerce').fillna(60).clip(0,100).round(1),
    })
    out['target_level'] = pd.cut(out['exam_score'], bins=[0,45,75,100], labels=['beginner','intermediate','advanced'], include_lowest=True).astype(str)
    return out


def _map_uci_student_performance() -> pd.DataFrame:
    uci_dir = RAW_DIR / 'uci_student_performance'
    frames = []
    for name in ['student-mat.csv', 'student-por.csv']:
        df = _safe_read(uci_dir / name, sep=';')
        if df.empty:
            continue
        df = _normalize_columns(df)
        score_cols = [c for c in ['G1','G2','G3'] if c in df.columns]
        if not score_cols:
            continue
        score = df[score_cols].mean(axis=1) * 5
        rows = len(df)
        topic_cycle = list(TOPIC_MAP.keys())
        out = pd.DataFrame({
            'topic': [topic_cycle[i % len(topic_cycle)] for i in range(rows)],
            'prior_level': pd.cut(score, bins=[0,45,75,100], labels=['beginner','intermediate','advanced'], include_lowest=True).astype(str),
            'study_hours': pd.to_numeric(df.get('studytime', 2), errors='coerce').fillna(2) * 2,
            'practice_tasks': pd.to_numeric(df.get('failures', 0), errors='coerce').fillna(0).rsub(4).clip(lower=0),
            'attendance': (100 - pd.to_numeric(df.get('absences', 5), errors='coerce').fillna(5) * 2).clip(30,100),
            'video_completion': (pd.to_numeric(df.get('studytime', 2), errors='coerce').fillna(2) * 22).clip(10,100),
            'quiz_score': score.clip(0,100),
            'exam_score': score.clip(0,100),
        })
        out['target_level'] = pd.cut(out['exam_score'], bins=[0,45,75,100], labels=['beginner','intermediate','advanced'], include_lowest=True).astype(str)
        frames.append(out)
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def load_learning_dataset() -> Tuple[pd.DataFrame, Dict]:
    main_path = RAW_DIR / "student_main" / "StudentPerformanceFactors.csv"
    backup_path = RAW_DIR / "student_backup" / "StudentsPerformance.csv"
    main_df = _safe_read(main_path)
    backup_df = _safe_read(backup_path)
    info = {
        "real_data_used": False,
        "rows": 0,
        "sources": [],
        "main_path": str(main_path),
        "backup_path": str(backup_path),
        "oulad_path": str(RAW_DIR / 'oulad'),
        "uci_path": str(RAW_DIR / 'uci_student_performance'),
    }
    frames = []

    oulad_df = _map_oulad_dataset()
    if not oulad_df.empty:
        frames.append(oulad_df)
        info['sources'].append('OULAD')

    uci_df = _map_uci_student_performance()
    if not uci_df.empty:
        frames.append(uci_df)
        info['sources'].append('UCI Student Performance')

    if not main_df.empty:
        df = _normalize_columns(main_df)
        exam_col = "Exam_Score" if "Exam_Score" in df.columns else ("ExamScore" if "ExamScore" in df.columns else None)
        if exam_col:
            topic_cycle = list(TOPIC_MAP.keys())
            rows = len(df)
            mapped = pd.DataFrame({
                "topic": [topic_cycle[i % len(topic_cycle)] for i in range(rows)],
                "prior_level": pd.cut(df.get("Previous_Scores", df[exam_col]), bins=[-1,50,75,100], labels=["beginner","intermediate","advanced"], include_lowest=True).astype(str),
                "study_hours": pd.to_numeric(df.get("Hours_Studied", 5), errors="coerce").fillna(5),
                "practice_tasks": pd.to_numeric(df.get("Tutoring_Sessions", 2), errors="coerce").fillna(2),
                "attendance": pd.to_numeric(df.get("Attendance", 75), errors="coerce").fillna(75),
                "video_completion": (pd.to_numeric(df.get("Access_to_Resources", 1), errors="coerce").fillna(1) * 25).clip(0,100),
                "quiz_score": pd.to_numeric(df.get("Previous_Scores", df[exam_col]), errors="coerce").fillna(60).clip(0,100),
                "exam_score": pd.to_numeric(df[exam_col], errors="coerce").fillna(60).clip(0,100),
            })
            mapped["target_level"] = pd.cut(mapped["exam_score"], bins=[0,45,75,100], labels=["beginner","intermediate","advanced"], include_lowest=True).astype(str)
            frames.append(mapped)
            info["sources"].append("StudentPerformanceFactors.csv")

    if not backup_df.empty:
        df = _normalize_columns(backup_df)
        math_col = "math_score" if "math_score" in df.columns else None
        reading_col = "reading_score" if "reading_score" in df.columns else None
        writing_col = "writing_score" if "writing_score" in df.columns else None
        if math_col:
            rows = len(df)
            exam_avg = pd.DataFrame(df[[c for c in [math_col, reading_col, writing_col] if c]]).mean(axis=1)
            topic_cycle = list(TOPIC_MAP.keys())
            mapped = pd.DataFrame({
                "topic": [topic_cycle[i % len(topic_cycle)] for i in range(rows)],
                "prior_level": pd.cut(exam_avg, bins=[-1,50,75,100], labels=["beginner","intermediate","advanced"], include_lowest=True).astype(str),
                "study_hours": pd.to_numeric(df.get("test_preparation_course", pd.Series([0]*rows)).astype(str).str.contains("completed").astype(int) * 4 + 3, errors="coerce").fillna(4),
                "practice_tasks": pd.to_numeric(df.get("lunch", pd.Series([1]*rows)).astype(str).str.contains("standard").astype(int) * 3 + 1, errors="coerce").fillna(2),
                "attendance": (exam_avg * 0.9).clip(30,100),
                "video_completion": (exam_avg * 0.8).clip(20,100),
                "quiz_score": exam_avg.clip(0,100),
                "exam_score": exam_avg.clip(0,100),
            })
            mapped["target_level"] = pd.cut(mapped["exam_score"], bins=[0,45,75,100], labels=["beginner","intermediate","advanced"], include_lowest=True).astype(str)
            frames.append(mapped)
            info["sources"].append("StudentsPerformance.csv")

    if frames:
        df = pd.concat(frames, ignore_index=True)
        info["real_data_used"] = True
        info["rows"] = int(len(df))
        return df, info

    df = build_sample_learning_dataset()
    info["rows"] = int(len(df))
    info["sources"].append("generated_sample_dataset")
    return df, info


def load_optional_heart_dataset() -> pd.DataFrame:
    path = RAW_DIR / "heart" / "heart.csv"
    return _safe_read(path)
