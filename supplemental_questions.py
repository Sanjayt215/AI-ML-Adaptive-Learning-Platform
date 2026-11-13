"""
Supplemental Question Bank for Quiz and Assessment enrichment.
Provides curated, authentic conceptual, application, and debugging questions
across all 30 canonical topics to eliminate procedural filler questions.
"""

from typing import Dict, List, Any

TOPIC_SUPPLEMENTAL_QUESTIONS: Dict[str, List[Dict[str, Any]]] = {
    "python": [
        {
            "item_id": "sup_py_01",
            "q": "What is the expected output of `np.array([1, 2, 3]) * np.array([[1], [2]])` using NumPy broadcasting?",
            "question": "What is the expected output of `np.array([1, 2, 3]) * np.array([[1], [2]])` using NumPy broadcasting?",
            "options": [
                "A 2D array of shape (2, 3): [[1, 2, 3], [2, 4, 6]]",
                "A 1D array of shape (3,): [1, 4, 3]",
                "A ValueError indicating incompatible array shapes (3,) and (2, 1)",
                "A scalar inner product value of 14"
            ],
            "answer": "A 2D array of shape (2, 3): [[1, 2, 3], [2, 4, 6]]",
            "correct_answer": "A 2D array of shape (2, 3): [[1, 2, 3], [2, 4, 6]]",
            "knowledge_components": ["python"],
            "difficulty": 3,
            "prerequisite_components": [],
            "source": "autolearn_supplemental_curated",
            "explanation": "NumPy broadcasts shape (3,) to (1, 3) and pairs it with (2, 1) along matching dimensions to produce an outer product grid of shape (2, 3)."
        },
        {
            "item_id": "sup_py_02",
            "q": "In Pandas, which method avoids SettingWithCopyWarning when creating a filtered subset of a DataFrame for modification?",
            "question": "In Pandas, which method avoids SettingWithCopyWarning when creating a filtered subset of a DataFrame for modification?",
            "options": [
                "df[df['col'] > 0].copy()",
                "df.filter(like='col')",
                "df.drop_duplicates()",
                "df.reset_index(drop=False)"
            ],
            "answer": "df[df['col'] > 0].copy()",
            "correct_answer": "df[df['col'] > 0].copy()",
            "knowledge_components": ["python"],
            "difficulty": 2,
            "prerequisite_components": [],
            "source": "autolearn_supplemental_curated",
            "explanation": "Calling .copy() explicitly allocates an independent DataFrame memory buffer, ensuring subsequent assignments do not inadvertently attempt to write through a slice view."
        }
    ],
    "data preprocessing": [
        {
            "item_id": "sup_prep_01",
            "q": "Why must scalers (e.g. StandardScaler) be fit strictly on the training set and only used to transform the test set?",
            "question": "Why must scalers (e.g. StandardScaler) be fit strictly on the training set and only used to transform the test set?",
            "options": [
                "To prevent data leakage by ensuring test set distribution statistics (mean, variance) do not leak into training",
                "Because test sets are always too small to compute a sample variance",
                "Because Scikit-learn throws an error if fit() is called on test data",
                "To automatically convert categorical columns to integers"
            ],
            "answer": "To prevent data leakage by ensuring test set distribution statistics (mean, variance) do not leak into training",
            "correct_answer": "To prevent data leakage by ensuring test set distribution statistics (mean, variance) do not leak into training",
            "knowledge_components": ["data preprocessing"],
            "difficulty": 3,
            "prerequisite_components": ["python"],
            "source": "autolearn_supplemental_curated",
            "explanation": "Fitting scalers on combined data leaks unseen validation or test distribution parameters into the training pipeline, leading to overly optimistic test performance."
        },
        {
            "item_id": "sup_prep_02",
            "q": "When dealing with high-cardinality nominal features (e.g., zip codes with 1,000 distinct values), why is one-hot encoding problematic?",
            "question": "When dealing with high-cardinality nominal features (e.g., zip codes with 1,000 distinct values), why is one-hot encoding problematic?",
            "options": [
                "Creates an ultra-sparse matrix with 1,000 columns, causing memory bloat and the curse of dimensionality",
                "Fails because one-hot encoding only supports up to 10 unique classes",
                "Distorts the mathematical distance between numeric target variables",
                "Forces decision trees to overfit on continuous numeric values"
            ],
            "answer": "Creates an ultra-sparse matrix with 1,000 columns, causing memory bloat and the curse of dimensionality",
            "correct_answer": "Creates an ultra-sparse matrix with 1,000 columns, causing memory bloat and the curse of dimensionality",
            "knowledge_components": ["data preprocessing"],
            "difficulty": 3,
            "prerequisite_components": ["python"],
            "source": "autolearn_supplemental_curated",
            "explanation": "One-hot encoding high-cardinality features introduces hundreds of sparse columns, drastically increasing memory overhead and leading to severe tree splitting inefficiency; target encoding or embeddings are preferred."
        }
    ],
    "linear regression": [
        {
            "item_id": "sup_linreg_01",
            "q": "What happens to the OLS weight estimate when two predictor features are perfectly collinear (correlation r = 1.0)?",
            "question": "What happens to the OLS weight estimate when two predictor features are perfectly collinear (correlation r = 1.0)?",
            "options": [
                "The Gram matrix (X^T * X) becomes singular and non-invertible, making analytical weight solutions non-unique",
                "The regression line automatically converts into a decision tree",
                "Mean Squared Error increases to exactly 1.0",
                "The model reduces the learning rate to zero automatically"
            ],
            "answer": "The Gram matrix (X^T * X) becomes singular and non-invertible, making analytical weight solutions non-unique",
            "correct_answer": "The Gram matrix (X^T * X) becomes singular and non-invertible, making analytical weight solutions non-unique",
            "knowledge_components": ["linear regression"],
            "difficulty": 4,
            "prerequisite_components": ["python", "data preprocessing"],
            "source": "autolearn_supplemental_curated",
            "explanation": "Perfect multicollinearity causes rank deficiency: (X^T * X)^(-1) does not exist, creating infinite degenerate weight combinations. L2 Ridge regularization resolves this by adding lambda * I to restore invertibility."
        },
        {
            "item_id": "sup_linreg_02",
            "q": "In linear regression residual analysis, what does a funnel-shaped residual plot indicate?",
            "question": "In linear regression residual analysis, what does a funnel-shaped residual plot indicate?",
            "options": [
                "Heteroscedasticity: non-constant error variance violating Gauss-Markov assumptions",
                "Perfect linear correlation between all features",
                "Underfitting due to an excessively large L1 penalty",
                "Overfitting caused by low polynomial degrees"
            ],
            "answer": "Heteroscedasticity: non-constant error variance violating Gauss-Markov assumptions",
            "correct_answer": "Heteroscedasticity: non-constant error variance violating Gauss-Markov assumptions",
            "knowledge_components": ["linear regression"],
            "difficulty": 3,
            "prerequisite_components": ["python", "data preprocessing"],
            "source": "autolearn_supplemental_curated",
            "explanation": "Heteroscedasticity occurs when error variance grows or shrinks across predicted values (e.g. wider spread for larger predictions), requiring log transformations or weighted least squares."
        }
    ],
    "classification": [
        {
            "item_id": "sup_clf_01",
            "q": "Why is ROC-AUC widely preferred over accuracy when evaluating fraud detection models where 99.8% of transactions are legitimate?",
            "question": "Why is ROC-AUC widely preferred over accuracy when evaluating fraud detection models where 99.8% of transactions are legitimate?",
            "options": [
                "A trivial dummy model predicting 'no fraud' achieves 99.8% accuracy but 0.50 ROC-AUC, exposing complete lack of discrimination",
                "Accuracy cannot be calculated on binary datasets",
                "ROC-AUC is faster to compute on GPU hardware than accuracy",
                "ROC-AUC penalizes True Negatives more severely than False Positives"
            ],
            "answer": "A trivial dummy model predicting 'no fraud' achieves 99.8% accuracy but 0.50 ROC-AUC, exposing complete lack of discrimination",
            "correct_answer": "A trivial dummy model predicting 'no fraud' achieves 99.8% accuracy but 0.50 ROC-AUC, exposing complete lack of discrimination",
            "knowledge_components": ["classification"],
            "difficulty": 3,
            "prerequisite_components": ["python", "data preprocessing", "linear regression"],
            "source": "autolearn_supplemental_curated",
            "explanation": "Under extreme class imbalance, raw accuracy reflects class proportions rather than classifier capability. ROC-AUC measures ranking discrimination across all possible decision thresholds."
        },
        {
            "item_id": "sup_clf_02",
            "q": "In multi-class classification with K classes, how does the Softmax function transform the raw logit vector z?",
            "question": "In multi-class classification with K classes, how does the Softmax function transform the raw logit vector z?",
            "options": [
                "Softmax(z_i) = exp(z_i) / sum_j(exp(z_j)), producing a valid categorical probability distribution summing to 1.0",
                "Softmax(z_i) = max(0, z_i), clamping negative logits to zero",
                "Softmax(z_i) = tanh(z_i), bounding values between -1 and +1",
                "Softmax(z_i) = 1 / (1 + z_i^2), computing an inverse quadratic decay"
            ],
            "answer": "Softmax(z_i) = exp(z_i) / sum_j(exp(z_j)), producing a valid categorical probability distribution summing to 1.0",
            "correct_answer": "Softmax(z_i) = exp(z_i) / sum_j(exp(z_j)), producing a valid categorical probability distribution summing to 1.0",
            "knowledge_components": ["classification"],
            "difficulty": 3,
            "prerequisite_components": ["python", "data preprocessing", "linear regression"],
            "source": "autolearn_supplemental_curated",
            "explanation": "Softmax exponentiates logits so all values are positive and divides by their sum, yielding non-negative probabilities that strictly sum to 1.0."
        }
    ],
    "decision trees": [
        {
            "item_id": "sup_tree_01",
            "q": "How does Gini Impurity differ from Shannon Entropy as split criteria in decision tree algorithms (CART)?",
            "question": "How does Gini Impurity differ from Shannon Entropy as split criteria in decision tree algorithms (CART)?",
            "options": [
                "Gini Impurity = 1 - sum(p_i^2) avoids logarithmic calculations, making it computationally faster while yielding near-identical tree splits",
                "Gini Impurity only applies to continuous regression targets, not classification",
                "Entropy cannot handle binary classification problems",
                "Gini Impurity guarantees globally optimal tree depth without pruning"
            ],
            "answer": "Gini Impurity = 1 - sum(p_i^2) avoids logarithmic calculations, making it computationally faster while yielding near-identical tree splits",
            "correct_answer": "Gini Impurity = 1 - sum(p_i^2) avoids logarithmic calculations, making it computationally faster while yielding near-identical tree splits",
            "knowledge_components": ["decision trees"],
            "difficulty": 3,
            "prerequisite_components": ["python", "classification"],
            "source": "autolearn_supplemental_curated",
            "explanation": "Gini impurity (1 - sum(p_i^2)) avoids computing transcendent log2 functions for every split candidate across millions of feature values, making CART implementations in Scikit-learn highly efficient."
        }
    ],
    "clustering": [
        {
            "item_id": "sup_clust_01",
            "q": "Why is K-Means clustering sensitive to initial centroid placement, and how does K-Means++ address this?",
            "question": "Why is K-Means clustering sensitive to initial centroid placement, and how does K-Means++ address this?",
            "options": [
                "Random initialization can get trapped in poor local minima; K-Means++ samples initial centers with probability proportional to squared distance from existing centers",
                "K-Means++ replaces centroid calculations with gradient descent backpropagation",
                "Random initialization causes memory leaks; K-Means++ preallocates memory buffers",
                "K-Means++ converts unsupervised clusters into supervised regression labels"
            ],
            "answer": "Random initialization can get trapped in poor local minima; K-Means++ samples initial centers with probability proportional to squared distance from existing centers",
            "correct_answer": "Random initialization can get trapped in poor local minima; K-Means++ samples initial centers with probability proportional to squared distance from existing centers",
            "knowledge_components": ["clustering"],
            "difficulty": 3,
            "prerequisite_components": ["python", "data preprocessing"],
            "source": "autolearn_supplemental_curated",
            "explanation": "K-Means++ spreads out initial cluster centroids across data space by sampling next centers proportional to D(x)^2, providing an O(log k) competitive ratio guarantee over standard Lloyd's algorithm."
        }
    ],
    "neural networks": [
        {
            "item_id": "sup_nn_01",
            "q": "How does Dropout regularization prevent overfitting in deep neural networks during training?",
            "question": "How does Dropout regularization prevent overfitting in deep neural networks during training?",
            "options": [
                "Randomly zeroes out a fraction p of hidden neuron activations per training step, preventing co-adaptation of features",
                "Permanently deletes neurons with weights close to zero after every epoch",
                "Scales the learning rate down by a factor of (1 - p) at each iteration",
                "Clips gradient vectors whose L2 norm exceeds a predefined threshold"
            ],
            "answer": "Randomly zeroes out a fraction p of hidden neuron activations per training step, preventing co-adaptation of features",
            "correct_answer": "Randomly zeroes out a fraction p of hidden neuron activations per training step, preventing co-adaptation of features",
            "knowledge_components": ["neural networks"],
            "difficulty": 3,
            "prerequisite_components": ["python", "classification"],
            "source": "autolearn_supplemental_curated",
            "explanation": "Dropout prevents neurons from relying on specific companion activations to correct their errors (co-adaptation), effectively training an implicit ensemble of sub-networks with shared weights."
        }
    ],
    "statistics": [
        {
            "item_id": "sup_stat_01",
            "q": "What fundamental principle does the Central Limit Theorem (CLT) establish in inferential statistics?",
            "question": "What fundamental principle does the Central Limit Theorem (CLT) establish in inferential statistics?",
            "options": [
                "The distribution of sample means approaches a normal Gaussian distribution as sample size N grows, regardless of the underlying population shape",
                "All real-world dataset distributions are perfectly normal",
                "Sample variance always equals population standard deviation",
                "The median is always strictly greater than the arithmetic mean"
            ],
            "answer": "The distribution of sample means approaches a normal Gaussian distribution as sample size N grows, regardless of the underlying population shape",
            "correct_answer": "The distribution of sample means approaches a normal Gaussian distribution as sample size N grows, regardless of the underlying population shape",
            "knowledge_components": ["statistics"],
            "difficulty": 3,
            "prerequisite_components": ["python"],
            "source": "autolearn_supplemental_curated",
            "explanation": "The CLT guarantees that the sampling distribution of the mean is approximately normal for sufficiently large N (typically N >= 30), enabling confidence intervals and hypothesis testing even on non-normal populations."
        }
    ],
    "reinforcement learning": [
        {
            "item_id": "sup_rl_01",
            "q": "In deep Q-learning (DQN), what is the primary role of the Experience Replay buffer?",
            "question": "In deep Q-learning (DQN), what is the primary role of the Experience Replay buffer?",
            "options": [
                "Breaks temporal correlations between consecutive transition tuples (s, a, r, s') and stabilizes gradient descent updates",
                "Stores trained neural weights on hard disk to avoid memory overflow",
                "Calculates closed-form matrix inversions for the value function",
                "Replaces the policy network with a deterministic lookup table"
            ],
            "answer": "Breaks temporal correlations between consecutive transition tuples (s, a, r, s') and stabilizes gradient descent updates",
            "correct_answer": "Breaks temporal correlations between consecutive transition tuples (s, a, r, s') and stabilizes gradient descent updates",
            "knowledge_components": ["reinforcement learning"],
            "difficulty": 3,
            "prerequisite_components": ["probability", "neural networks"],
            "source": "autolearn_supplemental_curated",
            "explanation": "Successive transitions in an RL environment are highly correlated. Sampling uniformly at random from a large replay buffer decorrelates training batches and allows sample-efficient data reuse."
        }
    ]
}


def get_supplemental_questions(topic: str) -> List[Dict[str, Any]]:
    """Returns curated supplemental questions for a topic to enrich quizzes without procedural templates."""
    clean = str(topic).strip().lower()
    return list(TOPIC_SUPPLEMENTAL_QUESTIONS.get(clean, []))
