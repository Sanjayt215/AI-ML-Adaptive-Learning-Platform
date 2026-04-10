
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesClassifier, ExtraTreesRegressor, GradientBoostingClassifier, RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LinearRegression, LogisticRegression, Ridge, Lasso
from sklearn.metrics import accuracy_score, mean_absolute_error
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC

FEATURES = ["topic", "prior_level", "study_hours", "practice_tasks", "attendance", "video_completion", "quiz_score"]
CLASS_TARGET = "target_level"
REG_TARGET = "exam_score"


@dataclass
class LearningModelBundle:
    classifier: Any
    regressor: Any
    leaderboard: Dict[str, float]
    regression_scores: Dict[str, float]
    best_model_name: str
    engine: str


def _preprocessor(df: pd.DataFrame):
    # Use explicit feature groups so modern pandas string dtypes do not get misclassified as numeric.
    categorical = ['topic', 'prior_level']
    numeric = [c for c in FEATURES if c not in categorical]
    return ColumnTransformer([
        ('cat', OneHotEncoder(handle_unknown='ignore'), categorical),
        ('num', StandardScaler(), numeric),
    ])


def _baseline_models(df: pd.DataFrame) -> LearningModelBundle:
    pre = _preprocessor(df)
    x_train, x_test, y_train, y_test = train_test_split(df[FEATURES], df[CLASS_TARGET], test_size=0.2, random_state=42, stratify=df[CLASS_TARGET])
    class_models = {
        'Logistic Regression': LogisticRegression(max_iter=1500),
        'SVM': SVC(kernel='rbf', probability=True),
        'KNN': KNeighborsClassifier(n_neighbors=7),
        'Random Forest': RandomForestClassifier(n_estimators=220, random_state=42),
        'Extra Trees': ExtraTreesClassifier(n_estimators=260, random_state=42),
        'Gradient Boosting': GradientBoostingClassifier(random_state=42),
    }
    scores = {}
    fitted = {}
    for name, model in class_models.items():
        pipe = Pipeline([('pre', pre), ('model', model)])
        pipe.fit(x_train, y_train)
        pred = pipe.predict(x_test)
        scores[name] = round(accuracy_score(y_test, pred), 4)
        fitted[name] = pipe
    best_name = max(scores, key=scores.get)

    x_train_r, x_test_r, y_train_r, y_test_r = train_test_split(df[FEATURES], df[REG_TARGET], test_size=0.2, random_state=42)
    reg_models = {
        'Linear Regression': LinearRegression(),
        'Ridge': Ridge(alpha=1.0),
        'Lasso': Lasso(alpha=0.01),
        'Random Forest Regressor': RandomForestRegressor(n_estimators=220, random_state=42),
        'Extra Trees Regressor': ExtraTreesRegressor(n_estimators=260, random_state=42),
    }
    reg_scores = {}
    fitted_regs = {}
    for name, model in reg_models.items():
        pipe = Pipeline([('pre', pre), ('model', model)])
        pipe.fit(x_train_r, y_train_r)
        pred = pipe.predict(x_test_r)
        reg_scores[name] = round(mean_absolute_error(y_test_r, pred), 4)
        fitted_regs[name] = pipe
    best_reg = min(reg_scores, key=reg_scores.get)
    return LearningModelBundle(
        classifier=fitted[best_name],
        regressor=fitted_regs[best_reg],
        leaderboard=scores,
        regression_scores=reg_scores,
        best_model_name=best_name,
        engine='baseline_automl',
    )


def build_learning_models(df: pd.DataFrame) -> LearningModelBundle:
    try:
        from autogluon.tabular import TabularPredictor  # type: ignore
    except Exception:
        return _baseline_models(df)

    try:
        train_df, test_df = train_test_split(df[FEATURES + [CLASS_TARGET]], test_size=0.2, random_state=42, stratify=df[CLASS_TARGET])
        predictor = TabularPredictor(label=CLASS_TARGET, eval_metric='accuracy', verbosity=0, path='artifacts/autogluon_classifier').fit(
            train_df,
            presets='medium_quality',
            time_limit=60,
        )
        leaderboard_df = predictor.leaderboard(test_df, silent=True)
        lb = {str(row['model']): round(float(row['score_test']), 4) for _, row in leaderboard_df[['model','score_test']].head(8).iterrows()}
        reg_train, reg_test = train_test_split(df[FEATURES + [REG_TARGET]], test_size=0.2, random_state=42)
        reg_predictor = TabularPredictor(label=REG_TARGET, eval_metric='mean_absolute_error', verbosity=0, path='artifacts/autogluon_regressor').fit(
            reg_train,
            presets='medium_quality',
            time_limit=60,
        )
        reg_lb_df = reg_predictor.leaderboard(reg_test, silent=True)
        reg_lb = {str(row['model']): round(float(row['score_test']), 4) for _, row in reg_lb_df[['model','score_test']].head(8).iterrows()}
        best_name = predictor.model_best or next(iter(lb), 'AutoGluonModel')
        return LearningModelBundle(predictor, reg_predictor, lb, reg_lb, best_name, 'autogluon')
    except Exception:
        return _baseline_models(df)


def predict_level_with_models(bundle: LearningModelBundle, topic: str, score_pct: float) -> str:
    row = pd.DataFrame([{
        'topic': topic,
        'prior_level': 'beginner' if score_pct < 45 else ('intermediate' if score_pct < 75 else 'advanced'),
        'study_hours': 4.0 if score_pct < 45 else (6.0 if score_pct < 75 else 8.0),
        'practice_tasks': 2 if score_pct < 45 else (4 if score_pct < 75 else 6),
        'attendance': 72.0 if score_pct < 45 else (82.0 if score_pct < 75 else 90.0),
        'video_completion': 45.0 if score_pct < 45 else (68.0 if score_pct < 75 else 85.0),
        'quiz_score': score_pct,
    }])
    if bundle.engine == 'autogluon':
        pred = bundle.classifier.predict(row)
        return str(pred.iloc[0])
    return str(bundle.classifier.predict(row)[0])


def predict_score_with_models(bundle: LearningModelBundle, topic: str, score_pct: float) -> float:
    row = pd.DataFrame([{
        'topic': topic,
        'prior_level': 'beginner' if score_pct < 45 else ('intermediate' if score_pct < 75 else 'advanced'),
        'study_hours': 4.0 if score_pct < 45 else (6.0 if score_pct < 75 else 8.0),
        'practice_tasks': 2 if score_pct < 45 else (4 if score_pct < 75 else 6),
        'attendance': 72.0 if score_pct < 45 else (82.0 if score_pct < 75 else 90.0),
        'video_completion': 45.0 if score_pct < 45 else (68.0 if score_pct < 75 else 85.0),
        'quiz_score': score_pct,
    }])
    if bundle.engine == 'autogluon':
        pred = bundle.regressor.predict(row)
        return round(float(pred.iloc[0]), 1)
    return round(float(bundle.regressor.predict(row)[0]), 1)
