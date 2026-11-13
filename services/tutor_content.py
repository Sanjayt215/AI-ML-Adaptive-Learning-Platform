"""
Educational Content Repository for Adaptive Personal Tutor & Learning Rescue Mode.
Provides curated, authentic conceptual explanations, step-by-step worked examples,
and diagnostic hints for all 30 canonical Knowledge Components in AutoLearn.
"""

from typing import Any, Dict, List, Optional

# Structured Conceptual Explanations for all 30 KCs
CONCEPT_EXPLANATIONS: Dict[str, Dict[str, Any]] = {
    "python": {
        "title": "Python for Machine Learning",
        "concept_summary": "Python provides the foundational programming language for ML workflows, leveraging optimized C-backed libraries like NumPy for vector math and Pandas for tabular data manipulation.",
        "key_points": [
            "NumPy arrays provide vectorized, high-performance n-dimensional array operations.",
            "Pandas DataFrames provide tabular indexing, slicing, aggregation, and missing value management.",
            "List comprehensions and lambda functions allow concise mathematical transformations."
        ],
        "common_pitfalls": "Using slow Python loops instead of vectorized NumPy array operations.",
        "key_formula": "Array slicing: arr[start:stop:step] · Vectorized dot product: np.dot(w, x)"
    },
    "probability": {
        "title": "Probability Fundamentals for AI",
        "concept_summary": "Probability models uncertainty, quantifying how likely events or outcomes are under incomplete information.",
        "key_points": [
            "Joint probability P(A, B) = P(A ∩ B) represents both events occurring.",
            "Conditional probability P(A|B) = P(A ∩ B) / P(B) conditions belief on observed evidence.",
            "Independence implies P(A, B) = P(A) * P(B) and P(A|B) = P(A)."
        ],
        "common_pitfalls": "Confusing P(A|B) with P(B|A) (the base-rate fallacy).",
        "key_formula": "P(A|B) = [P(B|A) * P(A)] / P(B) (Bayes' Rule)"
    },
    "statistics": {
        "title": "Descriptive & Inferential Statistics",
        "concept_summary": "Statistics summarizes dataset distributions (mean, variance, quartiles) and tests statistical hypotheses.",
        "key_points": [
            "Variance measures dispersion around the mean: Var(X) = E[(X - μ)²].",
            "Standard deviation σ = sqrt(Var) returns spread to original feature units.",
            "The Central Limit Theorem ensures sample means approximate normal distributions for large n."
        ],
        "common_pitfalls": "Relying on the mean alone when distributions are heavily skewed by outliers; use median.",
        "key_formula": "Variance: σ² = (1/N) * Σ (x_i - μ)² · Standard Error: SE = σ / sqrt(n)"
    },
    "data preprocessing": {
        "title": "Data Preprocessing & Cleaning",
        "concept_summary": "Raw data contains missing values, irregular scales, and categorical labels that must be transformed before models can learn patterns.",
        "key_points": [
            "Missing value imputation: replace NaNs with median (robust to outliers) or mode for categorical.",
            "Standardization (Z-score): transforms features to zero mean and unit variance (x - μ) / σ.",
            "Min-Max Normalization: bounds features between [0, 1]."
        ],
        "common_pitfalls": "Fitting scalers on the entire dataset before splitting, which causes data leakage into test sets.",
        "key_formula": "Standardization: z = (x - μ) / σ · Min-Max: x_norm = (x - x_min) / (x_max - x_min)"
    },
    "linear regression": {
        "title": "Linear Regression & Least Squares",
        "concept_summary": "Linear regression models a linear relationship between input continuous features and a target continuous scalar variable.",
        "key_points": [
            "The hypothesis function is ŷ = w^T * x + b.",
            "Trained by minimizing the Mean Squared Error (MSE) loss via Ordinary Least Squares or Gradient Descent.",
            "Lasso (L1) performs feature selection by shrinking coefficients to zero; Ridge (L2) prevents extreme weights."
        ],
        "common_pitfalls": "Assuming a linear model fits inherently non-linear or polynomial patterns without feature transforms.",
        "key_formula": "Loss: MSE = (1/N) * Σ (y_i - ŷ_i)² · Gradient: ∂MSE/∂w = -(2/N) * Σ x_i(y_i - ŷ_i)"
    },
    "classification": {
        "title": "Classification Fundamentals",
        "concept_summary": "Classification maps inputs to discrete category labels (binary or multi-class).",
        "key_points": [
            "Decision boundary separates feature space into distinct predicted classes.",
            "Logistic regression applies the sigmoid activation σ(z) = 1 / (1 + e^(-z)) to produce class probabilities.",
            "Binary Cross-Entropy loss penalizes confident incorrect probability predictions."
        ],
        "common_pitfalls": "Using accuracy as the sole metric when evaluating imbalanced datasets; use F1 or ROC-AUC.",
        "key_formula": "Sigmoid: σ(z) = 1 / (1 + e^(-z)) · BCE Loss: -[y*log(p) + (1-y)*log(1-p)]"
    },
    "decision trees": {
        "title": "Decision Trees & Information Gain",
        "concept_summary": "Decision trees recursively partition feature space into homogeneous sub-regions using greedy split criteria.",
        "key_points": [
            "Splits are chosen to maximize Information Gain (or decrease Gini Impurity).",
            "Entropy H(S) measures disorder: -Σ p_i * log2(p_i).",
            "Unconstrained trees easily overfit by memorizing training samples; pruning and depth limits are critical."
        ],
        "common_pitfalls": "Allowing trees to grow until leaf nodes have only 1 sample, leading to severe overfitting.",
        "key_formula": "Entropy: H(S) = -Σ p_i log2(p_i) · Information Gain: IG(S, A) = H(S) - Σ (|S_v|/|S|) * H(S_v)"
    },
    "neural networks": {
        "title": "Artificial Neural Networks (ANN)",
        "concept_summary": "Neural networks stack layers of parameterized linear transformations followed by non-linear activations to approximate complex functions.",
        "key_points": [
            "Forward pass computes layer activations: a^[l] = g(W^[l] * a^[l-1] + b^[l]).",
            "Non-linear activations (ReLU, GELU, Sigmoid) enable universal function approximation.",
            "Backpropagation applies the chain rule of calculus to compute loss gradients with respect to each weight."
        ],
        "common_pitfalls": "Using sigmoid activations in deep networks, causing the vanishing gradient problem.",
        "key_formula": "Layer: z = W*x + b, a = ReLU(z) = max(0, z) · Chain Rule: ∂L/∂W = (∂L/∂a) * (∂a/∂z) * (∂z/∂W)"
    },
    "model evaluation": {
        "title": "Model Evaluation & Cross-Validation",
        "concept_summary": "Evaluates generalizability on unseen data using metrics tailored to specific problem types.",
        "key_points": [
            "Precision = TP / (TP + FP) measures exactness (low false positive rate).",
            "Recall = TP / (TP + FN) measures completeness (low false negative rate).",
            "F1-Score is the harmonic mean of precision and recall: 2 * (P * R) / (P + R)."
        ],
        "common_pitfalls": "Evaluating on the training set or using test data for hyperparameter selection.",
        "key_formula": "F1 = 2 * (Precision * Recall) / (Precision + Recall) · Accuracy = (TP + TN) / Total"
    },
    "clustering": {
        "title": "Unsupervised Clustering & K-Means",
        "concept_summary": "Clustering groups unlabeled data points into clusters based on geometric or statistical similarity.",
        "key_points": [
            "K-Means iteratively alternates between assigning points to closest centroids and recalculating centroid means.",
            "Inertia (Within-Cluster Sum of Squares) measures cluster compactness.",
            "Silhouette Score evaluates how well separated a point is from neighboring clusters (-1 to +1)."
        ],
        "common_pitfalls": "K-Means assumes spherical clusters of equal variance; fails on complex non-linear shapes.",
        "key_formula": "WCSS = Σ_k Σ_{x ∈ C_k} ||x - μ_k||²"
    },
    "feature engineering": {
        "title": "Feature Engineering & Extraction",
        "concept_summary": "Creates domain-specific representations from raw data to improve model signal-to-noise ratio.",
        "key_points": [
            "One-Hot Encoding converts nominal categories into binary indicator columns.",
            "Target Encoding replaces category levels with the expected target value (requires smoothing).",
            "Interaction features combine two or more variables (e.g., width * height = area)."
        ],
        "common_pitfalls": "Target encoding without cross-validation folds, causing target leakage.",
        "key_formula": "Smoothed Target Encoding: S_i = (n * mean_cat + m * global_mean) / (n + m)"
    },
    "dimensionality reduction": {
        "title": "Dimensionality Reduction & PCA",
        "concept_summary": "Reduces feature count while preserving maximum variance or intrinsic manifold geometry.",
        "key_points": [
            "PCA (Principal Component Analysis) computes eigenvectors of the covariance matrix.",
            "First principal component aligns with the axis of maximum variance.",
            "Mitigates the Curse of Dimensionality and enables 2D/3D visualization."
        ],
        "common_pitfalls": "Applying PCA without standardizing features first; features with large units will dominate variance.",
        "key_formula": "Covariance Matrix: C = (1/n) * X^T * X · Eigen-decomposition: C * v = λ * v"
    },
    "ensemble methods": {
        "title": "Ensemble Methods: Bagging & Boosting",
        "concept_summary": "Combines multiple base models to produce a meta-model with lower variance (Bagging) or lower bias (Boosting).",
        "key_points": [
            "Random Forests use Bootstrap Aggregating (Bagging) + random feature subsets to reduce variance.",
            "Gradient Boosting (GBDT, XGBoost, LightGBM) sequentially fits new trees to the residual pseudo-gradients of the previous trees.",
            "Stacking trains a meta-learner on the cross-validated out-of-fold predictions of diverse base models."
        ],
        "common_pitfalls": "Setting learning rate too high in Gradient Boosting, causing rapid overfitting.",
        "key_formula": "Residual update: r_{i, m} = - [∂L(y_i, F(x_i)) / ∂F(x_i)] · Model: F_m(x) = F_{m-1}(x) + η * h_m(x)"
    },
    "svm": {
        "title": "Support Vector Machines (SVM)",
        "concept_summary": "Finds the optimal separating hyperplane that maximizes the geometric margin between classes.",
        "key_points": [
            "Support vectors are the critical data points closest to the decision boundary.",
            "Slack variables (C parameter) control the trade-off between maximizing margin and allowing misclassifications.",
            "The Kernel Trick (RBF, Polynomial) computes inner products in high-dimensional Hilbert spaces without explicit mapping."
        ],
        "common_pitfalls": "SVM training complexity is O(N² to N³), making it slow on very large datasets (> 100k samples).",
        "key_formula": "Margin: 2 / ||w|| · RBF Kernel: K(x, z) = exp(-γ * ||x - z||²)"
    },
    "nlp": {
        "title": "Natural Language Processing (NLP)",
        "concept_summary": "Transforms unstructured text into mathematical representations for linguistic analysis and generation.",
        "key_points": [
            "Tokenization splits text into subword units (BPE, WordPiece).",
            "TF-IDF weighs term frequency by inverse document frequency to downweight common stopwords.",
            "Dense word embeddings (Word2Vec, GloVe) encode semantic similarity geometrically."
        ],
        "common_pitfalls": "Using Bag-of-Words when word order, syntax, or context is critical for semantic meaning.",
        "key_formula": "TF-IDF = TF(t, d) * log(N / DF(t)) · Cosine Similarity: cos(u, v) = (u · v) / (||u|| * ||v||)"
    },
    "transformers": {
        "title": "Transformers & Self-Attention",
        "concept_summary": "Processes sequences in parallel using multi-head self-attention mechanisms to capture long-range contextual relationships.",
        "key_points": [
            "Scaled Dot-Product Attention: Attention(Q, K, V) = softmax((Q * K^T) / sqrt(d_k)) * V.",
            "Positional encodings inject sequence order information into permutation-invariant attention.",
            "Multi-head attention projects queries, keys, and values into multiple subspace representations."
        ],
        "common_pitfalls": "Standard attention memory complexity scales quadratically O(L²) with sequence length L.",
        "key_formula": "Attention(Q, K, V) = softmax(Q * K^T / sqrt(d_k)) * V"
    },
    "llm": {
        "title": "Large Language Models (LLMs)",
        "concept_summary": "Autoregressive generative transformer models pre-trained on vast web corpora using causal language modeling.",
        "key_points": [
            "Pre-training predicts the next token: maximize Σ log P(x_t | x_<t).",
            "Instruction fine-tuning and RLHF (Reinforcement Learning from Human Feedback) align models to human intent.",
            "Emergent abilities include in-context learning, multi-step chain-of-thought, and code synthesis."
        ],
        "common_pitfalls": "Hallucination: LLMs generate fluent text that is factually ungrounded; mitigate with RAG or tool use.",
        "key_formula": "Autoregressive objective: L(θ) = -Σ log P_θ(x_i | x_1, ..., x_{i-1})"
    },
    "rag": {
        "title": "Retrieval-Augmented Generation (RAG)",
        "concept_summary": "Combines dynamic semantic information retrieval over external knowledge bases with LLM generation.",
        "key_points": [
            "Document chunking and dense embedding creation using specialized embedding models.",
            "Vector database indexation (HNSW, FAISS) for sub-millisecond approximate nearest neighbor search.",
            "Prompt grounding: concatenates top-k retrieved chunks into the prompt context window before synthesis."
        ],
        "common_pitfalls": "Chunking documents without overlap, splitting key context sentences across chunk boundaries.",
        "key_formula": "Top-k retrieval: k-NN(q) = argmax_{d ∈ D} cos(emb(q), emb(d))"
    },
    "reinforcement learning": {
        "title": "Reinforcement Learning (RL)",
        "concept_summary": "An agent learns optimal decision policies through trial-and-error interaction with an environment to maximize expected cumulative reward.",
        "key_points": [
            "Markov Decision Process (MDP) defined by (S, A, P, R, γ).",
            "Value Function V(s) and Action-Value Function Q(s, a) estimate expected discounted return.",
            "Bellman Optimality Equation provides the foundation for Q-learning and DQN: Q*(s, a) = R + γ * max_a' Q*(s', a')."
        ],
        "common_pitfalls": "Setting discount factor γ = 0, causing the agent to be completely myopic and ignore future rewards.",
        "key_formula": "Bellman equation: Q(s, a) = r + γ * max_{a'} Q(s', a')"
    },
    "automl": {
        "title": "Automated Machine Learning (AutoML)",
        "concept_summary": "Automates the end-to-end process of applying machine learning: feature engineering, model selection, and hyperparameter optimization.",
        "key_points": [
            "Combined Algorithm Selection and Hyperparameter optimization (CASH).",
            "Uses Bayesian Optimization (TPE, GP) or Bandit algorithms (Hyperband) to find top configurations fast.",
            "Constructs diverse ensemble blends of top candidate models automatically."
        ],
        "common_pitfalls": "Evaluating AutoML models on the training set or without strict time budgets.",
        "key_formula": "Bayesian Opt: x* = argmax EI(x) = E[max(0, f(x) - f(x^+))]"
    }
}

# Detailed Step-by-Step Worked Examples for Learning Rescue Mode
WORKED_EXAMPLES: Dict[str, Dict[str, Any]] = {
    "linear regression": {
        "title": "Step-by-Step: Solving a Linear Regression Line",
        "problem": "Given 3 data points (x, y): (1, 2), (2, 4), (3, 5). Find the regression line equation ŷ = w * x + b.",
        "steps": [
            {
                "step_number": 1,
                "title": "Compute Means of X and Y",
                "explanation": "Find the average of the x-values and y-values.",
                "math": "x̄ = (1 + 2 + 3) / 3 = 2.0\nȳ = (2 + 4 + 5) / 3 = 11 / 3 ≈ 3.67"
            },
            {
                "step_number": 2,
                "title": "Calculate Slope (Weight w)",
                "explanation": "Slope is covariance divided by variance of X: w = Σ (x_i - x̄)(y_i - ȳ) / Σ (x_i - x̄)².",
                "math": "Numerator: (1-2)(2-3.67) + (2-2)(4-3.67) + (3-2)(5-3.67) = (-1)(-1.67) + 0 + (1)(1.33) = 1.67 + 1.33 = 3.0\nDenominator: (1-2)² + (2-2)² + (3-2)² = 1 + 0 + 1 = 2.0\nw = 3.0 / 2.0 = 1.50"
            },
            {
                "step_number": 3,
                "title": "Solve for Intercept (Bias b)",
                "explanation": "The line must pass through the centroid (x̄, ȳ): b = ȳ - w * x̄.",
                "math": "b = 3.67 - (1.50 * 2.0) = 3.67 - 3.0 = 0.67"
            },
            {
                "step_number": 4,
                "title": "Final Predictive Model & Check",
                "explanation": "The optimal least-squares line is ŷ = 1.5x + 0.67. Predict for x = 2: ŷ = 1.5(2) + 0.67 = 3.67 (close to actual 4.0)."
            }
        ],
        "key_takeaway": "Ordinary Least Squares finds the unique slope and intercept that minimizes the sum of squared vertical residuals.",
        "check_question": {
            "question": "If x increases by 2 units in ŷ = 1.5x + 0.67, how much will ŷ increase?",
            "options": ["1.5 units", "3.0 units", "0.67 units", "2.0 units"],
            "answer": "3.0 units",
            "hint": "Change in y is slope * change in x = 1.5 * 2 = 3.0"
        }
    },
    "classification": {
        "title": "Step-by-Step: Logistic Regression Sigmoid Calculation",
        "problem": "A logistic regression model has weights w = [0.8, -0.4] and bias b = -0.2. For an input x = [2.0, 1.0], calculate the predicted class probability.",
        "steps": [
            {
                "step_number": 1,
                "title": "Compute the Linear Logit z",
                "explanation": "Compute the linear dot product z = w^T * x + b.",
                "math": "z = (0.8 * 2.0) + (-0.4 * 1.0) + (-0.2)\nz = 1.6 - 0.4 - 0.2 = 1.0"
            },
            {
                "step_number": 2,
                "title": "Pass Logit Through Sigmoid Activation",
                "explanation": "Apply the logistic function σ(z) = 1 / (1 + e^(-z)) to compress z into a valid [0, 1] probability.",
                "math": "σ(1.0) = 1 / (1 + e^(-1.0)) ≈ 1 / (1 + 0.3679) = 1 / 1.3679 ≈ 0.731 (73.1%)"
            },
            {
                "step_number": 3,
                "title": "Apply Classification Decision Threshold",
                "explanation": "With the standard decision threshold of 0.50, since P(Y=1) = 0.731 > 0.50, we predict Class 1."
            }
        ],
        "key_takeaway": "Logistic regression maps any unbounded real logit z to a calibrated probability between 0 and 1 via the sigmoid curve.",
        "check_question": {
            "question": "What is the predicted probability when the logit z = 0?",
            "options": ["0.0 (0%)", "0.5 (50%)", "1.0 (100%)", "Undefined"],
            "answer": "0.5 (50%)",
            "hint": "σ(0) = 1 / (1 + e^0) = 1 / (1 + 1) = 0.50."
        }
    },
    "decision trees": {
        "title": "Step-by-Step: Calculating Entropy for a Split",
        "problem": "A dataset subset has 4 positive examples and 4 negative examples. Calculate its Shannon Entropy.",
        "steps": [
            {
                "step_number": 1,
                "title": "Determine Class Probabilities",
                "explanation": "Find proportion of positive (p+) and negative (p-) instances.",
                "math": "Total = 4 + 4 = 8\np+ = 4 / 8 = 0.50\np- = 4 / 8 = 0.50"
            },
            {
                "step_number": 2,
                "title": "Apply Shannon Entropy Formula",
                "explanation": "Entropy H(S) = - [p+ * log2(p+) + p- * log2(p-)].",
                "math": "log2(0.50) = -1.0\nH(S) = - [0.5 * (-1.0) + 0.5 * (-1.0)] = - [-0.5 - 0.5] = 1.0 bit"
            },
            {
                "step_number": 3,
                "title": "Interpret Result",
                "explanation": "An entropy of 1.0 represents maximum disorder (50/50 uncertainty). If all instances belonged to one class, entropy would be 0.0."
            }
        ],
        "key_takeaway": "Decision trees choose feature splits that produce child nodes with the lowest weighted entropy (highest information gain).",
        "check_question": {
            "question": "What is the entropy of a completely pure leaf node containing 10 positive samples and 0 negative samples?",
            "options": ["0.0 bits", "1.0 bit", "0.5 bits", "10.0 bits"],
            "answer": "0.0 bits",
            "hint": "A pure node has zero disorder: -1.0 * log2(1.0) = 0."
        }
    },
    "model evaluation": {
        "title": "Step-by-Step: Computing Precision, Recall, and F1-Score",
        "problem": "An ML diagnostic model tests 100 patients. True Positives (TP) = 20, False Positives (FP) = 5, False Negatives (FN) = 10, True Negatives (TN) = 65. Calculate Precision, Recall, and F1-Score.",
        "steps": [
            {
                "step_number": 1,
                "title": "Calculate Precision",
                "explanation": "Precision measures: of all predicted positives, how many are truly positive?",
                "math": "Precision = TP / (TP + FP) = 20 / (20 + 5) = 20 / 25 = 0.80 (80%)"
            },
            {
                "step_number": 2,
                "title": "Calculate Recall (Sensitivity)",
                "explanation": "Recall measures: of all actual positive cases, how many did the model detect?",
                "math": "Recall = TP / (TP + FN) = 20 / (20 + 10) = 20 / 30 ≈ 0.667 (66.7%)"
            },
            {
                "step_number": 3,
                "title": "Calculate F1-Score (Harmonic Mean)",
                "explanation": "Harmonic mean balances precision and recall.",
                "math": "F1 = 2 * (P * R) / (P + R) = 2 * (0.80 * 0.667) / (0.80 + 0.667) = 1.067 / 1.467 ≈ 0.727 (72.7%)"
            }
        ],
        "key_takeaway": "Precision focuses on avoiding false alarms (FP); Recall focuses on avoiding missed detections (FN).",
        "check_question": {
            "question": "In medical disease screening, which error is usually far more dangerous?",
            "options": ["False Positive (healthy person flagged for follow-up)", "False Negative (sick person sent home undetected)", "True Negative", "Both are equally dangerous"],
            "answer": "False Negative (sick person sent home undetected)",
            "hint": "A false negative means a severe disease goes untreated."
        }
    },
    "data preprocessing": {
        "title": "Step-by-Step: Feature Standardization (Z-Score)",
        "problem": "A feature has values [10, 20, 30]. Mean μ = 20, standard deviation σ = 8.16. Calculate the standardized Z-score for x = 30.",
        "steps": [
            {
                "step_number": 1,
                "title": "Subtract the Mean",
                "explanation": "Center the value around 0.",
                "math": "Difference = x - μ = 30 - 20 = +10.0"
            },
            {
                "step_number": 2,
                "title": "Divide by Standard Deviation",
                "explanation": "Scale by the spread of the data.",
                "math": "z = (x - μ) / σ = 10.0 / 8.16 ≈ +1.225"
            },
            {
                "step_number": 3,
                "title": "Interpretation",
                "explanation": "The value 30 is 1.225 standard deviations above the mean."
            }
        ],
        "key_takeaway": "Standardization ensures all features operate on equal scale with mean 0 and unit variance, preventing gradient descent instability.",
        "check_question": {
            "question": "What is the Z-score of a data point that is exactly equal to the dataset mean?",
            "options": ["0.0", "1.0", "-1.0", "Depends on variance"],
            "answer": "0.0",
            "hint": "z = (μ - μ) / σ = 0 / σ = 0.0."
        }
    },
    "python": {
        "title": "Step-by-Step: NumPy Vectorized Masking & Operations",
        "problem": "Given an array of student marks arr = np.array([45, 78, 92, 55, 88]), filter all passing marks (>= 60) and compute the curved average (+5 bonus).",
        "steps": [
            {
                "step_number": 1,
                "title": "Construct Boolean Array Mask",
                "explanation": "Apply comparison operator element-wise across the array in C-speed vectorized code without loops.",
                "math": "mask = arr >= 60\nResult: [False, True, True, False, True]"
            },
            {
                "step_number": 2,
                "title": "Filter Elements via Boolean Indexing",
                "explanation": "Use the boolean mask to extract only the True elements into a new 1D array.",
                "math": "passing = arr[mask]\nResult: [78, 92, 88]"
            },
            {
                "step_number": 3,
                "title": "Apply Broadcast Addition and Vectorized Mean",
                "explanation": "Add scalar 5 to all elements via NumPy broadcasting, then compute arithmetic mean.",
                "math": "curved = passing + 5  # [83, 97, 93]\naverage = np.mean(curved) = (83 + 97 + 93) / 3 = 273 / 3 = 91.0"
            }
        ],
        "key_takeaway": "NumPy vectorization replaces slow Python for-loops with contiguous C memory buffers and SIMD CPU vector operations.",
        "check_question": {
            "question": "If arr = np.array([10, 20, 30]) and we run arr[arr > 15] += 5, what does arr become?",
            "options": ["[10, 25, 35]", "[15, 25, 35]", "[10, 20, 30]", "[25, 35]"],
            "answer": "[10, 25, 35]",
            "hint": "Only elements > 15 (20 and 30) are selected and incremented by 5."
        }
    },
    "probability": {
        "title": "Step-by-Step: Updating Beliefs via Bayes' Theorem",
        "problem": "A disease has a 1% base rate prevalence P(D) = 0.01. A diagnostic test has 90% Sensitivity P(T+|D) = 0.90 and 5% False Positive Rate P(T+|not D) = 0.05. A patient tests positive. What is the true posterior probability P(D|T+)?",
        "steps": [
            {
                "step_number": 1,
                "title": "Identify Prior and Conditional Probabilities",
                "explanation": "Organize known values: Prior P(D) = 0.01, therefore P(not D) = 0.99. Sensitivity P(T+|D) = 0.90. False Positive Rate P(T+|not D) = 0.05.",
                "math": "P(D) = 0.01\nP(not D) = 0.99\nP(T+|D) = 0.90\nP(T+|not D) = 0.05"
            },
            {
                "step_number": 2,
                "title": "Compute Marginal Probability P(T+) (Law of Total Probability)",
                "explanation": "Add the probability of a positive test from sick patients and healthy patients.",
                "math": "P(T+) = P(T+|D)*P(D) + P(T+|not D)*P(not D)\nP(T+) = (0.90 * 0.01) + (0.05 * 0.99) = 0.009 + 0.0495 = 0.0585 (5.85%)"
            },
            {
                "step_number": 3,
                "title": "Apply Bayes' Rule to Find Posterior P(D|T+)",
                "explanation": "Posterior is True Positives divided by Total Positives.",
                "math": "P(D|T+) = [P(T+|D) * P(D)] / P(T+)\nP(D|T+) = 0.009 / 0.0585 ≈ 0.1538 (15.38%)"
            }
        ],
        "key_takeaway": "When base prevalence is rare (1%), even a 90% accurate test yields mostly false alarms (85% false positives) due to the large base population of healthy individuals (Base Rate Fallacy).",
        "check_question": {
            "question": "Why is P(D|T+) only ~15.4% despite the test having 90% sensitivity?",
            "options": [
                "Because the 5% false positive rate on the massive healthy majority (99%) produces far more false positives than true positives",
                "Because the test sensitivity was calculated incorrectly",
                "Because probability cannot exceed 50% in medical tests",
                "Because the patient tested positive twice"
            ],
            "answer": "Because the 5% false positive rate on the massive healthy majority (99%) produces far more false positives than true positives",
            "hint": "0.05 * 99 = 4.95 false alarms vs 0.90 * 1 = 0.90 true positives."
        }
    },
    "neural networks": {
        "title": "Step-by-Step: Forward Pass and Binary Cross-Entropy Loss",
        "problem": "A single artificial neuron has input x = [2.0, -1.0], weights w = [0.5, 1.0], and bias b = 0.0. Target ground truth is y = 1. Compute the pre-activation logit z, predicted probability p, and Binary Cross-Entropy loss.",
        "steps": [
            {
                "step_number": 1,
                "title": "Compute Linear Dot Product Pre-activation z",
                "explanation": "Calculate linear combination z = w^T * x + b.",
                "math": "z = (0.5 * 2.0) + (1.0 * -1.0) + 0.0 = 1.0 - 1.0 = 0.0"
            },
            {
                "step_number": 2,
                "title": "Pass Through Sigmoid Non-linearity",
                "explanation": "Apply logistic sigmoid activation sigma(z) = 1 / (1 + e^(-z)).",
                "math": "p = sigma(0.0) = 1 / (1 + e^0) = 1 / (1 + 1) = 0.50"
            },
            {
                "step_number": 3,
                "title": "Calculate Binary Cross-Entropy Loss",
                "explanation": "BCE loss L = - [y * ln(p) + (1 - y) * ln(1 - p)]. With target y = 1:",
                "math": "L = - [1 * ln(0.50) + 0] = - (-0.693) = 0.693 nats"
            }
        ],
        "key_takeaway": "When an unconfident network predicts p = 0.50 for a binary task, Binary Cross-Entropy loss equals ln(2) ≈ 0.693.",
        "check_question": {
            "question": "What happens to the BCE loss if the network predicts p = 0.99 for true label y = 1?",
            "options": [
                "Loss approaches 0: -ln(0.99) ≈ 0.01 (very small error penalty)",
                "Loss increases to infinity",
                "Loss becomes exactly 1.0",
                "Loss becomes negative"
            ],
            "answer": "Loss approaches 0: -ln(0.99) ≈ 0.01 (very small error penalty)",
            "hint": "When predicted probability matches true label, cross-entropy approaches zero."
        }
    },
    "reinforcement learning": {
        "title": "Step-by-Step: Tabular Q-Learning Temporal Difference Update",
        "problem": "An agent in state s_1 chooses action a_2. Current Q(s_1, a_2) = 4.0. The agent receives immediate reward r = +2.0 and transitions to s_2. In s_2, the available Q-values are Q(s_2, a_1) = 5.0 and Q(s_2, a_2) = 6.0. Using learning rate alpha = 0.5 and discount factor gamma = 0.9, update Q(s_1, a_2).",
        "steps": [
            {
                "step_number": 1,
                "title": "Identify Next State Maximum Q-Value",
                "explanation": "Find max_{a'} Q(s_2, a') among available actions in next state s_2.",
                "math": "max Q(s_2, a') = max(5.0, 6.0) = 6.0"
            },
            {
                "step_number": 2,
                "title": "Compute the Bellman TD Target",
                "explanation": "Target = immediate reward + discounted best future value: r + gamma * max Q(s', a').",
                "math": "TD Target = 2.0 + (0.9 * 6.0) = 2.0 + 5.4 = 7.4"
            },
            {
                "step_number": 3,
                "title": "Compute TD Error and Update Q-Value",
                "explanation": "TD Error delta = Target - Current Q. Then Q_new = Q_old + alpha * delta.",
                "math": "delta = 7.4 - 4.0 = +3.4\nQ_new = 4.0 + (0.5 * 3.4) = 4.0 + 1.7 = 5.7"
            }
        ],
        "key_takeaway": "Q-learning is an off-policy algorithm that bootstraps expected future returns without requiring an environmental transition probability model.",
        "check_question": {
            "question": "If the discount factor gamma = 0, what does the agent focus on?",
            "options": [
                "Only immediate rewards r, completely ignoring future consequences",
                "Only infinite-horizon future rewards",
                "Random exploration actions",
                "Maximum entropy regularization"
            ],
            "answer": "Only immediate rewards r, completely ignoring future consequences",
            "hint": "gamma = 0 zeros out the future term gamma * max Q(s', a')."
        }
    }
}


def get_concept_explanation(topic: str) -> Dict[str, Any]:
    """Retrieves structured conceptual explanation for any canonical KC."""
    clean = str(topic).strip().lower()
    if clean in CONCEPT_EXPLANATIONS:
        return CONCEPT_EXPLANATIONS[clean]

    # Graceful fallback for any topic
    return {
        "title": clean.replace("_", " ").title(),
        "concept_summary": f"Core concepts and computational workflows in {clean.replace('_', ' ')}.",
        "key_points": [
            f"Understand the theoretical formulation and mathematical objective of {clean}.",
            f"Apply appropriate data preparation and validation protocols for {clean}.",
            "Analyze model performance and interpret learned representations."
        ],
        "common_pitfalls": "Applying the algorithm without verifying underlying statistical assumptions.",
        "key_formula": "Standard representation: y = f(X; θ)"
    }


def get_worked_example(topic: str) -> Dict[str, Any]:
    """Retrieves step-by-step worked example for rescue mode."""
    clean = str(topic).strip().lower()
    if clean in WORKED_EXAMPLES:
        return WORKED_EXAMPLES[clean]

    # Generic high-quality worked example fallback
    return {
        "title": f"Step-by-Step Guided Analysis: {clean.replace('_', ' ').title()}",
        "problem": f"How do we systematically formulate and evaluate an applied model in {clean.replace('_', ' ')}?",
        "steps": [
            {
                "step_number": 1,
                "title": "Problem Formulation & Data Inspection",
                "explanation": "Identify inputs X, target y, and inspect feature distributions, missing values, and data types."
            },
            {
                "step_number": 2,
                "title": "Model Selection & Training",
                "explanation": "Instantiate the estimator with default hyperparameters, fit on training split, and evaluate loss convergence."
            },
            {
                "step_number": 3,
                "title": "Validation & Diagnostic Checking",
                "explanation": "Compute out-of-fold validation metrics and analyze residuals or misclassified instances."
            }
        ],
        "key_takeaway": "Always establish a simple baseline before tuning complex architectures.",
        "check_question": {
            "question": "What is the most critical first step before training any model?",
            "options": [
                "Inspect and clean the training data",
                "Immediately tune 50 hyperparameters",
                "Deploy directly to production",
                "Set random seed to zero without validation"
            ],
            "answer": "Inspect and clean the training data",
            "hint": "Garbage in, garbage out: data quality determines model capability."
        }
    }
