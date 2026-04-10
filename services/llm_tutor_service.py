from __future__ import annotations

import os
import textwrap
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, List

import pandas as pd
import requests
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from resources import TOPIC_CATALOG, normalize_topic
from services.catalog_service import rank_courses, rank_kaggle_datasets, rank_catalog_videos, project_for_topic

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

TOPIC_NOTES: Dict[str, str] = {
    'python': 'Python is the foundation language for AI and ML workflows. Focus on data types, functions, loops, list comprehensions, NumPy, pandas, and basic visualization.',
    'statistics': 'Statistics helps you summarize data, estimate uncertainty, and validate model decisions. Learn mean, variance, distributions, hypothesis testing, and confidence intervals.',
    'probability': 'Probability gives the mathematical language for uncertainty. Learn conditional probability, Bayes theorem, random variables, expectation, and common distributions.',
    'feature engineering': 'Feature engineering improves how raw data is represented. It includes encoding, scaling, feature creation, feature selection, and handling missing values.',
    'linear regression': 'Linear regression predicts continuous values and teaches the basics of supervised learning, fitting, coefficients, loss, and regularization.',
    'classification': 'Classification predicts categories such as pass/fail or spam/not-spam. Learn logistic regression, metrics, imbalance handling, and threshold tuning.',
    'decision trees': 'Decision trees split data into interpretable rules. Understand entropy, information gain, pruning, and ensemble extensions like random forests.',
    'clustering': 'Clustering groups unlabeled examples using similarity. Study K-means, hierarchical clustering, silhouette score, and feature scaling effects.',
    'dimensionality reduction': 'Dimensionality reduction compresses information into fewer features. Learn PCA, explained variance, visualization, and denoising tradeoffs.',
    'naive bayes': 'Naive Bayes is a probabilistic classifier that works well on sparse text features and small datasets, especially when assumptions are acceptable.',
    'neural networks': 'Neural networks learn layered representations. Understand perceptrons, activation functions, backpropagation, optimization, overfitting, and regularization.',
    'computer vision': 'Computer vision teaches machines to interpret images using preprocessing, convolutional neural networks, detection, segmentation, and augmentation.',
    'nlp': 'Natural language processing handles text tasks like tokenization, embeddings, sentiment analysis, translation, and retrieval.',
    'transformers': 'Transformers use attention to model long-range dependencies. They power modern NLP, vision transformers, and most LLM systems.',
    'llm': 'Large language models are pretrained on broad text corpora and then adapted through prompting, retrieval, instruction tuning, and tool use.',
    'prompt engineering': 'Prompt engineering structures instructions, context, role, constraints, and examples so language models answer more reliably.',
    'generative ai': 'Generative AI creates new text, images, audio, or code by learning data patterns. It includes diffusion, autoregressive models, and multimodal systems.',
    'reinforcement learning': 'Reinforcement learning optimizes behavior through rewards. Learn agents, environments, policies, exploration, and value functions.',
    'model evaluation': 'Model evaluation tells whether a model is trustworthy. Use train/validation/test splits, cross-validation, precision, recall, F1, ROC-AUC, and error analysis.',
    'model deployment': 'Model deployment makes models usable in real systems via APIs, monitoring, versioning, and retraining pipelines.',
    'automl': 'AutoML automates feature preprocessing, model search, and hyperparameter tuning so strong baselines are easier to build quickly.',
    'svm': 'Support Vector Machines maximize margin between classes and are strong for small to medium structured datasets.',
    'ensemble methods': 'Ensemble methods combine multiple models to improve robustness and predictive power through bagging, boosting, or stacking.',
    'hyperparameter tuning': 'Hyperparameter tuning searches for good model settings using grid search, random search, Bayesian optimization, or bandit-based methods.',
    'search algorithms': 'Search algorithms explore state spaces to find solutions. Learn BFS, DFS, uniform cost search, A*, heuristics, and admissibility.',
    'knowledge representation': 'Knowledge representation models facts, rules, entities, and relationships so AI systems can reason about them.',
    'expert systems': 'Expert systems combine a knowledge base and inference engine to emulate domain-specific decision making.',
    'fuzzy logic': 'Fuzzy logic handles partial truth with membership functions and linguistic rules, useful when boundaries are not crisp.',
    'rag': 'Retrieval-augmented generation combines search with a language model so answers are grounded in documents instead of memory alone.',
}

COMPARISON_HINTS = {
    ('classification', 'clustering'): 'Classification uses labeled data to predict known classes, while clustering uses unlabeled data to discover groups.',
    ('linear regression', 'classification'): 'Linear regression predicts continuous values; classification predicts discrete labels.',
    ('decision trees', 'random forest'): 'A decision tree is a single interpretable model, while a random forest averages many trees for higher robustness.',
    ('transformers', 'llm'): 'Transformers are the architecture family; an LLM is a large trained model often built on transformers.',
    ('rag', 'llm'): 'An LLM answers from learned parameters; RAG adds retrieved external context to improve freshness and grounding.',
}


@dataclass
class TutorReply:
    answer: str
    mode: str
    detected_topic: str
    retrieved_chunks: List[Dict]
    related_resources: Dict


@lru_cache(maxsize=1)
def load_dataset_registry() -> pd.DataFrame:
    path = os.path.join(DATA_DIR, 'real_dataset_registry.csv')
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame(columns=['dataset', 'task', 'topic', 'source', 'url', 'why_it_fits'])


@lru_cache(maxsize=1)
def _topic_documents():
    docs = []
    for topic, meta in TOPIC_CATALOG.items():
        docs.append({
            'topic': topic,
            'kind': 'topic_note',
            'text': ' '.join([
                topic,
                ' '.join(meta.get('aliases', [])),
                ' '.join(meta.get('prerequisites', [])),
                meta.get('project', ''),
                TOPIC_NOTES.get(topic, ''),
            ]).strip(),
        })
    df = load_dataset_registry()
    for _, row in df.iterrows():
        docs.append({
            'topic': normalize_topic(str(row.get('topic', ''))),
            'kind': 'dataset',
            'text': f"Dataset {row.get('dataset','')} task {row.get('task','')} topic {row.get('topic','')} source {row.get('source','')} why {row.get('why_it_fits','')}".strip(),
            'url': row.get('url', ''),
            'dataset': row.get('dataset', ''),
        })
    corpus = [d['text'] for d in docs] or ['machine learning']
    vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
    matrix = vectorizer.fit_transform(corpus)
    return docs, vectorizer, matrix


def retrieve_relevant_chunks(question: str, selected_topics: List[str], limit: int = 6) -> List[Dict]:
    docs, vectorizer, matrix = _topic_documents()
    query = ' '.join([question] + selected_topics)
    qv = vectorizer.transform([query])
    sims = cosine_similarity(qv, matrix).ravel()
    scored = sorted(enumerate(sims), key=lambda x: x[1], reverse=True)
    chunks = []
    for idx, score in scored:
        if score <= 0:
            continue
        item = dict(docs[idx])
        item['score'] = round(float(score), 4)
        chunks.append(item)
        if len(chunks) >= limit:
            break
    return chunks


def _detect_topic(question: str, selected_topics: List[str]) -> str:
    q = question.lower()
    for topic in selected_topics:
        keys = [topic] + TOPIC_CATALOG.get(topic, {}).get('aliases', [])
        if any(k.lower() in q for k in keys):
            return topic
    for topic, meta in TOPIC_CATALOG.items():
        keys = [topic] + meta.get('aliases', [])
        if any(k.lower() in q for k in keys):
            return topic
    return selected_topics[0] if selected_topics else 'python'


def _compare_answer(question: str, selected_topics: List[str]) -> str | None:
    q = question.lower().replace(' versus ', ' vs ')
    if ' vs ' not in q and 'difference' not in q and 'compare' not in q:
        return None
    mentioned = []
    for topic in list(TOPIC_CATALOG.keys()) + ['random forest']:
        if topic in q:
            mentioned.append(topic)
    if len(mentioned) < 2:
        return None
    a, b = mentioned[0], mentioned[1]
    pair = (a, b)
    rev = (b, a)
    if pair in COMPARISON_HINTS:
        base = COMPARISON_HINTS[pair]
    elif rev in COMPARISON_HINTS:
        base = COMPARISON_HINTS[rev]
    else:
        base = f"{a.title()} and {b.title()} solve different problems or use different assumptions. Compare them by task type, input labels, interpretability, data size, and evaluation metric."
    return base + f" For your project, use {a.title()} when it matches the task goal, and use {b.title()} when you need the strengths of that method."


def _build_learning_snapshot(profile: Dict, assessment: List[Dict]) -> str:
    topics = ', '.join(t.title() for t in profile.get('topics', [])) or 'No selected topics'
    weak = sorted(assessment, key=lambda x: x.get('score_pct', 0))[:2]
    strong = sorted(assessment, key=lambda x: x.get('score_pct', 0), reverse=True)[:2]
    weak_txt = ', '.join(f"{w['topic']} ({w['score_pct']}%)" for w in weak) if weak else 'not available yet'
    strong_txt = ', '.join(f"{s['topic']} ({s['score_pct']}%)" for s in strong) if strong else 'not available yet'
    return f"Selected topics: {topics}. Weak topics: {weak_txt}. Strong topics: {strong_txt}. Goal: {profile.get('target_goal','not set')}."


def _local_reasoned_answer(question: str, detected_topic: str, profile: Dict, assessment: List[Dict], chunks: List[Dict]) -> str:
    q = question.lower()
    meta = TOPIC_CATALOG.get(detected_topic, {})
    topic_note = TOPIC_NOTES.get(detected_topic, meta.get('project', ''))
    prerequisites = meta.get('prerequisites', [])
    current_result = next((r for r in assessment if r.get('topic') == detected_topic), None)
    current_level = (current_result or {}).get('predicted_level', 'beginner')
    current_score = (current_result or {}).get('score_pct', 0)
    courses = rank_courses(detected_topic, current_level, max_results=2)
    videos = rank_catalog_videos(detected_topic, current_level, max_results=2)
    datasets = rank_kaggle_datasets(detected_topic, current_level, max_results=2)
    proj = project_for_topic(detected_topic, current_level)

    compare = _compare_answer(question, profile.get('topics', []))
    if compare:
        return compare

    if any(k in q for k in ['doubt', 'clarify', 'explain', 'understand', 'what is', 'how does']):
        return textwrap.fill(
            f"{detected_topic.title()} explanation: {topic_note} Start from prerequisites like {', '.join(prerequisites) if prerequisites else 'Python and basic math'}, then study one concept at a time, solve 2 or 3 examples, and apply it in a mini project. For your current level ({current_level}) and score ({current_score}%), begin with '{videos[0]['title']}' and then try this project: {proj}",
            width=120,
        )
    if any(k in q for k in ['weak', 'improve', 'focus', 'increase score', 'low score']):
        weak = sorted(assessment, key=lambda x: x.get('score_pct', 0))[0] if assessment else {'topic': detected_topic, 'score_pct': current_score}
        return f"Your biggest improvement area is {weak['topic'].title()} at {weak.get('score_pct', 0)}%. To increase your learning score, revise fundamentals, complete the recommended path step, retry a fresh quiz, and finish a mini project. The fastest next action is to study one video, one course module, and one practice task for {weak['topic'].title()}."
    if any(k in q for k in ['next', 'roadmap', 'path', 'order']):
        ordered = profile.get('topics', [])
        return f"Suggested study order: {' → '.join(t.title() for t in ordered)}. Move to the next topic only after you can explain the current topic, score above 70%, and complete one applied task."
    if any(k in q for k in ['course', 'certificate', 'resource']):
        course = courses[0] if courses else {'title': 'recommended course', 'provider': 'trusted platform'}
        return f"For {detected_topic.title()}, the best next course is '{course['title']}' from {course['provider']}. After that, do the mini project: {proj}"
    if any(k in q for k in ['video', 'youtube']):
        video = videos[0] if videos else {'title': 'recommended tutorial'}
        return f"Start with this video for {detected_topic.title()}: '{video['title']}'. Then re-attempt the quiz to measure improvement."
    if any(k in q for k in ['dataset', 'data', 'kaggle']):
        ds = datasets[0] if datasets else None
        if ds:
            return f"A good dataset for {detected_topic.title()} is '{ds['title']}'. It fits because {ds.get('description', 'it matches the topic and difficulty level')}."
        return f"Use the dataset registry to choose a matching dataset for {detected_topic.title()} based on difficulty and task type."
    if any(k in q for k in ['project', 'build']):
        return f"Mini project for {detected_topic.title()}: {proj}"
    evidence = ' | '.join(c['text'][:110] for c in chunks[:3]) if chunks else topic_note
    return f"For {detected_topic.title()}, here is the best guidance based on your plan: {topic_note} Current evidence: {evidence}. Ask me to explain the topic, compare algorithms, suggest a dataset, or create a revision plan."


def _openai_available() -> bool:
    return bool(os.getenv('OPENAI_API_KEY'))


def _call_openai(question: str, detected_topic: str, profile: Dict, assessment: List[Dict], chunks: List[Dict]) -> str:
    api_key = os.getenv('OPENAI_API_KEY')
    model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    if not api_key:
        raise RuntimeError('OPENAI_API_KEY is not set')
    system = (
        'You are an AI/ML tutor inside a personalized learning platform. '
        'Answer clearly for a student, use simple English, stay grounded in the provided context, '
        'and give actionable next steps. Mention uncertainty when context is incomplete.'
    )
    context = '\n'.join(f"- {c.get('kind','note')}: {c.get('text','')[:400]}" for c in chunks[:6])
    user = (
        f"Student profile: {_build_learning_snapshot(profile, assessment)}\n"
        f"Detected topic: {detected_topic}\n"
        f"Retrieved context:\n{context}\n"
        f"Student question: {question}\n"
        'Give a direct answer, one example, and 2 next steps.'
    )
    resp = requests.post(
        'https://api.openai.com/v1/chat/completions',
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        json={
            'model': model,
            'messages': [
                {'role': 'system', 'content': system},
                {'role': 'user', 'content': user},
            ],
            'temperature': 0.4,
        },
        timeout=40,
    )
    resp.raise_for_status()
    data = resp.json()
    return data['choices'][0]['message']['content'].strip()


def generate_tutor_reply(question: str, profile: Dict, assessment: List[Dict]) -> TutorReply:
    selected_topics = profile.get('topics', []) or ['python']
    detected_topic = _detect_topic(question, selected_topics)
    chunks = retrieve_relevant_chunks(question, selected_topics)
    related_resources = {
        'videos': rank_catalog_videos(detected_topic, 'beginner', max_results=2),
        'courses': rank_courses(detected_topic, 'beginner', max_results=2),
        'datasets': rank_kaggle_datasets(detected_topic, 'beginner', max_results=2),
        'project': project_for_topic(detected_topic, 'beginner'),
    }
    if _openai_available():
        try:
            answer = _call_openai(question, detected_topic, profile, assessment, chunks)
            return TutorReply(answer=answer, mode='openai_llm', detected_topic=detected_topic, retrieved_chunks=chunks, related_resources=related_resources)
        except Exception:
            pass
    answer = _local_reasoned_answer(question, detected_topic, profile, assessment, chunks)
    return TutorReply(answer=answer, mode='local_rag_fallback', detected_topic=detected_topic, retrieved_chunks=chunks, related_resources=related_resources)
