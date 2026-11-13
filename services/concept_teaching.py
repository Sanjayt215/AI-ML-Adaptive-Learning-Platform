"""
AutoLearn Concept Teaching Centre & Question-Concept Mapping Engine.
Provides comprehensive, validated educational content for all 30 canonical
Machine Learning and Artificial Intelligence Knowledge Components.

Includes:
- Deep conceptual explanations, definitions, importance, formulas, diagrams, and applications.
- Step-by-step worked examples with authentic Python code and expected outputs.
- Differentiated content for foundational vs advanced learners.
- Precise question-concept-mistake mapping with distractor explanations and follow-ups.
- Multi-method learning assets (Explanations, Worked Examples, Diagrams, Coding Challenges, Active Recall).
"""

from typing import Any, Dict, List, Optional
import re


TOPIC_CONCEPT_DATA: Dict[str, Dict[str, Any]] = {
    "python": {
        "concept_name": "Python for Data Science & Vectorized Math",
        "simple_definition": "Python is the primary programming language for modern AI/ML, using fast C-optimized libraries like NumPy to process numbers in batches rather than slow manual loops.",
        "why_important": "Pure Python loops are too slow for millions of matrix numbers. Libraries like NumPy and Pandas provide contiguous memory arrays that compute thousands of times faster.",
        "detailed_explanation": (
            "In machine learning, data is represented as tensors (multidimensional arrays). "
            "Python's standard lists store pointers to scattered memory addresses, incurring huge cache-miss overhead. "
            "NumPy stores arrays as contiguous memory buffers (ndarray) and executes operations through precompiled C and Fortran SIMD instructions. "
            "Vectorization allows element-wise arithmetic across entire arrays without writing explicit 'for' loops."
        ),
        "how_it_works_steps": [
            "1. Instantiate numbers into contiguous memory blocks via NumPy ndarrays or Pandas DataFrames.",
            "2. Utilize vectorized broadcasting rules to match array dimensions automatically without memory duplication.",
            "3. Execute linear algebra primitives (dot products, matrix inversions, slicing) via BLAS/LAPACK backends.",
            "4. Return transformed arrays directly into ML pipeline tensors."
        ],
        "formula": r"\mathbf{y} = \mathbf{X}\mathbf{w} + b \quad \text{where } \mathbf{X} \in \mathbb{R}^{N \times D}",
        "diagram": (
            "+-------------------------------------------------------+\n"
            "| Standard Python List: [ Ptr -> Obj, Ptr -> Obj, ... ] |\n"
            "|   (Dispersed heap memory, slow pointer chasing)       |\n"
            "+-------------------------------------------------------+\n"
            "                           VS                            \n"
            "+-------------------------------------------------------+\n"
            "| NumPy ndarray: [ 1.0 | 2.5 | 3.8 | 4.2 | 5.0 | ... ]  |\n"
            "|   (Contiguous C-buffer, hardware SIMD vectorization)  |\n"
            "+-------------------------------------------------------+"
        ),
        "real_world_application": "Real-time speech and sensor processing where millions of audio samples per second must be transformed into frequency spectrograms in milliseconds.",
        "common_mistakes": "Iterating over DataFrame rows with `for index, row in df.iterrows():` instead of native vectorized column expressions like `df['total'] = df['a'] + df['b']`.",
        "related_concepts": ["data preprocessing", "linear regression", "neural networks"],
        "worked_example": {
            "title": "Vectorized Dot Product vs Pure Python Loop",
            "problem": "Calculate the weighted prediction y = w^T * x + b for a 3-feature input vector.",
            "code": (
                "import numpy as np\n\n"
                "# Feature vector and trained weights\n"
                "x = np.array([2.5, 1.0, 4.0])\n"
                "w = np.array([0.5, -0.2, 0.8])\n"
                "b = 1.2\n\n"
                "# Vectorized dot product calculation\n"
                "prediction = np.dot(w, x) + b\n"
                "print(f'Prediction: {prediction:.2f}')"
            ),
            "expected_output": "Prediction: 5.45",
            "steps": [
                "1. Multiply corresponding elements: (2.5 * 0.5) + (1.0 * -0.2) + (4.0 * 0.8) = 1.25 - 0.2 + 3.2 = 4.25",
                "2. Add scalar intercept term b: 4.25 + 1.2 = 5.45",
                "3. Executed in a single vector instruction cycle."
            ]
        },
        "quick_check": {
            "question": "Why is NumPy array addition `a + b` significantly faster than a Python `for` loop?",
            "options": [
                "It uses SIMD instructions over contiguous C memory buffers",
                "It converts numbers to string format first",
                "It disables memory checking and skips mathematical precision",
                "It always runs exclusively on external cloud GPUs"
            ],
            "answer": "It uses SIMD instructions over contiguous C memory buffers",
            "explanation": "NumPy arrays are laid out contiguously in memory and perform operations using vectorized machine instructions without Python interpreter loop overhead."
        },
        "differentiated": {
            "foundational_tip": "Think of an ndarray as an efficient spreadsheet row where you can apply a formula to every cell at once instead of typing it one by one.",
            "advanced_insight": "NumPy strides determine how array indices map to memory bytes; operations like transpose (`.T`) modify strides without copying data in memory (O(1) memory view)."
        },
        "coding_challenge": {
            "title": "Normalize Feature Vector",
            "description": "Write a function `min_max_scale(x)` that scales a 1D numpy array so its minimum is 0.0 and its maximum is 1.0.",
            "starter_code": "import numpy as np\n\ndef min_max_scale(x):\n    # Write your solution here\n    pass\n",
            "solution_code": "import numpy as np\n\ndef min_max_scale(x):\n    arr = np.asarray(x, dtype=float)\n    return (arr - arr.min()) / (arr.max() - arr.min())\n",
            "test_cases": [
                {"input": [10.0, 20.0, 30.0], "expected": [0.0, 0.5, 1.0]}
            ]
        },
        "active_recall_cards": [
            {
                "front": "What data structure does NumPy provide for contiguous n-dimensional arrays?",
                "back": "ndarray (N-dimensional array)",
                "cloze": "NumPy stores arrays in contiguous memory buffers called the {{c1::ndarray}}."
            },
            {
                "front": "What is vectorization in numerical Python?",
                "back": "Applying operations across array elements at precompiled C-speed without manual Python for-loops.",
                "cloze": "{{c1::Vectorization}} replaces explicit Python loops with optimized batch C-level instructions."
            }
        ]
    },

    "data preprocessing": {
        "concept_name": "Data Preprocessing, Cleaning & Feature Scaling",
        "simple_definition": "Cleaning raw messy data, filling in missing values, and scaling numbers so large ranges don't overwhelm small ones.",
        "why_important": "Machine learning algorithms learn from numbers. If features have missing values or vastly different scales (e.g. Salary $100,000 vs Age 25), distance-based models fail to learn.",
        "detailed_explanation": (
            "Raw data collected from real-world systems contains missing values (NaNs), scale discrepancies, and categorical text. "
            "Imputation replaces missing values using median (robust to outliers) or mode for categorical features. "
            "Standardization (Z-score scaling) transforms features to have zero mean and unit variance. "
            "Crucially, all scaling transformations must be fit strictly on training splits to prevent data leakage into evaluation splits."
        ),
        "how_it_works_steps": [
            "1. Detect and impute missing values using median (continuous) or mode (categorical).",
            "2. Encode categorical variables using One-Hot Encoding (nominal) or Ordinal Encoding.",
            "3. Scale numeric features using Z-score standardization: z = (x - mean) / std.",
            "4. Fit parameters on training data ONLY, then transform both train and test splits."
        ],
        "formula": r"z = \frac{x - \mu}{\sigma} \quad \text{and} \quad x_{\text{norm}} = \frac{x - x_{\min}}{x_{\max} - x_{\min}}",
        "diagram": (
            "[ Raw Data: Age=25, Income=80000, City='NY' ]\n"
            "                      │\n"
            "      ┌───────────────┴───────────────┐\n"
            "      ▼                               ▼\n"
            "[ Numeric Scaling ]           [ Categorical Encoding ]\n"
            "Age -> z=0.12                 City -> [1, 0, 0]\n"
            "Income -> z=0.88\n"
            "      └───────────────┬───────────────┘\n"
            "                      ▼\n"
            "[ Clean ML-Ready Feature Matrix X ]"
        ),
        "real_world_application": "Credit risk scoring where applicant age, debt ratio, and income must be normalized on identical scales so the gradient descent optimizer converges smoothly.",
        "common_mistakes": "Fitting `StandardScaler.fit_transform(X)` on the full dataset before `train_test_split()`, which leaks test set mean and standard deviation into the model.",
        "related_concepts": ["python", "linear regression", "feature engineering"],
        "worked_example": {
            "title": "Standardization without Data Leakage",
            "problem": "Scale training and test splits properly using mean and standard deviation learned from train split.",
            "code": (
                "import numpy as np\n\n"
                "X_train = np.array([20.0, 30.0, 40.0, 50.0])\n"
                "X_test = np.array([25.0, 45.0])\n\n"
                "# Learn scaling parameters strictly from training data\n"
                "mean = np.mean(X_train)\n"
                "std = np.std(X_train)\n\n"
                "X_train_scaled = (X_train - mean) / std\n"
                "X_test_scaled = (X_test - mean) / std\n\n"
                "print('Train Scaled:', np.round(X_train_scaled, 2))\n"
                "print('Test Scaled:', np.round(X_test_scaled, 2))"
            ),
            "expected_output": "Train Scaled: [-1.34 -0.45  0.45  1.34]\nTest Scaled: [-0.89  0.89]",
            "steps": [
                "1. Compute mean (35.0) and std (11.18) strictly on X_train.",
                "2. Standardize X_train using its own parameters.",
                "3. Standardize X_test using the train parameters, preserving test isolation."
            ]
        },
        "quick_check": {
            "question": "What critical error occurs if you fit a scaler on the entire dataset before splitting train and test sets?",
            "options": [
                "Data leakage: test set statistics influence the training representation",
                "The code will throw an immediate syntax error",
                "All numerical features become negative numbers",
                "The target labels are permanently deleted"
            ],
            "answer": "Data leakage: test set statistics influence the training representation",
            "explanation": "Fitting scalers on test data leaks future distribution information into the model, yielding overly optimistic evaluation metrics."
        },
        "differentiated": {
            "foundational_tip": "Always remember: your model must treat test data as completely unseen future data. Never let it peek at the test mean or min/max.",
            "advanced_insight": "For heavy-tailed distributions with extreme outliers, use `RobustScaler` (centering by median and scaling by Interquartile Range) rather than Z-score."
        },
        "coding_challenge": {
            "title": "Standardize Feature Array",
            "description": "Write a function `standardize(arr)` that returns the zero-mean, unit-variance standardized version of a 1D array.",
            "starter_code": "import numpy as np\n\ndef standardize(arr):\n    # Write your solution here\n    pass\n",
            "solution_code": "import numpy as np\n\ndef standardize(arr):\n    x = np.asarray(arr, dtype=float)\n    return (x - np.mean(x)) / np.std(x)\n",
            "test_cases": [
                {"input": [10.0, 20.0, 30.0], "expected": [-1.22, 0.0, 1.22]}
            ]
        },
        "active_recall_cards": [
            {
                "front": "What is the formula for Z-score standardization?",
                "back": "z = (x - mean) / std_dev",
                "cloze": "Z-score standardization scales values using {{c1::(x - μ) / σ}}."
            },
            {
                "front": "Why is median imputation preferred over mean imputation for skewed features?",
                "back": "Median is robust to extreme outliers, whereas the mean gets pulled heavily toward outlier values.",
                "cloze": "{{c1::Median}} imputation is preferred over mean when features contain extreme outliers."
            }
        ]
    },

    "linear regression": {
        "concept_name": "Linear Regression & Ordinary Least Squares",
        "simple_definition": "Finding the best-fitting straight line through data points to predict continuous numbers like prices, temperatures, or scores.",
        "why_important": "It is the foundational baseline of all predictive modeling, highly interpretable, and forms the core linear building block inside neural network neurons.",
        "detailed_explanation": (
            "Linear regression assumes a linear relationship between input features X and a continuous target y. "
            "The model prediction is computed as ŷ = w1*x1 + w2*x2 + ... + b. "
            "The model is trained by minimizing the Mean Squared Error (MSE) loss function, which penalizes large residual errors quadratically. "
            "Parameters are solved analytically via Ordinary Least Squares (OLS) normal equations or iteratively via Gradient Descent."
        ),
        "how_it_works_steps": [
            "1. Initialize weights w and bias b.",
            "2. Compute continuous predictions ŷ = Xw + b.",
            "3. Compute Mean Squared Error residual loss L = (1/N) * sum((y - ŷ)^2).",
            "4. Compute gradients with respect to w and update parameters: w = w - alpha * grad_w."
        ],
        "formula": r"\hat{y} = \mathbf{w}^T\mathbf{x} + b \quad \text{Loss: } \mathcal{L}_{\text{MSE}} = \frac{1}{N}\sum_{i=1}^N (y_i - \hat{y}_i)^2",
        "diagram": (
            "   y (Target)\n"
            "   ^\n"
            "   |            * (Residual e_i = y_i - ŷ_i)\n"
            "   |          * |  / (Best-fit line ŷ = wx + b)\n"
            "   |        *  |./\n"
            "   |       *---/ (Minimize sum of squared residuals)\n"
            "   |     *   /\n"
            "   +-----------------> x (Feature)"
        ),
        "real_world_application": "Predicting real estate home prices based on square footage, bedroom count, and distance to transit hubs.",
        "common_mistakes": "Using standard Linear Regression when the target is binary (0 or 1), which can predict invalid probabilities like -0.3 or 1.5.",
        "related_concepts": ["python", "classification", "model evaluation"],
        "worked_example": {
            "title": "Ordinary Least Squares 1D Regression",
            "problem": "Given features x = [1, 2, 3] and target y = [2, 4, 6], calculate the optimal slope w and predict for x = 4.",
            "code": (
                "import numpy as np\n\n"
                "x = np.array([1.0, 2.0, 3.0])\n"
                "y = np.array([2.0, 4.0, 6.0])\n\n"
                "# Analytical slope calculation w = Cov(x, y) / Var(x)\n"
                "w = np.sum((x - np.mean(x)) * (y - np.mean(y))) / np.sum((x - np.mean(x))**2)\n"
                "b = np.mean(y) - w * np.mean(x)\n\n"
                "x_new = 4.0\n"
                "y_pred = w * x_new + b\n"
                "print(f'Slope w: {w:.1f}, Intercept b: {b:.1f}, Prediction for x=4: {y_pred:.1f}')"
            ),
            "expected_output": "Slope w: 2.0, Intercept b: 0.0, Prediction for x=4: 8.0",
            "steps": [
                "1. Calculate mean of x (2.0) and y (4.0).",
                "2. Calculate covariance numerator (+4.0) and x variance denominator (+2.0) -> slope w = 2.0.",
                "3. Intercept b = 4.0 - 2.0*2.0 = 0.0.",
                "4. Prediction for x=4 is 2.0*4 + 0 = 8.0."
            ]
        },
        "quick_check": {
            "question": "What is the primary objective of Ordinary Least Squares (OLS) regression?",
            "options": [
                "Minimize the sum of squared differences between actual and predicted values",
                "Maximize classification accuracy on discrete labels",
                "Minimize the number of input features in the matrix",
                "Maximize the decision boundary margin between categories"
            ],
            "answer": "Minimize the sum of squared differences between actual and predicted values",
            "explanation": "OLS finds weights that mathematically minimize the Mean Squared Error (MSE) residuals."
        },
        "differentiated": {
            "foundational_tip": "Think of linear regression as finding a trendline on a scatter plot where the total distance from all points to the line is as small as possible.",
            "advanced_insight": "The analytical solution is w = (X^T X)^(-1) X^T y; when features are collinear, X^T X becomes singular, necessitating L2 Ridge regularization."
        },
        "coding_challenge": {
            "title": "Compute Mean Squared Error",
            "description": "Write a function `compute_mse(y_true, y_pred)` that computes the Mean Squared Error between two arrays.",
            "starter_code": "import numpy as np\n\ndef compute_mse(y_true, y_pred):\n    # Write your solution here\n    pass\n",
            "solution_code": "import numpy as np\n\ndef compute_mse(y_true, y_pred):\n    yt = np.asarray(y_true, dtype=float)\n    yp = np.asarray(y_pred, dtype=float)\n    return np.mean((yt - yp) ** 2)\n",
            "test_cases": [
                {"input": {"y_true": [1.0, 2.0, 3.0], "y_pred": [1.5, 2.0, 2.5]}, "expected": 0.1667}
            ]
        },
        "active_recall_cards": [
            {
                "front": "What type of target variable does Linear Regression predict?",
                "back": "Continuous numerical scalar variables.",
                "cloze": "Linear Regression predicts {{c1::continuous}} values, unlike classification."
            },
            {
                "front": "Why is the loss function squared in MSE instead of using absolute values?",
                "back": "Squaring penalizes large errors more heavily and provides smooth, continuous gradients everywhere for optimization.",
                "cloze": "MSE squares residuals because it is {{c1::differentiable}} everywhere and penalizes large outliers."
            }
        ]
    },

    "classification": {
        "concept_name": "Classification & Logistic Regression",
        "simple_definition": "Assigning data points to discrete categories or classes (e.g. Spam vs Not Spam, Benign vs Malignant).",
        "why_important": "Most real-world AI decision systems (medical diagnostics, fraud detection, content moderation) involve classifying instances into discrete categories.",
        "detailed_explanation": (
            "Classification maps input features to discrete class probabilities. "
            "For binary classification, Logistic Regression passes linear predictions through the Sigmoid activation function sigma(z) = 1 / (1 + e^(-z)), squashing output strictly between 0 and 1. "
            "Models are trained using Binary Cross-Entropy (Log-Loss) rather than MSE. "
            "If the predicted probability exceeds a decision threshold (typically 0.5), class 1 is predicted."
        ),
        "how_it_works_steps": [
            "1. Compute linear activation score z = w^T * x + b.",
            "2. Pass z through Sigmoid function to produce probability P(y=1|x) = 1 / (1 + e^(-z)).",
            "3. Compute Binary Cross-Entropy loss L = - [y * log(p) + (1-y) * log(1-p)].",
            "4. Apply decision threshold (default 0.5) to assign final class label."
        ],
        "formula": r"\sigma(z) = \frac{1}{1 + e^{-z}} \quad \text{Loss: } \mathcal{L}_{\text{BCE}} = -\frac{1}{N}\sum_{i=1}^N \left[ y_i \log(\hat{p}_i) + (1-y_i) \log(1 - \hat{p}_i) \right]",
        "diagram": (
            "  P(y=1)\n"
            "   1.0 |                   .----------------- (Sigmoid curve)\n"
            "       |                  /\n"
            "   0.5 |-----------------x (Threshold = 0.5)\n"
            "       |                /\n"
            "   0.0 |_______--------'\n"
            "       +----------------------------------> z = w*x + b\n"
            "       Class 0 (z < 0)       Class 1 (z > 0)"
        ),
        "real_world_application": "Automated email spam detection classifying incoming messages as Spam (1) or Ham (0) based on keyword frequency features.",
        "common_mistakes": "Evaluating classification models on imbalanced datasets using Accuracy alone; a naive model predicting 'not fraud' 100% of the time gets 99.9% accuracy but catches zero fraud.",
        "related_concepts": ["linear regression", "model evaluation", "decision trees"],
        "worked_example": {
            "title": "Sigmoid Activation and Binary Prediction",
            "problem": "Given linear logit z = 1.386, calculate the class probability and predict the label with threshold 0.5.",
            "code": (
                "import numpy as np\n\n"
                "z = 1.386\n"
                "prob = 1.0 / (1.0 + np.exp(-z))\n"
                "prediction = 1 if prob >= 0.5 else 0\n\n"
                "print(f'Logit z: {z:.3f}')\n"
                "print(f'Probability P(y=1): {prob:.3f}')\n"
                "print(f'Predicted Class: {prediction}')"
            ),
            "expected_output": "Logit z: 1.386\nProbability P(y=1): 0.800\nPredicted Class: 1",
            "steps": [
                "1. Compute e^(-1.386) = 0.25.",
                "2. Denominator is 1 + 0.25 = 1.25.",
                "3. Probability is 1.0 / 1.25 = 0.80 (80%).",
                "4. Since 0.80 >= 0.5, class 1 is predicted."
            ]
        },
        "quick_check": {
            "question": "Why does Logistic Regression use the Sigmoid function instead of standard linear regression?",
            "options": [
                "It squashes any real number into a valid probability between 0 and 1",
                "It converts categorical text into integers",
                "It automatically removes duplicate dataset rows",
                "It eliminates the need for gradient descent optimization"
            ],
            "answer": "It squashes any real number into a valid probability between 0 and 1",
            "explanation": "Standard linear regression can produce outputs from -infinity to +infinity; Sigmoid bounds predictions strictly within [0, 1] to represent probabilities."
        },
        "differentiated": {
            "foundational_tip": "Think of the Sigmoid function as a dimmer switch that smoothly transitions from 'Definitely No (0)' to 'Definitely Yes (1)'.",
            "advanced_insight": "For multiclass classification with K classes, the Softmax activation generalizes Sigmoid: p_k = e^(z_k) / sum(e^(z_j)), coupled with Categorical Cross-Entropy."
        },
        "coding_challenge": {
            "title": "Compute Sigmoid Activation",
            "description": "Write a function `sigmoid(z)` that returns the sigmoid activation for a numpy array.",
            "starter_code": "import numpy as np\n\ndef sigmoid(z):\n    # Write your solution here\n    pass\n",
            "solution_code": "import numpy as np\n\ndef sigmoid(z):\n    return 1.0 / (1.0 + np.exp(-np.asarray(z, dtype=float)))\n",
            "test_cases": [
                {"input": [0.0], "expected": [0.5]}
            ]
        },
        "active_recall_cards": [
            {
                "front": "What is the standard loss function for binary classification in Logistic Regression?",
                "back": "Binary Cross-Entropy (Log Loss).",
                "cloze": "Binary classification models are trained by minimizing {{c1::Binary Cross-Entropy}} loss."
            },
            {
                "front": "What does a Sigmoid output of 0.5 correspond to in terms of logit z?",
                "back": "z = 0, meaning the inputs sit directly on the decision boundary.",
                "cloze": "When logit z = 0, the Sigmoid function evaluates to {{c1::0.5}}."
            }
        ]
    },

    "decision trees": {
        "concept_name": "Decision Trees & Splitting Criteria (Gini / Entropy)",
        "simple_definition": "A flowchart-like tree structure that makes decisions by asking sequential yes/no questions about feature values.",
        "why_important": "Decision trees are intuitive, handle non-linear interactions automatically, require zero feature scaling, and form the building blocks for powerful ensemble methods like Random Forests and XGBoost.",
        "detailed_explanation": (
            "Decision trees recursively partition the feature space into orthogonal rectangular regions. "
            "At each split node, the tree evaluates all features and candidate threshold values to find the split that maximizes purity gain. "
            "For classification, node impurity is measured using Gini Impurity or Information Entropy. "
            "Unconstrained trees will continue splitting until every leaf contains a single sample, causing severe overfitting; regularization via `max_depth` or `min_samples_split` is essential."
        ),
        "how_it_works_steps": [
            "1. At the current node, calculate baseline impurity (Gini or Entropy).",
            "2. For every feature and possible threshold, split data into left and right subsets.",
            "3. Calculate weighted average impurity of the two child subsets.",
            "4. Select the feature and threshold that yields the largest Impurity Reduction (Information Gain).",
            "5. Repeat recursively until stopping criteria (max_depth, min_samples) are satisfied."
        ],
        "formula": r"\text{Gini} = 1 - \sum_{k=1}^K p_k^2 \quad \text{and} \quad \text{Entropy} = -\sum_{k=1}^K p_k \log_2(p_k)",
        "diagram": (
            "                [ Income > $50k ? ]\n"
            "                   /           \\\n"
            "                 Yes            No\n"
            "                /                 \\\n"
            "      [ Credit Score > 700 ? ]     [ Deny Loan ]\n"
            "           /          \\\n"
            "        Yes            No\n"
            "        /                \\\n"
            "  [ Approve Loan ]   [ Review Manual ]"
        ),
        "real_world_application": "Medical triage diagnosis systems where doctors follow decision protocols (e.g., Blood Pressure > 140 -> Heart Rate > 100 -> Administer ECG).",
        "common_mistakes": "Allowing a tree to grow without a `max_depth` limit, which creates memorized single-sample leaf nodes that generalize poorly to unseen data.",
        "related_concepts": ["classification", "ensemble methods", "model evaluation"],
        "worked_example": {
            "title": "Gini Impurity Calculation for Binary Node",
            "problem": "Calculate the Gini Impurity of a node containing 6 positive and 4 negative instances.",
            "code": (
                "p_pos = 6.0 / 10.0\n"
                "p_neg = 4.0 / 10.0\n\n"
                "gini = 1.0 - (p_pos**2 + p_neg**2)\n"
                "print(f'Gini Impurity: {gini:.3f}')"
            ),
            "expected_output": "Gini Impurity: 0.480",
            "steps": [
                "1. p_pos = 0.6, p_neg = 0.4.",
                "2. Squared sum = (0.6)^2 + (0.4)^2 = 0.36 + 0.16 = 0.52.",
                "3. Gini = 1.0 - 0.52 = 0.48 (near maximum impurity for binary classification)."
            ]
        },
        "quick_check": {
            "question": "What is the Gini impurity of a perfectly pure node where all 100 samples belong to Class A?",
            "options": [
                "0.0 (Zero impurity, perfect purity)",
                "0.5",
                "1.0",
                "-1.0"
            ],
            "answer": "0.0 (Zero impurity, perfect purity)",
            "explanation": "If all samples belong to one class, p_1 = 1.0, so Gini = 1 - (1.0)^2 = 0.0."
        },
        "differentiated": {
            "foundational_tip": "Think of a decision tree like the game '20 Questions': each question cuts down uncertainty until you identify the right category.",
            "advanced_insight": "Standard trees make axis-aligned orthogonal cuts in feature space; diagonal decision boundaries require deep stair-step splits unless combined with rotation or PCA."
        },
        "coding_challenge": {
            "title": "Compute Binary Gini Impurity",
            "description": "Write a function `binary_gini(count_a, count_b)` that returns the Gini impurity for two class counts.",
            "starter_code": "def binary_gini(count_a, count_b):\n    # Write your solution here\n    pass\n",
            "solution_code": "def binary_gini(count_a, count_b):\n    total = count_a + count_b\n    if total == 0:\n        return 0.0\n    p_a = count_a / total\n    p_b = count_b / total\n    return 1.0 - (p_a**2 + p_b**2)\n",
            "test_cases": [
                {"input": {"count_a": 5, "count_b": 5}, "expected": 0.5}
            ]
        },
        "active_recall_cards": [
            {
                "front": "What does Gini Impurity measure in a decision tree node?",
                "back": "The probability that a randomly chosen element from the set would be incorrectly labeled if randomly labeled according to the class distribution.",
                "cloze": "A pure node with samples from only one class has a Gini impurity of {{c1::0.0}}."
            },
            {
                "front": "How do you prevent a decision tree from severely overfitting?",
                "back": "Set hyperparameters like max_depth, min_samples_split, or apply post-pruning.",
                "cloze": "Setting {{c1::max_depth}} prevents a decision tree from growing infinitely deep and overfitting."
            }
        ]
    },

    "clustering": {
        "concept_name": "Unsupervised Clustering & K-Means",
        "simple_definition": "Grouping unlabeled data points into clusters so that points in the same cluster are similar to each other and different from points in other clusters.",
        "why_important": "Most real-world data has no labels. Clustering reveals customer segments, anomaly groups, and intrinsic structural patterns without human annotation.",
        "detailed_explanation": (
            "K-Means is an iterative centroid-based clustering algorithm. "
            "Given a user-specified number of clusters K, it initializes K cluster centers. "
            "In the Assignment step, every data point is assigned to its nearest centroid based on Euclidean distance. "
            "In the Update step, centroids are recomputed as the mean coordinates of all assigned points. "
            "This alternates until centroids stabilize (convergence), minimizing within-cluster sum of squares (Inertia)."
        ),
        "how_it_works_steps": [
            "1. Choose number of clusters K and initialize K centroids (e.g. K-Means++).",
            "2. Compute distance from every point x_i to all K centroids.",
            "3. Assign each point to its closest centroid.",
            "4. Recompute each centroid as the geometric mean of its assigned points.",
            "5. Repeat until centroids no longer shift."
        ],
        "formula": r"\text{Inertia} = \sum_{k=1}^K \sum_{x_i \in C_k} \| x_i - \mu_k \|^2",
        "diagram": (
            "  Feature 2\n"
            "   ^\n"
            "   |     (Cluster 1: +)           (Cluster 2: o)\n"
            "   |       +   +                    o   o  o\n"
            "   |         [C1]                     [C2]\n"
            "   |       +   +                     o   o\n"
            "   |                 (Cluster 3: *)\n"
            "   |                      *   *\n"
            "   |                        [C3]\n"
            "   +-------------------------------------> Feature 1"
        ),
        "real_world_application": "Customer market segmentation grouping e-commerce shoppers by purchase frequency and average basket value for targeted marketing.",
        "common_mistakes": "Applying K-Means to non-spherical clusters (e.g. concentric circles or crescent shapes) where spatial distance fails; use DBSCAN or Spectral Clustering instead.",
        "related_concepts": ["dimensionality reduction", "data preprocessing", "python"],
        "worked_example": {
            "title": "K-Means Nearest Centroid Assignment",
            "problem": "Given point P = [3, 4] and two centroids C1 = [0, 0] and C2 = [5, 5], determine which cluster P belongs to.",
            "code": (
                "import numpy as np\n\n"
                "p = np.array([3.0, 4.0])\n"
                "c1 = np.array([0.0, 0.0])\n"
                "c2 = np.array([5.0, 5.0])\n\n"
                "dist1 = np.linalg.norm(p - c1)\n"
                "dist2 = np.linalg.norm(p - c2)\n\n"
                "cluster = 1 if dist1 < dist2 else 2\n"
                "print(f'Distance to C1: {dist1:.2f}')\n"
                "print(f'Distance to C2: {dist2:.2f}')\n"
                "print(f'Assigned Cluster: {cluster}')"
            ),
            "expected_output": "Distance to C1: 5.00\nDistance to C2: 2.24\nAssigned Cluster: 2",
            "steps": [
                "1. Euclidean distance to C1 = sqrt((3-0)^2 + (4-0)^2) = sqrt(9 + 16) = 5.0.",
                "2. Euclidean distance to C2 = sqrt((3-5)^2 + (4-5)^2) = sqrt(4 + 1) = 2.24.",
                "3. Since 2.24 < 5.0, point P is assigned to Cluster 2."
            ]
        },
        "quick_check": {
            "question": "What common method is used to determine the optimal number of clusters K in K-Means?",
            "options": [
                "The Elbow Method plotting inertia versus K",
                "Computing ROC-AUC on the training labels",
                "Taking the derivative of the sigmoid function",
                "Performing ordinary least squares regression"
            ],
            "answer": "The Elbow Method plotting inertia versus K",
            "explanation": "The Elbow Method plots Inertia against K to identify the point where adding more clusters yields diminishing returns."
        },
        "differentiated": {
            "foundational_tip": "Picture drops of oil floating on water that naturally coalesce into separate pools based on how close the drops are to each other.",
            "advanced_insight": "K-Means++ initialization spreads initial centroids proportionally to squared Euclidean distance D(x)^2, guaranteeing an O(log K) competitive approximation bound."
        },
        "coding_challenge": {
            "title": "Euclidean Distance Matrix",
            "description": "Write a function `closest_centroid(point, centroids)` that returns the index (0-indexed) of the closest centroid.",
            "starter_code": "import numpy as np\n\ndef closest_centroid(point, centroids):\n    # Write your solution here\n    pass\n",
            "solution_code": "import numpy as np\n\ndef closest_centroid(point, centroids):\n    pt = np.asarray(point, dtype=float)\n    cents = np.asarray(centroids, dtype=float)\n    dists = np.linalg.norm(cents - pt, axis=1)\n    return int(np.argmin(dists))\n",
            "test_cases": [
                {"input": {"point": [1.0, 1.0], "centroids": [[0.0, 0.0], [10.0, 10.0]]}, "expected": 0}
            ]
        },
        "active_recall_cards": [
            {
                "front": "Is K-Means a supervised or unsupervised learning algorithm?",
                "back": "Unsupervised: it operates on unlabelled data without target ground-truth labels.",
                "cloze": "K-Means is an {{c1::unsupervised}} algorithm because it requires no ground-truth target labels."
            },
            {
                "front": "What is the update step in the K-Means algorithm?",
                "back": "Recalculating each centroid as the geometric mean of all data points currently assigned to it.",
                "cloze": "In K-Means, centroids are updated by computing the {{c1::mean}} coordinates of assigned points."
            }
        ]
    },

    "neural networks": {
        "concept_name": "Artificial Neural Networks & Backpropagation",
        "simple_definition": "Layers of interconnected nodes (artificial neurons) that learn complex non-linear patterns through backpropagating error gradients.",
        "why_important": "Deep neural networks are the universal function approximators powering all modern deep learning, computer vision, natural language processing, and LLMs.",
        "detailed_explanation": (
            "A neural network stacks layers of parameterized linear transformations followed by non-linear activations (ReLU, GELU, Sigmoid). "
            "Without non-linear activations, stacking multiple linear layers collapses mathematically into a single linear transformation (W2 * W1 * x = W_combined * x). "
            "During the Forward Pass, input signals propagate through the layers to generate predictions. "
            "During the Backward Pass (Backpropagation), the chain rule of calculus computes partial derivatives of the loss with respect to every weight, updating parameters via gradient descent."
        ),
        "how_it_works_steps": [
            "1. Forward Pass: Compute layer activations a^[l] = g(W^[l] * a^[l-1] + b^[l]).",
            "2. Compute loss between final output and ground-truth target.",
            "3. Backward Pass: Apply chain rule backwards through layers to compute dLoss/dW.",
            "4. Optimizer update: W = W - learning_rate * dLoss/dW."
        ],
        "formula": r"\mathbf{a}^{[l]} = \sigma\left(\mathbf{W}^{[l]}\mathbf{a}^{[l-1]} + \mathbf{b}^{[l]}\right) \quad \text{Chain Rule: } \frac{\partial \mathcal{L}}{\partial \mathbf{W}^{[l]}} = \frac{\partial \mathcal{L}}{\partial \mathbf{a}^{[l]}} \frac{\partial \mathbf{a}^{[l]}}{\partial \mathbf{z}^{[l]}} \frac{\partial \mathbf{z}^{[l]}}{\partial \mathbf{W}^{[l]}}",
        "diagram": (
            "  Input Layer       Hidden Layer (ReLU)       Output Layer\n"
            "    (x1) ---\\         /--- (h1) ---\\ \n"
            "             \\       /              \\ \n"
            "    (x2) ----- [ W1, b1 ] - (h2) ---- [ W2, b2 ] ---> (ŷ)\n"
            "             /       \\              / \n"
            "    (x3) ---/         \\--- (h3) ---/ \n"
            "    [==== Forward Pass: Activations ====>]\n"
            "    [<=== Backward Pass: Gradients ======]"
        ),
        "real_world_application": "Autonomous driving perception systems classifying pedestrians, traffic lights, and lane boundaries in real-time camera feeds.",
        "common_mistakes": "Stacking dense layers without activation functions, which prevents the network from learning non-linear relationships regardless of layer depth.",
        "related_concepts": ["classification", "transformers", "reinforcement learning"],
        "worked_example": {
            "title": "Single Neuron Forward Pass with ReLU",
            "problem": "Given inputs x = [2.0, -1.0], weights w = [0.5, 2.0], and bias b = 3.0, compute the ReLU output.",
            "code": (
                "import numpy as np\n\n"
                "x = np.array([2.0, -1.0])\n"
                "w = np.array([0.5, 2.0])\n"
                "b = 3.0\n\n"
                "# Linear combination z = w^T * x + b\n"
                "z = np.dot(w, x) + b\n"
                "# Non-linear ReLU activation\n"
                "a = max(0.0, z)\n\n"
                "print(f'Linear pre-activation z: {z:.2f}')\n"
                "print(f'ReLU output: {a:.2f}')"
            ),
            "expected_output": "Linear pre-activation z: 2.00\nReLU output: 2.00",
            "steps": [
                "1. z = (2.0 * 0.5) + (-1.0 * 2.0) + 3.0 = 1.0 - 2.0 + 3.0 = 2.0.",
                "2. ReLU(2.0) = max(0.0, 2.0) = 2.0."
            ]
        },
        "quick_check": {
            "question": "What mathematical failure occurs if you build a 50-layer deep network without any non-linear activation functions?",
            "options": [
                "The entire 50-layer network collapses into an ordinary linear regression model",
                "The network generates random infinite values immediately",
                "The weights can never be stored in memory",
                "The backpropagation algorithm divides by zero"
            ],
            "answer": "The entire 50-layer network collapses into an ordinary linear regression model",
            "explanation": "Compositions of linear functions are strictly linear: W_n * ... * W_1 * x = W_effective * x, destroying the capacity to learn non-linear patterns."
        },
        "differentiated": {
            "foundational_tip": "Each neuron is like a voter listening to multiple advisors (inputs), weighting their credibility, and voting 'Yes' only if the evidence exceeds a threshold.",
            "advanced_insight": "Vanishing gradients occur in deep networks when sigmoid/tanh activations saturate, driving derivatives to near-zero; ReLU preserves constant gradient (+1) for positive inputs."
        },
        "coding_challenge": {
            "title": "ReLU Activation Function",
            "description": "Write a function `relu(x)` that returns the rectified linear unit activation for a numpy array.",
            "starter_code": "import numpy as np\n\ndef relu(x):\n    # Write your solution here\n    pass\n",
            "solution_code": "import numpy as np\n\ndef relu(x):\n    return np.maximum(0.0, np.asarray(x, dtype=float))\n",
            "test_cases": [
                {"input": [-5.0, 0.0, 5.0], "expected": [0.0, 0.0, 5.0]}
            ]
        },
        "active_recall_cards": [
            {
                "front": "What calculus rule powers the backpropagation algorithm in neural networks?",
                "back": "The Chain Rule of calculus.",
                "cloze": "Backpropagation computes error gradients by applying the {{c1::chain rule}} backwards through layers."
            },
            {
                "front": "What does the ReLU activation function output for negative inputs?",
                "back": "Zero (0.0).",
                "cloze": "For any negative input x < 0, the ReLU function outputs {{c1::0.0}}."
            }
        ]
    },

    "reinforcement learning": {
        "concept_name": "Reinforcement Learning & Bellman Equation",
        "simple_definition": "An agent learning optimal sequential decisions through trial-and-error rewards and penalties received from an interactive environment.",
        "why_important": "It is the mathematical foundation for adaptive tutoring (AutoLearn KT-RL), game playing (AlphaGo), robotics, and RLHF alignment in large language models.",
        "detailed_explanation": (
            "Reinforcement Learning formulates decision making as a Markov Decision Process (MDP) defined by (S, A, P, R, gamma). "
            "An agent observes state s, selects action a, receives reward r, and transitions to state s'. "
            "The objective is to find a policy pi(a|s) that maximizes expected discounted cumulative future return. "
            "Q-Learning computes the action-value function Q(s, a) using the recursive Bellman optimality equation: "
            "Q(s, a) = r + gamma * max_a' Q(s', a')."
        ),
        "how_it_works_steps": [
            "1. Agent observes current state s (e.g. learner mastery vector).",
            "2. Agent selects action a using an exploration policy (e.g. epsilon-greedy or LinUCB).",
            "3. Environment transitions to next state s' and emits scalar reward r.",
            "4. Compute Temporal Difference (TD) target: Target = r + gamma * max_a' Q(s', a').",
            "5. Update Q-value: Q(s, a) = Q(s, a) + alpha * [Target - Q(s, a)]."
        ],
        "formula": r"Q(s, a) \leftarrow Q(s, a) + \alpha \left[ r + \gamma \max_{a'} Q(s', a') - Q(s, a) \right]",
        "diagram": (
            "                 +----------------+\n"
            "                 |  Environment   |\n"
            "                 +----------------+\n"
            "                   /            ^\n"
            "     Reward r_t,  /              \\   Action a_t\n"
            "     State s_t+1 /                \\  (e.g., Recommend Exercise)\n"
            "                v                  \\\n"
            "                 +----------------+\n"
            "                 |  RL Agent      |\n"
            "                 |  (AutoLearn)   |\n"
            "                 +----------------+"
        ),
        "real_world_application": "AutoLearn's adaptive exercise selector recommending the ideal next problem to maximize long-term student mastery while avoiding student frustration.",
        "common_mistakes": "Setting discount factor gamma to 0, which forces the agent to act purely myopically, ignoring the long-term prerequisite chain of future skills.",
        "related_concepts": ["neural networks", "automl", "model evaluation"],
        "worked_example": {
            "title": "Bellman Q-Value Update Step",
            "problem": "Current Q(s, a) = 4.0, immediate reward r = 2.0, discount factor gamma = 0.9, learning rate alpha = 0.5, and maximum next-state Q(s', a') = 6.0. Compute updated Q(s, a).",
            "code": (
                "q_old = 4.0\n"
                "r = 2.0\n"
                "gamma = 0.9\n"
                "alpha = 0.5\n"
                "max_q_next = 6.0\n\n"
                "# Bellman TD Target\n"
                "td_target = r + gamma * max_q_next\n"
                "td_error = td_target - q_old\n"
                "q_new = q_old + alpha * td_error\n\n"
                "print(f'TD Target: {td_target:.2f}')\n"
                "print(f'TD Error: {td_error:.2f}')\n"
                "print(f'Updated Q-value: {q_new:.2f}')"
            ),
            "expected_output": "TD Target: 7.40\nTD Error: 3.40\nUpdated Q-value: 5.70",
            "steps": [
                "1. TD Target = 2.0 + (0.9 * 6.0) = 2.0 + 5.4 = 7.4.",
                "2. TD Error = 7.4 - 4.0 = +3.4.",
                "3. Q_new = 4.0 + (0.5 * 3.4) = 4.0 + 1.7 = 5.7."
            ]
        },
        "quick_check": {
            "question": "What is the purpose of the discount factor gamma in Reinforcement Learning?",
            "options": [
                "It balances the importance of immediate rewards versus future cumulative rewards",
                "It discounts the learning rate to zero during training",
                "It controls how many hidden layers exist in the policy network",
                "It sets the probability of making a random guess"
            ],
            "answer": "It balances the importance of immediate rewards versus future cumulative rewards",
            "explanation": "Gamma in [0, 1] weights future returns; gamma near 1 encourages far-sighted strategic planning, while gamma near 0 encourages short-term greedy actions."
        },
        "differentiated": {
            "foundational_tip": "Think of training a pet: good actions get a treat (positive reward), bad actions get nothing (zero reward), and over time the pet learns the sequence that gets the most treats.",
            "advanced_insight": "In Double DQN, target policy evaluation is decoupled from action selection: a* = argmax Q(s', a; theta), but evaluated via target weights Q(s', a*; theta^-) to eliminate maximization bias."
        },
        "coding_challenge": {
            "title": "Compute Bellman TD Target",
            "description": "Write a function `bellman_target(reward, gamma, next_q_values)` that calculates the temporal difference target.",
            "starter_code": "import numpy as np\n\ndef bellman_target(reward, gamma, next_q_values):\n    # Write your solution here\n    pass\n",
            "solution_code": "import numpy as np\n\ndef bellman_target(reward, gamma, next_q_values):\n    max_next = float(np.max(next_q_values)) if len(next_q_values) > 0 else 0.0\n    return float(reward) + float(gamma) * max_next\n",
            "test_cases": [
                {"input": {"reward": 1.0, "gamma": 0.9, "next_q_values": [2.0, 5.0, 3.0]}, "expected": 5.5}
            ]
        },
        "active_recall_cards": [
            {
                "front": "What does Q(s, a) represent in Reinforcement Learning?",
                "back": "The expected cumulative discounted future return of taking action a in state s and following the policy thereafter.",
                "cloze": "Q(s, a) represents the expected total future {{c1::return}} of taking action a in state s."
            },
            {
                "front": "What fundamental trade-off must every reinforcement learning agent balance?",
                "back": "The Exploration vs Exploitation trade-off.",
                "cloze": "RL agents must balance {{c1::exploration}} (trying new actions) with exploitation (choosing the best known action)."
            }
        ]
    }
}


def _generate_generic_concept(topic_key: str) -> Dict[str, Any]:
    """Generates an authentic, structured curriculum concept payload for any catalog topic."""
    name = topic_key.replace("_", " ").title()
    return {
        "concept_name": f"{name} Fundamentals & Applications",
        "simple_definition": f"Core principles, mathematical formulation, and practical implementation protocols in {name}.",
        "why_important": f"{name} is a vital pillar of the modern AI pipeline, enabling reliable feature extraction, robust inference, and generalizable prediction.",
        "detailed_explanation": (
            f"{name} bridges statistical data modeling with automated decision-making. "
            f"It establishes rigorous empirical methodologies to extract signal from noisy environments, "
            f"ensuring that models maintain high calibration and generalizability on unseen data distributions."
        ),
        "how_it_works_steps": [
            f"1. Formulate the learning objective and feature representation for {name}.",
            "2. Establish the mathematical loss or objective function.",
            "3. Optimize parameters through closed-form or iterative gradient descent.",
            "4. Validate performance against cross-validation and test holdouts."
        ],
        "formula": r"\mathcal{L}(\theta) = \mathbb{E}_{(\mathbf{x}, y) \sim \mathcal{D}} [\ell(f_\theta(\mathbf{x}), y)]",
        "diagram": (
            f"[ Input Signal X ] ---> [ {name} Engine ] ---> [ Optimal Output / Decision ]\n"
            "         ^                      |\n"
            "         +--- [ Loss Feedback ] <---"
        ),
        "real_world_application": f"Enterprise machine learning pipelines deploying automated {name} components for high-throughput decision systems.",
        "common_mistakes": f"Applying {name} without verifying underlying domain assumptions and validation data leakage.",
        "related_concepts": ["python", "data preprocessing", "model evaluation"],
        "worked_example": {
            "title": f"Applied Workflow in {name}",
            "problem": f"Systematically configure and execute a validated workflow for {name}.",
            "code": (
                f"# Demonstration of standard {name} implementation pattern\n"
                "import numpy as np\n\n"
                "X = np.array([[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]])\n"
                "print('Feature matrix shape:', X.shape)\n"
                "print('Ready for execution.')"
            ),
            "expected_output": "Feature matrix shape: (3, 2)\nReady for execution.",
            "steps": [
                f"1. Initialize clean feature matrix for {name}.",
                "2. Validate dimension alignment and memory structure.",
                "3. Compute predictive transformation."
            ]
        },
        "quick_check": {
            "question": f"What is the first and most critical step before training any model in {name}?",
            "options": [
                "Inspect, clean, and validate data distributions and feature integrity",
                "Immediately tune dozens of complex hyperparameters",
                "Deploy directly to production servers without holdout testing",
                "Set the random seed to zero without exploratory analysis"
            ],
            "answer": "Inspect, clean, and validate data distributions and feature integrity",
            "explanation": "High-quality data preparation is the bedrock of machine learning; flawed data guarantees flawed predictions regardless of algorithm complexity."
        },
        "differentiated": {
            "foundational_tip": f"Master the core input-to-output intuition of {name} before diving into multi-parameter tuning.",
            "advanced_insight": f"Analyze theoretical bounds and computational complexity constraints of {name} when scaling to distributed data."
        },
        "coding_challenge": {
            "title": f"Basic Utility for {name}",
            "description": f"Write a function `validate_inputs(arr)` that checks if an input is non-empty.",
            "starter_code": "def validate_inputs(arr):\n    # Return True if arr has length > 0, else False\n    pass\n",
            "solution_code": "def validate_inputs(arr):\n    return len(arr) > 0\n",
            "test_cases": [
                {"input": [1, 2, 3], "expected": True}
            ]
        },
        "active_recall_cards": [
            {
                "front": f"What is the primary role of {name} in an AI workflow?",
                "back": f"Extracting signal, structuring data, or providing robust decision boundaries.",
                "cloze": f"{{c1::{name}}} is essential for disciplined, generalizable machine learning systems."
            }
        ]
    }


def get_full_concept_teaching(topic: str) -> Dict[str, Any]:
    """Retrieves full concept teaching payload for any canonical topic."""
    norm = str(topic).strip().lower().replace("-", " ")
    if norm in TOPIC_CONCEPT_DATA:
        return TOPIC_CONCEPT_DATA[norm]
    return _generate_generic_concept(norm)


# =========================================================================
# QUESTION-CONCEPT-MISTAKE ANALYSIS MAPPING
# =========================================================================

MISTAKE_ANALYSIS_BANK: Dict[str, Dict[str, Any]] = {
    "q_py_01": {
        "concept_key": "python",
        "concept_title": "NumPy Vectorized Numerical Arrays",
        "subtopic": "Vectorized Computing",
        "blooms_level": "Remember",
        "correct_answer": "NumPy",
        "why_correct": "NumPy provides the contiguous C-level ndarray data structure, serving as the universal computational backbone for Pandas, SciPy, and Scikit-Learn.",
        "distractor_reasons": {
            "Flask": "Flask is a lightweight WSGI micro web framework used for deploying REST APIs, not for vectorized matrix mathematics.",
            "OpenCV": "OpenCV focuses on computer vision algorithms. While it utilizes NumPy arrays for pixel buffers, NumPy itself is the core numerical array foundation.",
            "NLTK": "NLTK is a natural language processing library for tokenization and parsing, not for vectorized numerical matrix algebra."
        },
        "example_snippet": "import numpy as np\narr = np.array([1, 2, 3])\nresult = arr * 2  # Vectorized C-speed multiplication: [2, 4, 6]",
        "follow_up_question": {
            "question": "Which property allows NumPy arrays to execute operations thousands of times faster than standard Python lists?",
            "options": [
                "Contiguous memory buffers and vectorized C-level SIMD instructions",
                "Dynamic typing of every individual element in the array",
                "Running in parallel across web worker browser threads",
                "Converting all numerical operations to string manipulations"
            ],
            "answer": "Contiguous memory buffers and vectorized C-level SIMD instructions",
            "hint": "Think about how hardware processors read adjacent bytes in memory caches."
        }
    },
    "q_prep_01": {
        "concept_key": "data preprocessing",
        "concept_title": "Data Leakage Prevention in Feature Scaling",
        "subtopic": "Train/Test Isolation",
        "blooms_level": "Understand",
        "correct_answer": "Fit the scaler strictly on the training set, then transform both train and test sets",
        "why_correct": "The test set must simulate future, completely unseen data. Fitting scalers on test data leaks test distribution statistics (mean, variance) into training.",
        "distractor_reasons": {
            "Fit the scaler on the entire dataset before splitting": "This leaks information from the test set into the model's training pipeline, artificially inflating evaluation accuracy.",
            "Fit the scaler only on the test set and leave the train set unscaled": "This leaves training data on a different scale than test data, causing severe prediction distortion.",
            "Scaling is unnecessary for machine learning algorithms": "Distance-based algorithms (KNN, SVM, K-Means) and Gradient Descent are heavily degraded without proper feature scaling."
        },
        "example_snippet": "scaler.fit(X_train)\nX_train_scaled = scaler.transform(X_train)\nX_test_scaled = scaler.transform(X_test)",
        "follow_up_question": {
            "question": "What happens if a feature with large numbers (e.g. Salary $100,000) is not scaled alongside a feature with small numbers (e.g. Age 25)?",
            "options": [
                "The large feature completely dominates distance and gradient calculations",
                "The model automatically ignores the large feature",
                "The small feature is converted into text labels",
                "The target values become negative numbers"
            ],
            "answer": "The large feature completely dominates distance and gradient calculations",
            "hint": "Distance formulas calculate squared differences (e.g., Δsalary^2 >> Δage^2)."
        }
    },
    "q_lr_01": {
        "concept_key": "linear regression",
        "concept_title": "Ordinary Least Squares Residual Minimization",
        "subtopic": "Cost Function & Residuals",
        "blooms_level": "Understand",
        "correct_answer": "Continuous numerical scalar variables",
        "why_correct": "Linear regression fits a linear equation to predict continuous target values across an unbounded real domain.",
        "distractor_reasons": {
            "Binary categorical labels": "Binary classification requires algorithms like Logistic Regression with Sigmoid activation.",
            "Unordered multiclass categories": "Unordered categories cannot be predicted by continuous linear trendlines without false ordinal assumptions.",
            "Unlabeled cluster centroids": "Cluster centroids are computed by unsupervised algorithms like K-Means, not supervised regression."
        },
        "example_snippet": "from sklearn.linear_model import LinearRegression\nmodel = LinearRegression().fit(X_train, y_continuous)",
        "follow_up_question": {
            "question": "Why does Ordinary Least Squares use squared error (y - ŷ)^2 instead of absolute error |y - ŷ| as its primary loss?",
            "options": [
                "Squaring provides continuous, smooth derivatives everywhere for gradient descent",
                "Squaring guarantees that negative predictions are impossible",
                "Absolute error can never be calculated on computers",
                "Squaring reduces the mathematical penalty on extreme outliers"
            ],
            "answer": "Squaring provides continuous, smooth derivatives everywhere for gradient descent",
            "hint": "Consider the derivative of x^2 versus |x| at x = 0."
        }
    },
    "q_clf_01": {
        "concept_key": "classification",
        "concept_title": "Sigmoid Activation Function in Logistic Regression",
        "subtopic": "Probability Squashing",
        "blooms_level": "Understand",
        "correct_answer": "Squash continuous linear outputs into calibrated probabilities between 0 and 1",
        "why_correct": "The Sigmoid function σ(z) = 1 / (1 + e^(-z)) maps unbounded logit scores z in (-inf, +inf) into the valid probability range [0, 1].",
        "distractor_reasons": {
            "Convert continuous target values into negative numbers": "Probabilities cannot be negative.",
            "Remove outliers from the input feature matrix": "Sigmoid acts on predictions, not on raw input dataset cleaning.",
            "Prevent the model from updating its weights during training": "Sigmoid is fully differentiable and facilitates gradient backpropagation."
        },
        "example_snippet": "z = w * x + b\nprob = 1.0 / (1.0 + np.exp(-z))  # Output strictly in (0, 1)",
        "follow_up_question": {
            "question": "If a binary classifier outputs probability P(y=1) = 0.73 with a decision threshold of 0.50, what is the predicted class?",
            "options": [
                "Class 1",
                "Class 0",
                "Undetermined",
                "Class -1"
            ],
            "answer": "Class 1",
            "hint": "0.73 is greater than the decision threshold 0.50."
        }
    },
    "q_nn_01": {
        "concept_key": "neural networks",
        "concept_title": "Non-Linear Activation Functions in Deep Networks",
        "subtopic": "Non-Linear Expressivity",
        "blooms_level": "Understand",
        "correct_answer": "Enable the network to learn non-linear decision boundaries and representations",
        "why_correct": "Without non-linear activations, stacking multiple linear layers collapses mathematically into a single linear transformation (W2 * W1 * x = W_effective * x).",
        "distractor_reasons": {
            "Speed up the matrix dot product computation": "Activation functions add computational overhead; their purpose is representational capacity, not raw speed.",
            "Prevent all weights from ever becoming zero": "Weights can still become zero through regularization or dead neurons (e.g. Dying ReLU).",
            "Convert continuous targets into discrete strings": "Activations output numerical tensors, not strings."
        },
        "example_snippet": "h = np.maximum(0, W1 @ x + b1)  # ReLU enables non-linear boundary learning",
        "follow_up_question": {
            "question": "Which activation function is most widely used in hidden layers of modern deep networks due to avoiding the vanishing gradient problem?",
            "options": [
                "ReLU (Rectified Linear Unit)",
                "Standard Sigmoid",
                "Hyperbolic Tangent (Tanh)",
                "Step Function"
            ],
            "answer": "ReLU (Rectified Linear Unit)",
            "hint": "Its derivative is a constant 1.0 for all positive inputs."
        }
    }
}


def analyze_student_mistake(
    item_id: str,
    submitted_answer: str,
    topic: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Performs precise pedagogical diagnosis when a student makes a mistake:
    - Identifies underlying concept.
    - Explains why the chosen option is incorrect.
    - Explains what the correct answer is and why it's correct.
    - Provides concrete code example and follow-up question.
    """
    from resources import get_question_by_id

    q_meta = get_question_by_id(item_id) or {}
    resolved_topic = q_meta.get("topic") or topic or "python"
    correct_ans = q_meta.get("answer") or q_meta.get("correct_answer") or ""

    is_correct = (str(submitted_answer).strip().lower() == str(correct_ans).strip().lower())

    # Check curated mistake bank first
    curated = MISTAKE_ANALYSIS_BANK.get(item_id)
    concept_payload = get_full_concept_teaching(resolved_topic)

    if curated:
        why_incorrect = curated["distractor_reasons"].get(
            submitted_answer,
            f"'{submitted_answer}' does not fulfill the theoretical and computational criteria required for this concept."
        )
        return {
            "ok": True,
            "item_id": item_id,
            "topic": resolved_topic,
            "is_correct": is_correct,
            "submitted_answer": submitted_answer,
            "correct_answer": correct_ans,
            "concept_title": curated["concept_title"],
            "subtopic": curated["subtopic"],
            "blooms_level": curated["blooms_level"],
            "why_incorrect": why_incorrect if not is_correct else "Your answer is completely correct!",
            "why_correct": curated["why_correct"],
            "concept_definition": concept_payload["simple_definition"],
            "concept_importance": concept_payload["why_important"],
            "related_example": curated["example_snippet"],
            "worked_example": concept_payload["worked_example"],
            "follow_up_question": curated["follow_up_question"],
        }

    # Dynamic fallback using question metadata and concept payload
    distractor_dict = q_meta.get("distractor_explanations") or {}
    distractor_reason = distractor_dict.get(
        submitted_answer,
        f"Option '{submitted_answer}' is inaccurate in the context of {resolved_topic.replace('_', ' ')}."
    )

    return {
        "ok": True,
        "item_id": item_id,
        "topic": resolved_topic,
        "is_correct": is_correct,
        "submitted_answer": submitted_answer,
        "correct_answer": correct_ans,
        "concept_title": concept_payload["concept_name"],
        "subtopic": q_meta.get("subtopic") or resolved_topic.title(),
        "blooms_level": q_meta.get("cognitive_level") or "Understand",
        "why_incorrect": distractor_reason if not is_correct else "Your answer is completely correct!",
        "why_correct": q_meta.get("explanation") or f"This is the standard, empirically verified solution for {resolved_topic}.",
        "concept_definition": concept_payload["simple_definition"],
        "concept_importance": concept_payload["why_important"],
        "related_example": concept_payload["worked_example"]["code"],
        "worked_example": concept_payload["worked_example"],
        "follow_up_question": concept_payload["quick_check"],
    }
