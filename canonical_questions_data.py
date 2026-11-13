"""
Script to generate the enhanced canonical 52-question bank for autolearn_fullstack/resources.py.
Preserves all 52 canonical item_ids and ensures 100% compliance with validate_item_bank().
"""

import sys
import os

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

# 1. First 10 topics: QUIZ_QUESTIONS
UPGRADED_QUIZ_QUESTIONS = {
    "python": [
        {
            "item_id": "q_py_01",
            "q": "Which Python library provides the core foundation for vectorized N-dimensional arrays and high-performance numerical computation in machine learning?",
            "question": "Which Python library provides the core foundation for vectorized N-dimensional arrays and high-performance numerical computation in machine learning?",
            "options": ["NumPy", "Flask", "OpenCV", "NLTK"],
            "answer": "NumPy",
            "correct_answer": "NumPy",
            "knowledge_components": ["python"],
            "difficulty": 1,
            "prerequisite_components": [],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "recall",
            "question_type": "conceptual",
            "explanation": "NumPy provides the ndarray data structure with contiguous C-level memory buffers and vectorized array operations, forming the numerical computation foundation for SciPy, Pandas, and Scikit-learn.",
            "distractor_explanations": {
                "Flask": "Flask is a lightweight WSGI web framework for serving HTTP APIs, not a numerical array library.",
                "OpenCV": "OpenCV focuses on computer vision algorithms; although it uses NumPy arrays for pixel buffers, NumPy is the underlying numerical array library.",
                "NLTK": "NLTK is a natural language processing toolkit for tokenization and text analysis, not general vectorized numerical computation."
            }
        },
        {
            "item_id": "q_py_02",
            "q": "In Python, which built-in data structure provides average O(1) time complexity for key lookups using an underlying hash table?",
            "question": "In Python, which built-in data structure provides average O(1) time complexity for key lookups using an underlying hash table?",
            "options": ["dictionary", "list", "tuple", "set"],
            "answer": "dictionary",
            "correct_answer": "dictionary",
            "knowledge_components": ["python"],
            "difficulty": 1,
            "prerequisite_components": [],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Python dictionaries (dict) map unique hashable keys to arbitrary values with amortized O(1) lookup, insertion, and deletion complexity via hash table implementation.",
            "distractor_explanations": {
                "list": "Lists are ordered dynamic sequence arrays with O(n) linear search complexity when looking up values by content.",
                "tuple": "Tuples are immutable sequence arrays with O(n) search time, indexing by integer position rather than key-value associations.",
                "set": "Sets use hash tables for O(1) membership testing but store distinct keys only, without associated values."
            }
        },
    ],
    "data preprocessing": [
        {
            "item_id": "q_dataprep_01",
            "q": "What is the primary rationale for applying feature scaling (such as StandardScaler or MinMaxScaler) prior to training distance-based and gradient-based models?",
            "question": "What is the primary rationale for applying feature scaling (such as StandardScaler or MinMaxScaler) prior to training distance-based and gradient-based models?",
            "options": [
                "Prevent features with larger numerical magnitudes from dominating distance metrics and gradients",
                "Increase the number of rows available for cross-validation",
                "Automatically impute missing values across correlated columns",
                "Transform categorical text variables into binary integer flags"
            ],
            "answer": "Prevent features with larger numerical magnitudes from dominating distance metrics and gradients",
            "correct_answer": "Prevent features with larger numerical magnitudes from dominating distance metrics and gradients",
            "knowledge_components": ["data preprocessing"],
            "difficulty": 2,
            "prerequisite_components": ["python"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Algorithms like KNN, SVM, and gradient descent calculate Euclidean distances or gradients. Features with large numerical ranges (e.g. salary in thousands) dominate features with small ranges (e.g. age in tens), distorting distance metrics and causing elongated, oscillating loss landscapes.",
            "distractor_explanations": {
                "Increase the number of rows available for cross-validation": "Feature scaling transforms column value ranges; it neither generates synthetic data nor adds rows.",
                "Automatically impute missing values across correlated columns": "Handling missing data requires imputation techniques like SimpleImputer or KNNImputer, which must occur prior to or alongside scaling.",
                "Transform categorical text variables into binary integer flags": "Categorical encoding (such as OneHotEncoder or OrdinalEncoder) converts non-numeric strings to numeric vectors, whereas scaling adjusts numerical ranges."
            }
        },
        {
            "item_id": "q_dataprep_02",
            "q": "When a continuous feature has significant outliers and a heavily skewed distribution with missing entries, which imputation strategy is statistically most robust?",
            "question": "When a continuous feature has significant outliers and a heavily skewed distribution with missing entries, which imputation strategy is statistically most robust?",
            "options": [
                "Median imputation",
                "Mean imputation",
                "Mode imputation",
                "Dropping all columns with any missing values"
            ],
            "answer": "Median imputation",
            "correct_answer": "Median imputation",
            "knowledge_components": ["data preprocessing"],
            "difficulty": 2,
            "prerequisite_components": ["python"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "application",
            "question_type": "conceptual",
            "explanation": "The median represents the 50th percentile and is invariant to extreme tail outliers, making it statistically more robust than the mean for skewed numerical distributions.",
            "distractor_explanations": {
                "Mean imputation": "The arithmetic mean is pulled towards extreme outlier values, which introduces severe bias into imputed values.",
                "Mode imputation": "The mode is suitable for discrete categorical variables, but typically ineffective for continuous real-valued measurements.",
                "Dropping all columns with any missing values": "Dropping entire columns indiscriminately destroys predictive signal and reduces sample statistical power."
            }
        },
    ],
    "linear regression": [
        {
            "item_id": "q_linreg_01",
            "q": "What primary supervised learning task does standard Linear Regression model continuous targets for?",
            "question": "What primary supervised learning task does standard Linear Regression model continuous targets for?",
            "options": [
                "Regression",
                "Clustering",
                "Association rules",
                "Image segmentation"
            ],
            "answer": "Regression",
            "correct_answer": "Regression",
            "knowledge_components": ["linear regression"],
            "difficulty": 2,
            "prerequisite_components": ["python", "data preprocessing"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "recall",
            "question_type": "conceptual",
            "explanation": "Linear regression models continuous numerical scalar targets y from input features x, which is the foundational formulation of regression (in contrast to discrete categorical labels in classification or unlabeled data in clustering).",
            "distractor_explanations": {
                "Clustering": "Clustering is unsupervised grouping of unlabeled data without target variables.",
                "Association rules": "Association rule mining identifies transaction item co-occurrences (e.g. Apriori), not continuous numeric prediction.",
                "Image segmentation": "Image segmentation performs pixel-level categorical classification, not scalar continuous linear regression."
            }
        },
        {
            "item_id": "q_linreg_02",
            "q": "How does Lasso (L1) regularization fundamentally differ from Ridge (L2) regularization in regularized linear models?",
            "question": "How does Lasso (L1) regularization fundamentally differ from Ridge (L2) regularization in regularized linear models?",
            "options": [
                "Lasso uses an absolute weight penalty that can shrink redundant coefficients exactly to zero for feature selection",
                "Ridge completely eliminates irrelevant coefficients to create sparse models",
                "Lasso minimizes Mean Absolute Error while Ridge minimizes Mean Squared Error",
                "Ridge is only applicable to binary classification models whereas Lasso is for regression"
            ],
            "answer": "Lasso uses an absolute weight penalty that can shrink redundant coefficients exactly to zero for feature selection",
            "correct_answer": "Lasso uses an absolute weight penalty that can shrink redundant coefficients exactly to zero for feature selection",
            "knowledge_components": ["linear regression"],
            "difficulty": 3,
            "prerequisite_components": ["python", "data preprocessing"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "analysis",
            "question_type": "conceptual",
            "explanation": "Lasso adds an L1 norm penalty lambda * sum(|w_i|). Because L1 contours have sharp diamond vertices along coordinate axes, the optimization optimum frequently lands on axes, driving non-essential coefficients to exactly 0.",
            "distractor_explanations": {
                "Ridge completely eliminates irrelevant coefficients to create sparse models": "Ridge adds an L2 penalty lambda * sum(w_i^2), shrinking weights asymptotically towards zero without setting them exactly to zero.",
                "Lasso minimizes Mean Absolute Error while Ridge minimizes Mean Squared Error": "Both Lasso and Ridge retain MSE as their primary data loss term; they differ strictly in their penalty regularization term.",
                "Ridge is only applicable to binary classification models whereas Lasso is for regression": "Both Ridge and Lasso are regression regularizers that can also be applied to Logistic Regression classifiers."
            }
        },
    ],
    "classification": [
        {
            "item_id": "q_clf_01",
            "q": "In binary logistic regression, which mathematical activation function maps linear logits z = w^T*x + b into calibrated class probabilities between 0 and 1?",
            "question": "In binary logistic regression, which mathematical activation function maps linear logits z = w^T*x + b into calibrated class probabilities between 0 and 1?",
            "options": [
                "Sigmoid (Logistic) function",
                "ReLU (Rectified Linear Unit)",
                "Softmax over unbounded logits",
                "Sign step function"
            ],
            "answer": "Sigmoid (Logistic) function",
            "correct_answer": "Sigmoid (Logistic) function",
            "knowledge_components": ["classification"],
            "difficulty": 2,
            "prerequisite_components": ["python", "data preprocessing", "linear regression"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "The sigmoid function sigma(z) = 1 / (1 + exp(-z)) smoothly maps any real number in (-inf, +inf) to the interval (0, 1), representing the Bernoulli probability P(Y=1|X).",
            "distractor_explanations": {
                "ReLU (Rectified Linear Unit)": "ReLU outputs max(0, z), which is unbounded for positive values and does not produce valid probabilities in [0, 1].",
                "Softmax over unbounded logits": "Softmax generalizes the sigmoid to multi-class categorical distributions (K >= 3), whereas binary logistic regression uses the standard sigmoid.",
                "Sign step function": "The perceptron step function produces discrete binary outputs {0, 1} or {-1, +1} rather than differentiable class probabilities."
            }
        },
        {
            "item_id": "q_clf_02",
            "q": "How does the K-Nearest Neighbors (KNN) algorithm predict the class label of a new query point?",
            "question": "How does the K-Nearest Neighbors (KNN) algorithm predict the class label of a new query point?",
            "options": [
                "Majority vote among the K closest training instances according to a distance metric",
                "Evaluating a learned linear decision hyperplane w^T*x + b = 0",
                "Descending a recursive binary decision tree based on feature thresholds",
                "Computing class likelihoods under conditional independence assumptions"
            ],
            "answer": "Majority vote among the K closest training instances according to a distance metric",
            "correct_answer": "Majority vote among the K closest training instances according to a distance metric",
            "knowledge_components": ["classification"],
            "difficulty": 2,
            "prerequisite_components": ["python", "data preprocessing", "linear regression"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "KNN is a non-parametric, instance-based lazy learner that calculates distances (e.g. Euclidean or Manhattan) between the query and all training points, assigning the most frequent class among the K nearest neighbors.",
            "distractor_explanations": {
                "Evaluating a learned linear decision hyperplane w^T*x + b = 0": "Linear decision hyperplanes are used by Logistic Regression and linear Support Vector Machines, not instance-based KNN.",
                "Descending a recursive binary decision tree based on feature thresholds": "Descending orthogonal binary splits is the inference mechanism of Decision Trees.",
                "Computing class likelihoods under conditional independence assumptions": "Conditional independence likelihood calculation is the mechanism of Naive Bayes classifiers."
            }
        },
    ],
    "decision trees": [
        {
            "item_id": "q_tree_01",
            "q": "What is a primary pedagogical and practical advantage of single Decision Trees compared to complex deep neural networks or ensemble black-boxes?",
            "question": "What is a primary pedagogical and practical advantage of single Decision Trees compared to complex deep neural networks or ensemble black-boxes?",
            "options": [
                "High interpretability through human-readable hierarchical if-else decision rules",
                "Complete immunity to training data overfitting and noise",
                "Superior parameter sample efficiency for ultra-high-dimensional text embeddings",
                "Convex optimization guarantee ensuring global loss minimum convergence"
            ],
            "answer": "High interpretability through human-readable hierarchical if-else decision rules",
            "correct_answer": "High interpretability through human-readable hierarchical if-else decision rules",
            "knowledge_components": ["decision trees"],
            "difficulty": 2,
            "prerequisite_components": ["python", "data preprocessing", "classification"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Decision trees can be visualized and explained as a sequence of transparent if-then decision thresholds, making them directly auditable for domain experts and regulatory compliance.",
            "distractor_explanations": {
                "Complete immunity to training data overfitting and noise": "Unconstrained decision trees are notoriously prone to overfitting, memorizing training noise and creating overly complex leaf partitions.",
                "Superior parameter sample efficiency for ultra-high-dimensional text embeddings": "Linear models and transformer embeddings typically outperform standard single trees on high-dimensional sparse text vectors.",
                "Convex optimization guarantee ensuring global loss minimum convergence": "Tree construction uses greedy heuristic recursive splitting (e.g. CART), which does not guarantee a globally optimal tree."
            }
        },
        {
            "item_id": "q_tree_02",
            "q": "What is the primary role of cost-complexity pruning or setting max_depth in decision tree training?",
            "question": "What is the primary role of cost-complexity pruning or setting max_depth in decision tree training?",
            "options": [
                "Reduce tree variance and overfitting by removing splits that add negligible generalization power",
                "Speed up GPU kernel matrix multiplications during inference",
                "Force the tree to create multi-way oblique non-linear hyperplanes",
                "Automatically scale features so they share equal variance"
            ],
            "answer": "Reduce tree variance and overfitting by removing splits that add negligible generalization power",
            "correct_answer": "Reduce tree variance and overfitting by removing splits that add negligible generalization power",
            "knowledge_components": ["decision trees"],
            "difficulty": 3,
            "prerequisite_components": ["python", "data preprocessing", "classification"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "application",
            "question_type": "conceptual",
            "explanation": "Pruning cuts back subtrees that capture idiosyncratic training sample noise rather than true population patterns, improving out-of-sample generalization.",
            "distractor_explanations": {
                "Speed up GPU kernel matrix multiplications during inference": "Decision tree inference consists of scalar comparisons on CPU rather than GPU dense matrix multiplications.",
                "Force the tree to create multi-way oblique non-linear hyperplanes": "Standard CART decision trees strictly make axis-aligned orthogonal splits on individual features, not oblique hyperplanes.",
                "Automatically scale features so they share equal variance": "Tree-based algorithms are monotonic transformations invariant to feature scaling, so pruning has no scaling function."
            }
        },
    ],
    "clustering": [
        {
            "item_id": "q_clust_01",
            "q": "In unsupervised machine learning, what core optimization task does the standard K-Means algorithm perform?",
            "question": "In unsupervised machine learning, what core optimization task does the standard K-Means algorithm perform?",
            "options": [
                "Partition N observations into K clusters by iteratively minimizing within-cluster sum of squares (inertia)",
                "Fit a maximum-margin linear separator between two pre-labeled classes",
                "Sequentially train weak decision stumps to minimize residual classification error",
                "Project high-dimensional features onto top orthogonal eigenvector axes"
            ],
            "answer": "Partition N observations into K clusters by iteratively minimizing within-cluster sum of squares (inertia)",
            "correct_answer": "Partition N observations into K clusters by iteratively minimizing within-cluster sum of squares (inertia)",
            "knowledge_components": ["clustering"],
            "difficulty": 2,
            "prerequisite_components": ["python", "data preprocessing"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "K-Means alternates between assigning points to the nearest cluster centroid (Voronoi partitioning) and recomputing centroids as the arithmetic mean of assigned points, minimizing inertia.",
            "distractor_explanations": {
                "Fit a maximum-margin linear separator between two pre-labeled classes": "Maximum-margin separation on labeled data is the supervised formulation of Support Vector Machines.",
                "Sequentially train weak decision stumps to minimize residual classification error": "Sequential weak learner training is Gradient Boosting or AdaBoost.",
                "Project high-dimensional features onto top orthogonal eigenvector axes": "Orthogonal eigenvector projection is Principal Component Analysis (PCA)."
            }
        },
        {
            "item_id": "q_clust_02",
            "q": "In hierarchical clustering, what graphical tree diagram visually depicts the sequence of cluster merges or splits across varying distance thresholds?",
            "question": "In hierarchical clustering, what graphical tree diagram visually depicts the sequence of cluster merges or splits across varying distance thresholds?",
            "options": [
                "Dendrogram",
                "ROC Curve",
                "Scree plot",
                "Confusion Matrix"
            ],
            "answer": "Dendrogram",
            "correct_answer": "Dendrogram",
            "knowledge_components": ["clustering"],
            "difficulty": 3,
            "prerequisite_components": ["python", "data preprocessing"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "A dendrogram illustrates the nested groupings of data points in agglomerative or divisive hierarchical clustering, where the vertical height of each fusion branch indicates the dissimilarity distance between merged clusters.",
            "distractor_explanations": {
                "ROC Curve": "A Receiver Operating Characteristic (ROC) curve plots True Positive Rate against False Positive Rate across classification thresholds.",
                "Scree plot": "A scree plot displays the eigenvalues or explained variance ratio of successive principal components in PCA.",
                "Confusion Matrix": "A confusion matrix tabulates True Positives, False Positives, True Negatives, and False Negatives for classification models."
            }
        },
    ],
    "dimensionality reduction": [
        {
            "item_id": "q_dimred_01",
            "q": "What is the primary geometric objective of Principal Component Analysis (PCA)?",
            "question": "What is the primary geometric objective of Principal Component Analysis (PCA)?",
            "options": [
                "Identify orthogonal projection axes (eigenvectors) that maximize the variance of projected data",
                "Maximize class separability by maximizing between-class scatter relative to within-class scatter",
                "Cluster data points into Voronoi cells around K moving centroids",
                "Train non-linear neural bottleneck representations to reconstruct corrupted inputs"
            ],
            "answer": "Identify orthogonal projection axes (eigenvectors) that maximize the variance of projected data",
            "correct_answer": "Identify orthogonal projection axes (eigenvectors) that maximize the variance of projected data",
            "knowledge_components": ["dimensionality reduction"],
            "difficulty": 3,
            "prerequisite_components": ["python", "data preprocessing", "classification"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "PCA performs eigendecomposition or singular value decomposition (SVD) on the centered covariance matrix, identifying mutually orthogonal principal directions that preserve maximum dataset variance.",
            "distractor_explanations": {
                "Maximize class separability by maximizing between-class scatter relative to within-class scatter": "Maximizing between-class relative to within-class scatter using class labels is Linear Discriminant Analysis (LDA).",
                "Cluster data points into Voronoi cells around K moving centroids": "Voronoi cell assignment around K centroids is K-Means clustering.",
                "Train non-linear neural bottleneck representations to reconstruct corrupted inputs": "Bottleneck reconstruction of corrupted inputs is an Autoencoder neural network."
            }
        },
        {
            "item_id": "q_dimred_02",
            "q": "Why is Linear Discriminant Analysis (LDA) classified as a supervised dimensionality reduction technique whereas PCA is unsupervised?",
            "question": "Why is Linear Discriminant Analysis (LDA) classified as a supervised dimensionality reduction technique whereas PCA is unsupervised?",
            "options": [
                "LDA utilizes known target class labels to maximize between-class separation relative to within-class spread",
                "LDA requires no class labels and strictly maximizes overall feature covariance",
                "PCA relies on cross-validation target labels to pick components",
                "LDA is restricted to regression target variables while PCA is for classification"
            ],
            "answer": "LDA utilizes known target class labels to maximize between-class separation relative to within-class spread",
            "correct_answer": "LDA utilizes known target class labels to maximize between-class separation relative to within-class spread",
            "knowledge_components": ["dimensionality reduction"],
            "difficulty": 3,
            "prerequisite_components": ["python", "data preprocessing", "classification"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "analysis",
            "question_type": "conceptual",
            "explanation": "LDA maximizes Fisher's criterion (S_B / S_W), requiring ground-truth class labels to calculate between-class scatter matrix S_B and within-class scatter matrix S_W.",
            "distractor_explanations": {
                "LDA requires no class labels and strictly maximizes overall feature covariance": "This describes PCA, which is unsupervised and ignores target labels entirely.",
                "PCA relies on cross-validation target labels to pick components": "PCA calculates eigenvectors solely from input feature matrix X, without any knowledge of target y.",
                "LDA is restricted to regression target variables while PCA is for classification": "LDA is explicitly a classification technique; its continuous equivalent is canonical correlation analysis."
            }
        },
    ],
    "naive bayes": [
        {
            "item_id": "q_nb_01",
            "q": "What is the defining 'naive' assumption made by Naive Bayes classifiers when calculating posterior class probabilities?",
            "question": "What is the defining 'naive' assumption made by Naive Bayes classifiers when calculating posterior class probabilities?",
            "options": [
                "All input features are conditionally independent given the class label",
                "All feature distributions are perfectly linear and have zero variance",
                "The prior probability of every class is always uniformly equal to 0.50",
                "The training dataset contains zero outliers or measurement noise"
            ],
            "answer": "All input features are conditionally independent given the class label",
            "correct_answer": "All input features are conditionally independent given the class label",
            "knowledge_components": ["naive bayes"],
            "difficulty": 2,
            "prerequisite_components": ["python", "classification"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Naive Bayes assumes P(x_1, x_2, ..., x_d | C_k) = prod(P(x_i | C_k)). Even when features exhibit real-world correlation, this independence assumption simplifies computation from exponential joint tables to linear product sums.",
            "distractor_explanations": {
                "All feature distributions are perfectly linear and have zero variance": "Naive Bayes allows continuous Gaussian, discrete Multinomial, or Bernoulli distributions with non-zero variance.",
                "The prior probability of every class is always uniformly equal to 0.50": "Priors P(C_k) are estimated from class frequencies in the training data, not arbitrarily set to 0.50.",
                "The training dataset contains zero outliers or measurement noise": "Naive Bayes does not assume noise-free data, although extreme zero frequencies require Laplace smoothing."
            }
        },
        {
            "item_id": "q_nb_02",
            "q": "Why is Laplace (additive) smoothing universally applied in Multinomial Naive Bayes text classification?",
            "question": "Why is Laplace (additive) smoothing universally applied in Multinomial Naive Bayes text classification?",
            "options": [
                "Prevent zero-frequency word counts from nullifying the entire joint posterior probability product to zero",
                "Scale word frequency term counts so their sum equals exactly 1.0",
                "Remove stop words and punctuation marks from raw text inputs",
                "Compute inverse document frequency weights across document collections"
            ],
            "answer": "Prevent zero-frequency word counts from nullifying the entire joint posterior probability product to zero",
            "correct_answer": "Prevent zero-frequency word counts from nullifying the entire joint posterior probability product to zero",
            "knowledge_components": ["naive bayes"],
            "difficulty": 3,
            "prerequisite_components": ["python", "classification"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "analysis",
            "question_type": "conceptual",
            "explanation": "If a word never appeared in a class during training, P(word|class) = 0. In a multiplicative probability chain, a single zero forces the entire joint likelihood P(document|class) to 0. Laplace smoothing adds alpha (typically 1) to all count numerators to prevent this catastrophic zero-probability collapse.",
            "distractor_explanations": {
                "Scale word frequency term counts so their sum equals exactly 1.0": "Normalizing counts to sum to 1.0 is standard frequency normalization, not additive Laplace smoothing.",
                "Remove stop words and punctuation marks from raw text inputs": "Removing stop words is text cleaning/preprocessing, not smoothing.",
                "Compute inverse document frequency weights across document collections": "Inverse document frequency is part of TF-IDF weighting, not smoothing."
            }
        },
    ],
    "neural networks": [
        {
            "item_id": "q_nn_01",
            "q": "What is the primary mathematical necessity of using non-linear activation functions (such as ReLU, GELU, or Sigmoid) between layers in deep neural networks?",
            "question": "What is the primary mathematical necessity of using non-linear activation functions (such as ReLU, GELU, or Sigmoid) between layers in deep neural networks?",
            "options": [
                "Enable the network to approximate complex non-linear functions; without them, stacked linear layers collapse into a single linear transformation",
                "Speed up matrix multiplications on GPU tensor cores",
                "Guarantee that all output activations sum to 1.0 across hidden neurons",
                "Prevent any weights from becoming negative during training"
            ],
            "answer": "Enable the network to approximate complex non-linear functions; without them, stacked linear layers collapse into a single linear transformation",
            "correct_answer": "Enable the network to approximate complex non-linear functions; without them, stacked linear layers collapse into a single linear transformation",
            "knowledge_components": ["neural networks"],
            "difficulty": 3,
            "prerequisite_components": ["python", "data preprocessing", "classification"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "A composition of linear functions W_2 * (W_1 * x + b_1) + b_2 is mathematically equivalent to a single linear transformation W' * x + b'. Non-linear activations introduce curvature, allowing deep networks to act as universal function approximators.",
            "distractor_explanations": {
                "Speed up matrix multiplications on GPU tensor cores": "Activation functions add elementwise computation steps; they do not accelerate GPU linear algebra.",
                "Guarantee that all output activations sum to 1.0 across hidden neurons": "Softmax at the output layer ensures outputs sum to 1.0, but hidden activations like ReLU have no such constraint.",
                "Prevent any weights from becoming negative during training": "Weights in neural networks are freely signed real numbers; activations operate on neuron pre-activations, not weights."
            }
        },
        {
            "item_id": "q_nn_02",
            "q": "How does the Adam optimizer improve over standard Stochastic Gradient Descent (SGD) with fixed learning rate?",
            "question": "How does the Adam optimizer improve over standard Stochastic Gradient Descent (SGD) with fixed learning rate?",
            "options": [
                "Combines adaptive learning rates per parameter (RMSprop) with exponential moving average of past gradients (Momentum)",
                "Calculates the exact second-order Hessian matrix inversion at each training step",
                "Evaluates all possible weight configurations using grid search at every epoch",
                "Eliminates the backpropagation step by solving weights via closed-form linear algebra"
            ],
            "answer": "Combines adaptive learning rates per parameter (RMSprop) with exponential moving average of past gradients (Momentum)",
            "correct_answer": "Combines adaptive learning rates per parameter (RMSprop) with exponential moving average of past gradients (Momentum)",
            "knowledge_components": ["neural networks"],
            "difficulty": 3,
            "prerequisite_components": ["python", "data preprocessing", "classification"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Adam (Adaptive Moment Estimation) tracks both the first moment m_t (exponential moving average of gradients) to maintain velocity and the second moment v_t (exponential moving average of squared gradients) to scale learning rates individually for each parameter.",
            "distractor_explanations": {
                "Calculates the exact second-order Hessian matrix inversion at each training step": "Exact Hessian inversion (Newton's method) has O(p^3) computational cost, which is intractable for modern neural networks with millions of parameters.",
                "Evaluates all possible weight configurations using grid search at every epoch": "Grid search over continuous high-dimensional parameter spaces is impossible.",
                "Eliminates the backpropagation step by solving weights via closed-form linear algebra": "Deep non-linear neural networks have non-convex loss surfaces that cannot be solved via closed-form equations."
            }
        },
    ],
    "automl": [
        {
            "item_id": "q_automl_01",
            "q": "What core problem in machine learning engineering does Automated Machine Learning (AutoML) systematically address?",
            "question": "What core problem in machine learning engineering does Automated Machine Learning (AutoML) systematically address?",
            "options": [
                "Automating model architecture selection, feature transformation pipelines, and hyperparameter optimization under resource constraints",
                "Replacing the need for ground-truth data collection and labeling entirely",
                "Guaranteeing 100% test accuracy on any arbitrary real-world dataset",
                "Translating Python machine learning code into hardware circuit schematics"
            ],
            "answer": "Automating model architecture selection, feature transformation pipelines, and hyperparameter optimization under resource constraints",
            "correct_answer": "Automating model architecture selection, feature transformation pipelines, and hyperparameter optimization under resource constraints",
            "knowledge_components": ["automl"],
            "difficulty": 2,
            "prerequisite_components": ["python", "classification", "model evaluation"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "AutoML addresses the Combined Algorithm Selection and Hyperparameter optimization (CASH) problem, testing candidate algorithms and preprocessing pipelines via search strategies (e.g. Bayesian optimization, genetic algorithms) to find high-performing configurations.",
            "distractor_explanations": {
                "Replacing the need for ground-truth data collection and labeling entirely": "AutoML requires labeled training data to optimize and evaluate candidate models.",
                "Guaranteeing 100% test accuracy on any arbitrary real-world dataset": "No ML algorithm can guarantee 100% accuracy due to Bayes error, irreducible noise, and sample variance.",
                "Translating Python machine learning code into hardware circuit schematics": "Compiling code to hardware circuits (HLS/FPGA) is high-level synthesis, not AutoML."
            }
        },
        {
            "item_id": "q_automl_02",
            "q": "In gradient boosting algorithms (such as XGBoost, LightGBM, and CatBoost), how are successive decision trees trained?",
            "question": "In gradient boosting algorithms (such as XGBoost, LightGBM, and CatBoost), how are successive decision trees trained?",
            "options": [
                "Sequentially, where each new tree fits the pseudo-residuals (negative gradient of the loss) of the ensemble so far",
                "Independently in parallel on bootstrap samples with random feature subsets (Bagging)",
                "By running genetic mutations on the root split criterion of a single tree",
                "By clustering data points into K leaf clusters using unsupervised distance metrics"
            ],
            "answer": "Sequentially, where each new tree fits the pseudo-residuals (negative gradient of the loss) of the ensemble so far",
            "correct_answer": "Sequentially, where each new tree fits the pseudo-residuals (negative gradient of the loss) of the ensemble so far",
            "knowledge_components": ["automl"],
            "difficulty": 3,
            "prerequisite_components": ["python", "classification", "model evaluation"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Gradient boosting builds an additive model sequentially: each new tree h_m(x) is fit to the negative gradient of the loss function with respect to the current ensemble prediction F_{m-1}(x), systematically correcting remaining errors.",
            "distractor_explanations": {
                "Independently in parallel on bootstrap samples with random feature subsets (Bagging)": "Training independent trees in parallel on bootstrap samples is the formulation of Random Forests (Bagging), not Gradient Boosting.",
                "By running genetic mutations on the root split criterion of a single tree": "Evolutionary search is a meta-heuristic, not the standard mathematical formulation of gradient boosting.",
                "By clustering data points into K leaf clusters using unsupervised distance metrics": "Clustering partitions unlabeled data, whereas boosting minimizes supervised differentiable loss functions."
            }
        },
    ],
}

# 2. Next 12 topics: ADDITIONAL_QUIZ_QUESTIONS
UPGRADED_ADDITIONAL_QUIZ_QUESTIONS = {
    "statistics": [
        {
            "item_id": "q_stat_01",
            "q": "Which summary statistic represents the central tendency of a dataset, computed as the sum of all observations divided by sample size N?",
            "question": "Which summary statistic represents the central tendency of a dataset, computed as the sum of all observations divided by sample size N?",
            "options": ["Arithmetic Mean", "Sample Variance", "Shannon Entropy", "Interquartile Range"],
            "answer": "Arithmetic Mean",
            "correct_answer": "Arithmetic Mean",
            "knowledge_components": ["statistics"],
            "difficulty": 1,
            "prerequisite_components": ["python"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "recall",
            "question_type": "conceptual",
            "explanation": "The arithmetic mean mu = (1/N) * sum(x_i) is the expected value of a finite sample, measuring the gravitational center of numerical observations.",
            "distractor_explanations": {
                "Sample Variance": "Variance measures the dispersion or spread of values around the mean, not central tendency.",
                "Shannon Entropy": "Entropy measures the information uncertainty or disorder in probability distributions.",
                "Interquartile Range": "The IQR is the difference between the 75th and 25th percentiles (Q3 - Q1), measuring dispersion."
            }
        },
        {
            "item_id": "q_stat_02",
            "q": "What does the sample standard deviation (sigma) quantify about a dataset?",
            "question": "What does the sample standard deviation (sigma) quantify about a dataset?",
            "options": [
                "The typical dispersion or spread of observations around the sample mean in original measurement units",
                "The probability that a new query sample belongs to the positive class",
                "The total number of unique discrete category labels in the dataset",
                "The rate of convergence of gradient descent backpropagation"
            ],
            "answer": "The typical dispersion or spread of observations around the sample mean in original measurement units",
            "correct_answer": "The typical dispersion or spread of observations around the sample mean in original measurement units",
            "knowledge_components": ["statistics"],
            "difficulty": 2,
            "prerequisite_components": ["python"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Standard deviation sigma = sqrt((1/N) * sum((x_i - mu)^2)) is the square root of variance, returning dispersion to the same physical units as the original data.",
            "distractor_explanations": {
                "The probability that a new query sample belongs to the positive class": "Class probability is estimated via logistic regression or classification algorithms, not standard deviation.",
                "The total number of unique discrete category labels in the dataset": "Cardinality counts distinct unique categories, not continuous dispersion.",
                "The rate of convergence of gradient descent backpropagation": "Convergence rate depends on learning rate and condition number of the Hessian, not data standard deviation alone."
            }
        },
    ],
    "probability": [
        {
            "item_id": "q_prob_01",
            "q": "According to Kolmogorov's probability axioms, what bounded interval must any valid probability P(E) lie within?",
            "question": "According to Kolmogorov's probability axioms, what bounded interval must any valid probability P(E) lie within?",
            "options": ["Between 0.0 and 1.0 inclusive [0, 1]", "Between -1.0 and +1.0 inclusive [-1, 1]", "Between 1.0 and 100.0 inclusive [1, 100]", "Any real number in (-infinity, +infinity)"],
            "answer": "Between 0.0 and 1.0 inclusive [0, 1]",
            "correct_answer": "Between 0.0 and 1.0 inclusive [0, 1]",
            "knowledge_components": ["probability"],
            "difficulty": 1,
            "prerequisite_components": ["statistics"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "recall",
            "question_type": "conceptual",
            "explanation": "By Kolmogorov's first axiom of non-negativity and second axiom of unit measure, the probability of any event E satisfies 0 <= P(E) <= 1, with P(sample space) = 1.0.",
            "distractor_explanations": {
                "Between -1.0 and +1.0 inclusive [-1, 1]": "Pearson correlation coefficients lie in [-1, +1], but probabilities cannot be negative.",
                "Between 1.0 and 100.0 inclusive [1, 100]": "Percentages are expressed in [0, 100], but mathematical probabilities are defined strictly on [0, 1].",
                "Any real number in (-infinity, +infinity)": "Log-odds (logits) span (-inf, +inf), but probabilities must be normalized to [0, 1]."
            }
        },
        {
            "item_id": "q_prob_02",
            "q": "How does Bayes' Theorem update our prior belief P(A) after observing new evidence B?",
            "question": "How does Bayes' Theorem update our prior belief P(A) after observing new evidence B?",
            "options": [
                "P(A|B) = [P(B|A) * P(A)] / P(B)",
                "P(A|B) = P(A) + P(B) - P(A and B)",
                "P(A|B) = P(A) * P(B)",
                "P(A|B) = [P(A) + P(B)] / 2"
            ],
            "answer": "P(A|B) = [P(B|A) * P(A)] / P(B)",
            "correct_answer": "P(A|B) = [P(B|A) * P(A)] / P(B)",
            "knowledge_components": ["probability"],
            "difficulty": 3,
            "prerequisite_components": ["statistics"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "application",
            "question_type": "calculation",
            "explanation": "Bayes' Theorem states that Posterior = (Likelihood * Prior) / Marginal Evidence: P(A|B) = P(B|A) * P(A) / P(B).",
            "distractor_explanations": {
                "P(A|B) = P(A) + P(B) - P(A and B)": "This is the addition rule for the union of two events P(A or B), not conditional probability.",
                "P(A|B) = P(A) * P(B)": "This is the multiplication rule for joint probability P(A and B) strictly when A and B are independent.",
                "P(A|B) = [P(A) + P(B)] / 2": "This is a simple arithmetic average, not conditional Bayesian updating."
            }
        },
    ],
    "feature engineering": [
        {
            "item_id": "q_fe_01",
            "q": "When preparing nominal categorical features without intrinsic ordering (e.g., country names) for linear models, which encoding prevents imposing false ordinal relationships?",
            "question": "When preparing nominal categorical features without intrinsic ordering (e.g., country names) for linear models, which encoding prevents imposing false ordinal relationships?",
            "options": [
                "One-hot encoding (creating binary dummy columns for each category)",
                "Label encoding (assigning arbitrary sequential integers 0, 1, 2, ...)",
                "MinMax scaling to the interval [0, 1]",
                "Logarithmic power transformation"
            ],
            "answer": "One-hot encoding (creating binary dummy columns for each category)",
            "correct_answer": "One-hot encoding (creating binary dummy columns for each category)",
            "knowledge_components": ["feature engineering"],
            "difficulty": 2,
            "prerequisite_components": ["python", "data preprocessing", "statistics"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "One-hot encoding creates K binary columns with values in {0, 1}. Label encoding assigns integers (e.g., USA=0, Canada=1, UK=2), misleading linear models into assuming Canada is mathematically between USA and UK.",
            "distractor_explanations": {
                "Label encoding (assigning arbitrary sequential integers 0, 1, 2, ...)": "Label encoding imposes a spurious numerical hierarchy on unordered nominal categories.",
                "MinMax scaling to the interval [0, 1]": "MinMax scaling requires continuous numeric inputs and cannot encode discrete text categories.",
                "Logarithmic power transformation": "Log transforms reduce positive skewness in continuous features, not categorical strings."
            }
        },
        {
            "item_id": "q_fe_02",
            "q": "How does systematic feature selection (e.g., Recursive Feature Elimination or LASSO penalty) benefit machine learning pipelines?",
            "question": "How does systematic feature selection (e.g., Recursive Feature Elimination or LASSO penalty) benefit machine learning pipelines?",
            "options": [
                "Reduces the curse of dimensionality, limits model variance, and speeds up inference",
                "Guarantees that training loss will reach zero on complex non-linear datasets",
                "Automatically creates deep polynomial interaction features between all columns",
                "Ensures that all missing values are imputed without data leakage"
            ],
            "answer": "Reduces the curse of dimensionality, limits model variance, and speeds up inference",
            "correct_answer": "Reduces the curse of dimensionality, limits model variance, and speeds up inference",
            "knowledge_components": ["feature engineering"],
            "difficulty": 2,
            "prerequisite_components": ["python", "data preprocessing", "statistics"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Eliminating uninformative or collinear features reduces model complexity, combats overfitting (variance), improves interpretability, and lowers storage and computation overhead.",
            "distractor_explanations": {
                "Guarantees that training loss will reach zero on complex non-linear datasets": "Reducing features can increase training bias slightly, preventing zero training loss.",
                "Automatically creates deep polynomial interaction features between all columns": "Feature expansion (PolynomialFeatures) creates combinations; feature selection does the opposite by removing unneeded features.",
                "Ensures that all missing values are imputed without data leakage": "Feature selection identifies valuable columns; missing value imputation is a separate preprocessing step."
            }
        },
    ],
    "model evaluation": [
        {
            "item_id": "q_modeval_01",
            "q": "In binary classification with imbalanced classes, how is Precision mathematically defined?",
            "question": "In binary classification with imbalanced classes, how is Precision mathematically defined?",
            "options": [
                "True Positives / (True Positives + False Positives)",
                "True Positives / (True Positives + False Negatives)",
                "(True Positives + True Negatives) / Total Samples",
                "True Negatives / (True Negatives + False Positives)"
            ],
            "answer": "True Positives / (True Positives + False Positives)",
            "correct_answer": "True Positives / (True Positives + False Positives)",
            "knowledge_components": ["model evaluation"],
            "difficulty": 3,
            "prerequisite_components": ["classification", "statistics"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Precision = TP / (TP + FP) measures exactness: out of all positive predictions made by the model, what fraction were truly positive?",
            "distractor_explanations": {
                "True Positives / (True Positives + False Negatives)": "This is Recall (Sensitivity), measuring completeness out of all actual real positives.",
                "(True Positives + True Negatives) / Total Samples": "This is Overall Accuracy, which can be severely misleading on imbalanced datasets.",
                "True Negatives / (True Negatives + False Positives)": "This is Specificity (True Negative Rate), measuring detection of actual negatives."
            }
        },
        {
            "item_id": "q_modeval_02",
            "q": "What is the primary motivation for using K-Fold Cross-Validation rather than a single train-test split?",
            "question": "What is the primary motivation for using K-Fold Cross-Validation rather than a single train-test split?",
            "options": [
                "Obtain an unbiased, lower-variance estimate of out-of-sample generalization performance across K distinct validation folds",
                "Ensure that training data and validation data have different column schemas",
                "Allow the model to memorize the test split to achieve higher reported validation scores",
                "Completely eliminate the need for hyperparameter tuning"
            ],
            "answer": "Obtain an unbiased, lower-variance estimate of out-of-sample generalization performance across K distinct validation folds",
            "correct_answer": "Obtain an unbiased, lower-variance estimate of out-of-sample generalization performance across K distinct validation folds",
            "knowledge_components": ["model evaluation"],
            "difficulty": 3,
            "prerequisite_components": ["classification", "statistics"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "K-fold cross-validation evaluates the model across K separate non-overlapping validation partitions, averaging performance to guard against high-variance splits or lucky test sets.",
            "distractor_explanations": {
                "Ensure that training data and validation data have different column schemas": "Training and validation splits must strictly share identical column schemas.",
                "Allow the model to memorize the test split to achieve higher reported validation scores": "Testing on memorized data is data snooping / overfitting, defeating validation entirely.",
                "Completely eliminate the need for hyperparameter tuning": "Cross-validation is used precisely to evaluate hyperparameters, not eliminate them."
            }
        },
    ],
    "computer vision": [
        {
            "item_id": "q_cv_01",
            "q": "In digital image processing with OpenCV, how are standard color images typically represented in memory?",
            "question": "In digital image processing with OpenCV, how are standard color images typically represented in memory?",
            "options": [
                "As 3D NumPy arrays of shape (Height, Width, 3) in BGR color channel order",
                "As a single continuous 1D string of base64 ASCII characters",
                "As binary decision tree graphs storing pixel coordinates",
                "As 2D sparse adjacency matrices of color gradients"
            ],
            "answer": "As 3D NumPy arrays of shape (Height, Width, 3) in BGR color channel order",
            "correct_answer": "As 3D NumPy arrays of shape (Height, Width, 3) in BGR color channel order",
            "knowledge_components": ["computer vision"],
            "difficulty": 2,
            "prerequisite_components": ["python", "neural networks"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "recall",
            "question_type": "conceptual",
            "explanation": "OpenCV reads images into standard uint8 NumPy arrays of shape (height, width, channels), using Blue-Green-Red (BGR) channel ordering rather than RGB.",
            "distractor_explanations": {
                "As a single continuous 1D string of base64 ASCII characters": "Base64 strings are used for serialization and web transport, not direct pixel manipulation.",
                "As binary decision tree graphs storing pixel coordinates": "Images are raster grids of pixel intensities, not decision trees.",
                "As 2D sparse adjacency matrices of color gradients": "Standard images are dense multi-channel matrices, not sparse graphs."
            }
        },
        {
            "item_id": "q_cv_02",
            "q": "Why are Convolutional Neural Networks (CNNs) drastically more effective for image tasks than standard Fully Connected (MLP) networks?",
            "question": "Why are Convolutional Neural Networks (CNNs) drastically more effective for image tasks than standard Fully Connected (MLP) networks?",
            "options": [
                "Local receptive fields and spatial weight sharing provide translation equivariance and parameter efficiency",
                "CNNs do not use backpropagation or gradient descent during training",
                "Fully connected layers cannot accept 2D matrices as inputs under any circumstances",
                "Convolutional layers guarantee zero classification loss on test sets"
            ],
            "answer": "Local receptive fields and spatial weight sharing provide translation equivariance and parameter efficiency",
            "correct_answer": "Local receptive fields and spatial weight sharing provide translation equivariance and parameter efficiency",
            "knowledge_components": ["computer vision"],
            "difficulty": 3,
            "prerequisite_components": ["python", "neural networks"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "CNNs apply small convolutional filter kernels across the entire image. Reusing the same filter weights across all spatial locations reduces parameter counts from millions to thousands and captures translation-invariant visual features (edges, textures, shapes).",
            "distractor_explanations": {
                "CNNs do not use backpropagation or gradient descent during training": "CNNs are fully differentiable networks trained via backpropagation and gradient descent.",
                "Fully connected layers cannot accept 2D matrices as inputs under any circumstances": "Fully connected networks can accept flattened 2D images, but lose 2D spatial relationships and require impractically large weight matrices.",
                "Convolutional layers guarantee zero classification loss on test sets": "No neural architecture guarantees zero generalization loss."
            }
        },
    ],
    "nlp": [
        {
            "item_id": "q_nlp_01",
            "q": "What is the primary role of tokenization (e.g., Byte-Pair Encoding or WordPiece) in Natural Language Processing pipelines?",
            "question": "What is the primary role of tokenization (e.g., Byte-Pair Encoding or WordPiece) in Natural Language Processing pipelines?",
            "options": [
                "Segment raw character strings into discrete subword or word units mapped to vocabulary IDs",
                "Automatically translate English text into structured SQL queries",
                "Calculate semantic cosine similarity between whole paragraphs",
                "Compress text files using lossless Huffman coding"
            ],
            "answer": "Segment raw character strings into discrete subword or word units mapped to vocabulary IDs",
            "correct_answer": "Segment raw character strings into discrete subword or word units mapped to vocabulary IDs",
            "knowledge_components": ["nlp"],
            "difficulty": 2,
            "prerequisite_components": ["python", "neural networks"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Tokenization converts raw text strings into a sequence of discrete numerical token IDs from a fixed vocabulary, allowing neural models to look up continuous dense vector embeddings.",
            "distractor_explanations": {
                "Automatically translate English text into structured SQL queries": "Text-to-SQL is a specialized semantic parsing task, not basic tokenization.",
                "Calculate semantic cosine similarity between whole paragraphs": "Semantic similarity requires embedding models (e.g., sentence-transformers), not simple tokenization.",
                "Compress text files using lossless Huffman coding": "Huffman coding is binary data compression, not lexical NLP tokenization."
            }
        },
        {
            "item_id": "q_nlp_02",
            "q": "In text classification, what does sentiment analysis primarily predict?",
            "question": "In text classification, what does sentiment analysis primarily predict?",
            "options": [
                "The emotional polarity, attitude, or sentiment orientation (e.g., positive, neutral, negative) of text",
                "The exact grammatical parse tree of subordinate clauses",
                "The chronological publication timestamp of an article",
                "The audio phoneme frequencies of spoken words"
            ],
            "answer": "The emotional polarity, attitude, or sentiment orientation (e.g., positive, neutral, negative) of text",
            "correct_answer": "The emotional polarity, attitude, or sentiment orientation (e.g., positive, neutral, negative) of text",
            "knowledge_components": ["nlp"],
            "difficulty": 2,
            "prerequisite_components": ["python", "neural networks"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "recall",
            "question_type": "conceptual",
            "explanation": "Sentiment analysis is an NLP text classification task that determines whether the subjective opinion expressed in a passage is positive, negative, or neutral.",
            "distractor_explanations": {
                "The exact grammatical parse tree of subordinate clauses": "Generating hierarchical syntactic trees is constituency or dependency parsing.",
                "The chronological publication timestamp of an article": "Predicting publication timestamps is metadata extraction or document date detection.",
                "The audio phoneme frequencies of spoken words": "Analyzing phoneme frequencies is speech processing/acoustics, not text sentiment classification."
            }
        },
    ],
    "transformers": [
        {
            "item_id": "q_transf_01",
            "q": "What core mathematical mechanism allows Transformer architectures to model long-range token dependencies in parallel without recurrence?",
            "question": "What core mathematical mechanism allows Transformer architectures to model long-range token dependencies in parallel without recurrence?",
            "options": [
                "Scaled Dot-Product Self-Attention: Attention(Q, K, V) = softmax(Q * K^T / sqrt(d_k)) * V",
                "Bidirectional Long Short-Term Memory (LSTM) recurrence cells",
                "Dynamic time warping over discrete hidden Markov chains",
                "Greedy recursive decision tree thresholding"
            ],
            "answer": "Scaled Dot-Product Self-Attention: Attention(Q, K, V) = softmax(Q * K^T / sqrt(d_k)) * V",
            "correct_answer": "Scaled Dot-Product Self-Attention: Attention(Q, K, V) = softmax(Q * K^T / sqrt(d_k)) * V",
            "knowledge_components": ["transformers"],
            "difficulty": 4,
            "prerequisite_components": ["nlp", "neural networks"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Scaled dot-product attention computes pairwise similarity scores between query vectors Q and key vectors K, scaling by 1/sqrt(d_k) to prevent vanishing softmax gradients, and produces a weighted sum of value vectors V in parallel across all tokens.",
            "distractor_explanations": {
                "Bidirectional Long Short-Term Memory (LSTM) recurrence cells": "LSTMs process tokens sequentially step-by-step, creating sequential bottlenecks that Transformers replace.",
                "Dynamic time warping over discrete hidden Markov chains": "DTW and HMMs are classical speech alignment models, not neural self-attention.",
                "Greedy recursive decision tree thresholding": "Decision tree splitting is a rule-based supervised method, unrelated to neural self-attention."
            }
        },
        {
            "item_id": "q_transf_02",
            "q": "How does the pretraining architecture of BERT differ from GPT?",
            "question": "How does the pretraining architecture of BERT differ from GPT?",
            "options": [
                "BERT uses bidirectional encoder attention with masked language modeling (MLM), whereas GPT uses causal autoregressive decoder attention",
                "BERT is an autoregressive generative decoder while GPT is a non-generative encoder",
                "BERT does not use self-attention layers while GPT does",
                "BERT is trained strictly on images while GPT is trained on audio"
            ],
            "answer": "BERT uses bidirectional encoder attention with masked language modeling (MLM), whereas GPT uses causal autoregressive decoder attention",
            "correct_answer": "BERT uses bidirectional encoder attention with masked language modeling (MLM), whereas GPT uses causal autoregressive decoder attention",
            "knowledge_components": ["transformers"],
            "difficulty": 3,
            "prerequisite_components": ["nlp", "neural networks"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "analysis",
            "question_type": "conceptual",
            "explanation": "BERT (Bidirectional Encoder Representations from Transformers) attends to both left and right context tokens simultaneously to understand full sentence representations. GPT (Generative Pretrained Transformer) uses causal masking to predict the next token from left-to-right.",
            "distractor_explanations": {
                "BERT is an autoregressive generative decoder while GPT is a non-generative encoder": "The roles are reversed: GPT is the autoregressive decoder, and BERT is the non-autoregressive encoder.",
                "BERT does not use self-attention layers while GPT does": "Both BERT and GPT are built on self-attention; they differ in masking (bidirectional vs causal).",
                "BERT is trained strictly on images while GPT is trained on audio": "Both BERT and GPT are foundational text transformer architectures."
            }
        },
    ],
    "llm": [
        {
            "item_id": "q_llm_01",
            "q": "What does the acronym 'LLM' represent in modern artificial intelligence and machine learning research?",
            "question": "What does the acronym 'LLM' represent in modern artificial intelligence and machine learning research?",
            "options": [
                "Large Language Model",
                "Low Latency Memory",
                "Linear Logic Machine",
                "Local Learning Module"
            ],
            "answer": "Large Language Model",
            "correct_answer": "Large Language Model",
            "knowledge_components": ["llm"],
            "difficulty": 1,
            "prerequisite_components": ["transformers", "nlp"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "recall",
            "question_type": "conceptual",
            "explanation": "LLM stands for Large Language Model: deep neural networks (typically with billions of parameters) pretrained on vast textual corpora using self-supervised objectives.",
            "distractor_explanations": {
                "Low Latency Memory": "Hardware RAM and cache can be low-latency, but this is not the ML concept LLM.",
                "Linear Logic Machine": "A linear logic machine is a theoretical concept in formal logic, not a neural language model.",
                "Local Learning Module": "Local learning refers to non-centralized federated training, not LLMs."
            }
        },
        {
            "item_id": "q_llm_02",
            "q": "How does Retrieval-Augmented Generation (RAG) significantly mitigate hallucination and knowledge staleness in Large Language Models?",
            "question": "How does Retrieval-Augmented Generation (RAG) significantly mitigate hallucination and knowledge staleness in Large Language Models?",
            "options": [
                "Retrieves relevant verifiable documents from an external vector index and injects them into the prompt context before generation",
                "Permanently updates the frozen neural model weights at every inference query",
                "Replaces the transformer self-attention mechanism with a deterministic SQL parser",
                "Restricts the model vocabulary strictly to single-syllable dictionary words"
            ],
            "answer": "Retrieves relevant verifiable documents from an external vector index and injects them into the prompt context before generation",
            "correct_answer": "Retrieves relevant verifiable documents from an external vector index and injects them into the prompt context before generation",
            "knowledge_components": ["llm"],
            "difficulty": 3,
            "prerequisite_components": ["transformers", "nlp"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "RAG queries an external database or vector store with the user's question, fetches the most semantically relevant text passages, and concatenates them into the prompt. The LLM then generates its answer conditioned on this ground-truth retrieved evidence.",
            "distractor_explanations": {
                "Permanently updates the frozen neural model weights at every inference query": "RAG works in-context at inference time without modifying underlying model weights.",
                "Replaces the transformer self-attention mechanism with a deterministic SQL parser": "RAG works alongside Transformer generation; it does not replace the model architecture.",
                "Restricts the model vocabulary strictly to single-syllable dictionary words": "RAG preserves the full expressive vocabulary of the language model."
            }
        },
    ],
    "prompt engineering": [
        {
            "item_id": "q_prompt_01",
            "q": "In prompt engineering, what does 'few-shot in-context learning' specifically entail?",
            "question": "In prompt engineering, what does 'few-shot in-context learning' specifically entail?",
            "options": [
                "Providing a small set of input-output example demonstrations directly in the prompt context to guide model format and reasoning",
                "Fine-tuning the neural model weights on a few thousand gradient descent iterations",
                "Compressing the prompt text into an ultra-short single-word instruction",
                "Limiting the LLM API token generation budget to fewer than 5 tokens"
            ],
            "answer": "Providing a small set of input-output example demonstrations directly in the prompt context to guide model format and reasoning",
            "correct_answer": "Providing a small set of input-output example demonstrations directly in the prompt context to guide model format and reasoning",
            "knowledge_components": ["prompt engineering"],
            "difficulty": 2,
            "prerequisite_components": ["llm"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Few-shot prompting provides 2-5 exemplars of the desired task inside the context window. The model's attention mechanism conditions on these examples to infer the expected pattern without parameter updates.",
            "distractor_explanations": {
                "Fine-tuning the neural model weights on a few thousand gradient descent iterations": "Gradient descent training on dataset samples is fine-tuning, not in-context prompt engineering.",
                "Compressing the prompt text into an ultra-short single-word instruction": "Prompt brevity is concise instruction, not few-shot demonstration.",
                "Limiting the LLM API token generation budget to fewer than 5 tokens": "Constraining max_tokens sets generation limits, not pedagogical prompting."
            }
        },
        {
            "item_id": "q_prompt_02",
            "q": "Why does Chain-of-Thought (CoT) prompting ('Let's think step by step') substantially enhance reasoning accuracy on multi-step arithmetic and symbolic problems?",
            "question": "Why does Chain-of-Thought (CoT) prompting ('Let's think step by step') substantially enhance reasoning accuracy on multi-step arithmetic and symbolic problems?",
            "options": [
                "Allows the model to generate intermediate reasoning tokens, giving the transformer computational steps across multiple forward passes",
                "Doubles the hardware clock speed of the underlying inference GPU accelerators",
                "Guarantees that the final generated answer will never contain spelling errors",
                "Permanently corrects erroneous factual weights stored in the transformer feed-forward layers"
            ],
            "answer": "Allows the model to generate intermediate reasoning tokens, giving the transformer computational steps across multiple forward passes",
            "correct_answer": "Allows the model to generate intermediate reasoning tokens, giving the transformer computational steps across multiple forward passes",
            "knowledge_components": ["prompt engineering"],
            "difficulty": 2,
            "prerequisite_components": ["llm"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "analysis",
            "question_type": "conceptual",
            "explanation": "In autoregressive transformers, each token generation is a fixed amount of computation. By outputting intermediate thinking steps, the model breaks down the problem and attends to previous steps in subsequent tokens, significantly outperforming direct answer jumps.",
            "distractor_explanations": {
                "Doubles the hardware clock speed of the underlying inference GPU accelerators": "Prompt engineering has no effect on physical hardware clock speeds.",
                "Guarantees that the final generated answer will never contain spelling errors": "CoT improves semantic and logical reasoning, but provides no formal grammar guarantees.",
                "Permanently corrects erroneous factual weights stored in the transformer feed-forward layers": "Prompting does not alter frozen neural network weights."
            }
        },
    ],
    "generative ai": [
        {
            "item_id": "q_genai_01",
            "q": "What is the fundamental capability that distinguishes Generative AI models from traditional Discriminative AI models?",
            "question": "What is the fundamental capability that distinguishes Generative AI models from traditional Discriminative AI models?",
            "options": [
                "Modeling the joint data distribution P(X, Y) or P(X) to synthesize novel text, image, or audio content",
                "Restricting outputs strictly to binary zero-or-one class classifications",
                "Requiring all input features to be stored in relational SQL database tables",
                "Executing only deterministic mathematical rule engines without probability distributions"
            ],
            "answer": "Modeling the joint data distribution P(X, Y) or P(X) to synthesize novel text, image, or audio content",
            "correct_answer": "Modeling the joint data distribution P(X, Y) or P(X) to synthesize novel text, image, or audio content",
            "knowledge_components": ["generative ai"],
            "difficulty": 2,
            "prerequisite_components": ["llm", "neural networks"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Discriminative models learn decision boundaries to estimate conditional class probabilities P(Y|X). Generative models learn the underlying data distribution P(X) or joint distribution P(X, Y), allowing them to sample and generate plausible new content.",
            "distractor_explanations": {
                "Restricting outputs strictly to binary zero-or-one class classifications": "Binary decision making is discriminative classification, not generative synthesis.",
                "Requiring all input features to be stored in relational SQL database tables": "Generative models process unstructured multimodal data (text, pixels, audio, code).",
                "Executing only deterministic mathematical rule engines without probability distributions": "Generative models are fundamentally probabilistic and generative, not static deterministic rules."
            }
        },
        {
            "item_id": "q_genai_02",
            "q": "In modern AI research, what defines a 'Foundation Model' (such as GPT-4, Llama 3, or Gemini)?",
            "question": "In modern AI research, what defines a 'Foundation Model' (such as GPT-4, Llama 3, or Gemini)?",
            "options": [
                "A large-scale model pretrained on vast multimodal datasets that can be adapted to a broad spectrum of downstream tasks via prompting or fine-tuning",
                "A basic linear regression baseline trained on a single CSV table",
                "A proprietary database schema used exclusively for offline data storage",
                "A rule-based expert system hardcoded with manual if-then statements"
            ],
            "answer": "A large-scale model pretrained on vast multimodal datasets that can be adapted to a broad spectrum of downstream tasks via prompting or fine-tuning",
            "correct_answer": "A large-scale model pretrained on vast multimodal datasets that can be adapted to a broad spectrum of downstream tasks via prompting or fine-tuning",
            "knowledge_components": ["generative ai"],
            "difficulty": 3,
            "prerequisite_components": ["llm", "neural networks"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Foundation models are trained at scale on massive diverse datasets using self-supervised objectives, capturing generalized world knowledge that enables cross-domain transfer to specialized tasks.",
            "distractor_explanations": {
                "A basic linear regression baseline trained on a single CSV table": "Simple baselines are single-task statistical models, not foundation models.",
                "A proprietary database schema used exclusively for offline data storage": "Database schemas structure tables, not machine learning foundation models.",
                "A rule-based expert system hardcoded with manual if-then statements": "Expert systems rely on hand-crafted rules without foundation model self-supervised pretraining."
            }
        },
    ],
    "reinforcement learning": [
        {
            "item_id": "q_rl_01",
            "q": "In the standard Reinforcement Learning framework, how does an agent learn optimal decision policies over time?",
            "question": "In the standard Reinforcement Learning framework, how does an agent learn optimal decision policies over time?",
            "options": [
                "By interacting with an environment, taking actions, and receiving scalar numerical rewards to maximize cumulative discounted return",
                "By strictly minimizing mean squared error against static ground-truth human label columns",
                "By sorting unsupervised data points into hierarchical dendrogram clusters",
                "By evaluating deterministic SQL queries over relational database schemas"
            ],
            "answer": "By interacting with an environment, taking actions, and receiving scalar numerical rewards to maximize cumulative discounted return",
            "correct_answer": "By interacting with an environment, taking actions, and receiving scalar numerical rewards to maximize cumulative discounted return",
            "knowledge_components": ["reinforcement learning"],
            "difficulty": 2,
            "prerequisite_components": ["probability", "neural networks"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "An RL agent operates in a Markov Decision Process (MDP): observing state s, selecting action a, receiving scalar reward r, and transitioning to s', learning a policy pi*(s) that maximizes expected discounted return G_t = sum(gamma^k * r_{t+k+1}).",
            "distractor_explanations": {
                "By strictly minimizing mean squared error against static ground-truth human label columns": "Supervised learning minimizes loss against pre-existing static labels, whereas RL learns from active trial-and-error feedback.",
                "By sorting unsupervised data points into hierarchical dendrogram clusters": "Hierarchical clustering is unsupervised grouping without goals or reward signals.",
                "By evaluating deterministic SQL queries over relational database schemas": "Executing SQL queries is database querying, not reinforcement learning."
            }
        },
        {
            "item_id": "q_rl_02",
            "q": "What does Q-learning systematically compute and update via the Bellman optimality equation?",
            "question": "What does Q-learning systematically compute and update via the Bellman optimality equation?",
            "options": [
                "State-action values Q(s, a) representing expected cumulative discounted rewards: Q(s, a) <- Q(s, a) + alpha * [r + gamma * max_a' Q(s', a') - Q(s, a)]",
                "A deterministic table of static image pixel color values",
                "A sequence of prompt tokens for conversational language models",
                "A set of boolean feature flags for binary decision trees"
            ],
            "answer": "State-action values Q(s, a) representing expected cumulative discounted rewards: Q(s, a) <- Q(s, a) + alpha * [r + gamma * max_a' Q(s', a') - Q(s, a)]",
            "correct_answer": "State-action values Q(s, a) representing expected cumulative discounted rewards: Q(s, a) <- Q(s, a) + alpha * [r + gamma * max_a' Q(s', a') - Q(s, a)]",
            "knowledge_components": ["reinforcement learning"],
            "difficulty": 3,
            "prerequisite_components": ["probability", "neural networks"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Q-learning is an off-policy Temporal Difference algorithm that updates Q-values towards the target r + gamma * max_{a'} Q(s', a'), estimating the optimal value of taking action a in state s.",
            "distractor_explanations": {
                "A deterministic table of static image pixel color values": "Pixel intensity buffers are digital images, not Q-value functions.",
                "A sequence of prompt tokens for conversational language models": "Token sequences are language model completions, not action-value tables.",
                "A set of boolean feature flags for binary decision trees": "Decision tree node conditions are split criteria, not expected Bellman returns."
            }
        },
    ],
    "model deployment": [
        {
            "item_id": "q_deploy_01",
            "q": "What is the primary operational objective of model deployment (MLOps) in production machine learning?",
            "question": "What is the primary operational objective of model deployment (MLOps) in production machine learning?",
            "options": [
                "Packaging a trained model and hosting it as a reliable, scalable service that delivers predictions to end users or applications",
                "Deleting trained weights to free up disk storage after training concludes",
                "Running continuous hyperparameter grid searches indefinitely without serving inferences",
                "Converting tabular CSV datasets into printable PDF summaries"
            ],
            "answer": "Packaging a trained model and hosting it as a reliable, scalable service that delivers predictions to end users or applications",
            "correct_answer": "Packaging a trained model and hosting it as a reliable, scalable service that delivers predictions to end users or applications",
            "knowledge_components": ["model deployment"],
            "difficulty": 2,
            "prerequisite_components": ["model evaluation", "automl"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Model deployment transitions an ML model from experimental development to live production, providing endpoints (REST, gRPC), monitoring data drift, latency, and throughput.",
            "distractor_explanations": {
                "Deleting trained weights to free up disk storage after training concludes": "Trained weights are the core deliverable of machine learning and must be preserved.",
                "Running continuous hyperparameter grid searches indefinitely without serving inferences": "Endless tuning without serving predictions provides zero real-world utility.",
                "Converting tabular CSV datasets into printable PDF summaries": "Document reporting is presentation formatting, not model serving."
            }
        },
        {
            "item_id": "q_deploy_02",
            "q": "What is the primary purpose of a RESTful inference API endpoint (e.g. POST /predict) in deployed ML systems?",
            "question": "What is the primary purpose of a RESTful inference API endpoint (e.g. POST /predict) in deployed ML systems?",
            "options": [
                "Allow client applications to send input feature payloads over HTTP and receive real-time model predictions in JSON format",
                "Directly recompile the operating system kernel on the server host",
                "Provide a static CSS styling sheet for frontend web browsers",
                "Format database hard drive partitions during user authentication"
            ],
            "answer": "Allow client applications to send input feature payloads over HTTP and receive real-time model predictions in JSON format",
            "correct_answer": "Allow client applications to send input feature payloads over HTTP and receive real-time model predictions in JSON format",
            "knowledge_components": ["model deployment"],
            "difficulty": 2,
            "prerequisite_components": ["model evaluation", "automl"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "An inference endpoint decouples the client from model implementation: clients submit JSON payloads containing feature values, and the server computes and returns model predictions with low latency.",
            "distractor_explanations": {
                "Directly recompile the operating system kernel on the server host": "Kernel compilation is low-level OS management, completely unrelated to inference APIs.",
                "Provide a static CSS styling sheet for frontend web browsers": "Serving CSS is static asset delivery, not ML inference.",
                "Format database hard drive partitions during user authentication": "Drive formatting is disk maintenance and destructive."
            }
        },
    ],
}

# 3. Final 8 topics: MORE_QUIZ
UPGRADED_MORE_QUIZ = {
    "svm": [
        {
            "item_id": "q_svm_01",
            "q": "What is the primary geometric objective of a Support Vector Machine (SVM) classifier in linear or kernel space?",
            "question": "What is the primary geometric objective of a Support Vector Machine (SVM) classifier in linear or kernel space?",
            "options": [
                "Find an optimal decision hyperplane that maximizes the margin (perpendicular distance) between opposing classes",
                "Maximize the number of training iterations before gradient descent stops",
                "Calculate the maximum number of clusters using hierarchical dendrograms",
                "Train an ensemble of decision trees on random feature subsets"
            ],
            "answer": "Find an optimal decision hyperplane that maximizes the margin (perpendicular distance) between opposing classes",
            "correct_answer": "Find an optimal decision hyperplane that maximizes the margin (perpendicular distance) between opposing classes",
            "knowledge_components": ["svm"],
            "difficulty": 3,
            "prerequisite_components": ["machine learning basics", "linear algebra"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "SVM finds the maximum-margin hyperplane w^T*x + b = 0. The margin is 2 / ||w||, bounded by the closest data points known as support vectors, which maximizes generalization robustness.",
            "distractor_explanations": {
                "Maximize the number of training iterations before gradient descent stops": "Optimization aims to converge to the minimum loss as efficiently as possible, not maximize iterations.",
                "Calculate the maximum number of clusters using hierarchical dendrograms": "Dendrograms are used in hierarchical clustering, whereas SVM is a supervised classifier.",
                "Train an ensemble of decision trees on random feature subsets": "Training trees on random subsets is Random Forests, not Support Vector Machines."
            }
        }
    ],
    "ensemble methods": [
        {
            "item_id": "q_ens_01",
            "q": "How does Boosting fundamentally differ from Bagging in ensemble machine learning?",
            "question": "How does Boosting fundamentally differ from Bagging in ensemble machine learning?",
            "options": [
                "Boosting trains weak learners sequentially to correct mistakes of prior models; Bagging trains learners in parallel on independent bootstrap samples",
                "Boosting trains models in parallel to reduce variance, while Bagging trains models sequentially to reduce bias",
                "Boosting only works on linear regression models while Bagging only works on neural networks",
                "Bagging uses scalar weights to adjust gradient descent learning rates while Boosting does not"
            ],
            "answer": "Boosting trains weak learners sequentially to correct mistakes of prior models; Bagging trains learners in parallel on independent bootstrap samples",
            "correct_answer": "Boosting trains weak learners sequentially to correct mistakes of prior models; Bagging trains learners in parallel on independent bootstrap samples",
            "knowledge_components": ["ensemble methods"],
            "difficulty": 3,
            "prerequisite_components": ["machine learning basics", "decision trees"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "analysis",
            "question_type": "conceptual",
            "explanation": "Bagging (Bootstrap Aggregating) trains independent models in parallel on bootstrap samples to reduce model variance. Boosting trains models sequentially, where each new learner focuses on instances mispredicted by previous learners to reduce model bias.",
            "distractor_explanations": {
                "Boosting trains models in parallel to reduce variance, while Bagging trains models sequentially to reduce bias": "This states the exact opposite of the true mathematical definitions of Bagging and Boosting.",
                "Boosting only works on linear regression models while Bagging only works on neural networks": "Both Bagging and Boosting are general ensemble paradigms that commonly use decision trees (Random Forest, XGBoost).",
                "Bagging uses scalar weights to adjust gradient descent learning rates while Boosting does not": "Boosting uses weights or gradients to guide sequential training; Bagging averages unweighted parallel predictions."
            }
        }
    ],
    "hyperparameter tuning": [
        {
            "item_id": "q_tune_01",
            "q": "What is the primary mechanism of Grid Search (GridSearchCV) in model hyperparameter optimization?",
            "question": "What is the primary mechanism of Grid Search (GridSearchCV) in model hyperparameter optimization?",
            "options": [
                "Exhaustively evaluates model cross-validation performance across every Cartesian product combination of candidate parameters",
                "Sequentially updates Gaussian Process priors using expected improvement acquisition functions",
                "Applies genetic crossover and mutation operators to select optimal feature weights",
                "Calculates analytical closed-form parameter solutions using matrix inversion"
            ],
            "answer": "Exhaustively evaluates model cross-validation performance across every Cartesian product combination of candidate parameters",
            "correct_answer": "Exhaustively evaluates model cross-validation performance across every Cartesian product combination of candidate parameters",
            "knowledge_components": ["hyperparameter tuning"],
            "difficulty": 2,
            "prerequisite_components": ["machine learning basics"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Grid search takes explicit lists of candidate values for each hyperparameter and evaluates model performance across the complete Cartesian product grid via cross-validation.",
            "distractor_explanations": {
                "Sequentially updates Gaussian Process priors using expected improvement acquisition functions": "Updating Gaussian Process priors with acquisition functions is Bayesian Optimization (e.g. Optuna, Hyperopt).",
                "Applies genetic crossover and mutation operators to select optimal feature weights": "Genetic crossover and mutation is evolutionary optimization.",
                "Calculates analytical closed-form parameter solutions using matrix inversion": "Hyperparameters (like tree depth, learning rate, regularization C) cannot be solved via closed-form matrix equations."
            }
        }
    ],
    "search algorithms": [
        {
            "item_id": "q_search_01",
            "q": "In graph and tree search algorithms, how does Breadth-First Search (BFS) traverse state space?",
            "question": "In graph and tree search algorithms, how does Breadth-First Search (BFS) traverse state space?",
            "options": [
                "Explores all neighbor nodes at the current depth level before progressing to nodes at the next depth level using a FIFO queue",
                "Recursively explores as deep as possible along each branch before backtracking using a LIFO stack",
                "Evaluates an admissible heuristic h(n) to prioritize nodes with lowest estimated cost f(n) = g(n) + h(n)",
                "Samples nodes randomly according to a uniform probability distribution"
            ],
            "answer": "Explores all neighbor nodes at the current depth level before progressing to nodes at the next depth level using a FIFO queue",
            "correct_answer": "Explores all neighbor nodes at the current depth level before progressing to nodes at the next depth level using a FIFO queue",
            "knowledge_components": ["search algorithms"],
            "difficulty": 2,
            "prerequisite_components": ["data structures", "python"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "BFS uses a First-In-First-Out (FIFO) queue to visit all vertices at distance d before inspecting vertices at distance d+1, guaranteeing shortest path discovery in unweighted graphs.",
            "distractor_explanations": {
                "Recursively explores as deep as possible along each branch before backtracking using a LIFO stack": "This is Depth-First Search (DFS).",
                "Evaluates an admissible heuristic h(n) to prioritize nodes with lowest estimated cost f(n) = g(n) + h(n)": "This is A* Search using a priority queue.",
                "Samples nodes randomly according to a uniform probability distribution": "Random sampling is random walk search, not systematic BFS."
            }
        }
    ],
    "knowledge representation": [
        {
            "item_id": "q_kr_01",
            "q": "What is the primary role of Knowledge Representation (KR) in classical Artificial Intelligence?",
            "question": "What is the primary role of Knowledge Representation (KR) in classical Artificial Intelligence?",
            "options": [
                "Structuring real-world facts, rules, and semantic relationships into formal formats (ontologies, logic) that automated inference engines can reason over",
                "Compressing raster graphic files into web-friendly vector formats",
                "Allocating GPU compute threads across distributed tensor clusters",
                "Running gradient descent updates on deep convolutional filters"
            ],
            "answer": "Structuring real-world facts, rules, and semantic relationships into formal formats (ontologies, logic) that automated inference engines can reason over",
            "correct_answer": "Structuring real-world facts, rules, and semantic relationships into formal formats (ontologies, logic) that automated inference engines can reason over",
            "knowledge_components": ["knowledge representation"],
            "difficulty": 3,
            "prerequisite_components": ["artificial intelligence"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Knowledge representation formalizes knowledge using first-order logic, semantic networks, or ontologies so that automated reasoning systems can deduce new conclusions from established facts.",
            "distractor_explanations": {
                "Compressing raster graphic files into web-friendly vector formats": "Image compression is media processing, not AI knowledge representation.",
                "Allocating GPU compute threads across distributed tensor clusters": "Thread scheduling is systems engineering and hardware acceleration.",
                "Running gradient descent updates on deep convolutional filters": "Backpropagation is connectionist deep learning, not formal knowledge representation."
            }
        }
    ],
    "expert systems": [
        {
            "item_id": "q_expert_01",
            "q": "What are the two fundamental decoupled architectural components that constitute an Expert System?",
            "question": "What are the two fundamental decoupled architectural components that constitute an Expert System?",
            "options": [
                "A Knowledge Base containing domain facts and rules, and an Inference Engine that applies logical reasoning",
                "A Convolutional Encoder and a Deconvolutional Decoder",
                "A PostgreSQL relational database and an HTML web browser template",
                "A Random Forest classifier and an XGBoost ranker"
            ],
            "answer": "A Knowledge Base containing domain facts and rules, and an Inference Engine that applies logical reasoning",
            "correct_answer": "A Knowledge Base containing domain facts and rules, and an Inference Engine that applies logical reasoning",
            "knowledge_components": ["expert systems"],
            "difficulty": 2,
            "prerequisite_components": ["knowledge representation", "artificial intelligence"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Expert systems separate domain-specific knowledge (the Knowledge Base of IF-THEN rules and facts) from the general problem-solving mechanism (the Inference Engine, which executes forward or backward chaining).",
            "distractor_explanations": {
                "A Convolutional Encoder and a Deconvolutional Decoder": "Encoder-decoder pairs are deep neural networks (e.g. U-Net, autoencoders), not rule-based expert systems.",
                "A PostgreSQL relational database and an HTML web browser template": "Databases and HTML templates form standard web apps, not AI expert systems.",
                "A Random Forest classifier and an XGBoost ranker": "Random Forest and XGBoost are tree ensembles, not expert systems."
            }
        }
    ],
    "fuzzy logic": [
        {
            "item_id": "q_fuzzy_01",
            "q": "How does Fuzzy Logic fundamentally extend classical Boolean logic in AI decision systems?",
            "question": "How does Fuzzy Logic fundamentally extend classical Boolean logic in AI decision systems?",
            "options": [
                "Allows continuous truth values between 0.0 and 1.0 representing partial membership in sets, handling real-world vagueness and ambiguity",
                "Requires all variables to strictly evaluate to binary 0 (False) or 1 (True) only",
                "Replaces probability theory with deterministic integer arithmetic",
                "Guarantees that decisions can be made without any sensory input or data"
            ],
            "answer": "Allows continuous truth values between 0.0 and 1.0 representing partial membership in sets, handling real-world vagueness and ambiguity",
            "correct_answer": "Allows continuous truth values between 0.0 and 1.0 representing partial membership in sets, handling real-world vagueness and ambiguity",
            "knowledge_components": ["fuzzy logic"],
            "difficulty": 3,
            "prerequisite_components": ["statistics"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Classical logic is crisp (x in S or x not in S). Fuzzy logic uses membership functions mu_A(x) in [0, 1] to represent degrees of truth (e.g., 'temperature is moderately warm' = 0.72), making it ideal for human-like control systems.",
            "distractor_explanations": {
                "Requires all variables to strictly evaluate to binary 0 (False) or 1 (True) only": "This is classical binary Boolean logic, which fuzzy logic specifically generalizes.",
                "Replaces probability theory with deterministic integer arithmetic": "Fuzzy logic models degrees of truth/vagueness rather than likelihood of occurrence; it does not replace math with integer arithmetic.",
                "Guarantees that decisions can be made without any sensory input or data": "Fuzzy inference requires crisp inputs to fuzzify before evaluating fuzzy rule sets."
            }
        }
    ],
    "rag": [
        {
            "item_id": "q_rag_01",
            "q": "In a modern Retrieval-Augmented Generation (RAG) architecture, what is the role of dense vector embeddings and approximate nearest neighbor (ANN) search?",
            "question": "In a modern Retrieval-Augmented Generation (RAG) architecture, what is the role of dense vector embeddings and approximate nearest neighbor (ANN) search?",
            "options": [
                "Convert text chunks into semantic vector coordinates and retrieve the most contextually relevant passages using cosine similarity",
                "Compress text documents to reduce cloud storage billing costs",
                "Directly generate final conversational responses without passing prompts to an LLM",
                "Encrypt private user queries before transmitting them over SSL connections"
            ],
            "answer": "Convert text chunks into semantic vector coordinates and retrieve the most contextually relevant passages using cosine similarity",
            "correct_answer": "Convert text chunks into semantic vector coordinates and retrieve the most contextually relevant passages using cosine similarity",
            "knowledge_components": ["rag"],
            "difficulty": 3,
            "prerequisite_components": ["llm", "nlp", "prompt engineering"],
            "source": "autolearn_canonical_curated",
            "cognitive_level": "comprehension",
            "question_type": "conceptual",
            "explanation": "Embedding models map textual semantics to high-dimensional dense vectors. ANN search (e.g., HNSW in vector databases) retrieves the top-k chunks having highest cosine similarity with the query vector, providing grounded context for LLM generation.",
            "distractor_explanations": {
                "Compress text documents to reduce cloud storage billing costs": "Vector embeddings increase storage requirements because high-dimensional float vectors are stored alongside raw text chunks.",
                "Directly generate final conversational responses without passing prompts to an LLM": "Vector search retrieves relevant context chunks; the LLM is still required to synthesize the final natural language answer.",
                "Encrypt private user queries before transmitting them over SSL connections": "Embeddings represent semantic geometry for retrieval, not cryptographic data encryption."
            }
        }
    ],
}

if __name__ == "__main__":
    print(f"Loaded {len(UPGRADED_QUIZ_QUESTIONS)} topics in QUIZ_QUESTIONS")
    print(f"Loaded {len(UPGRADED_ADDITIONAL_QUIZ_QUESTIONS)} topics in ADDITIONAL_QUIZ_QUESTIONS")
    print(f"Loaded {len(UPGRADED_MORE_QUIZ)} topics in MORE_QUIZ")
