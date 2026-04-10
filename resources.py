from __future__ import annotations

TOPIC_CATALOG = {
    "python": {
        "aliases": ["python", "machine learning libraries in python", "ml libraries"],
        "prerequisites": [],
        "videos": {
            "beginner": [
                {"title": "Python for Beginners - Full Course", "channel": "freeCodeCamp.org", "url": "https://www.youtube.com/watch?v=rfscVS0vtbw"},
                {"title": "Python Tutorial for Beginners", "channel": "Programming with Mosh", "url": "https://www.youtube.com/watch?v=_uQrJ0TkZlc"},
            ],
            "intermediate": [
                {"title": "NumPy Full Course", "channel": "freeCodeCamp.org", "url": "https://www.youtube.com/watch?v=QUT1VHiLmmI"},
                {"title": "Pandas Full Course for Data Analysis", "channel": "freeCodeCamp.org", "url": "https://www.youtube.com/watch?v=vmEHCJofslg"},
            ],
            "advanced": [
                {"title": "Scikit-learn Crash Course", "channel": "Data School", "url": "https://www.youtube.com/watch?v=0B5eIE_1vpU"},
                {"title": "Machine Learning with Python", "channel": "freeCodeCamp.org", "url": "https://www.youtube.com/watch?v=7eh4d6sabA0"},
            ],
        },
        "courses": [
            {"title": "Python for Everybody", "provider": "Coursera", "url": "https://www.coursera.org/specializations/python", "certificate": True},
            {"title": "Introduction to Python Programming", "provider": "edX", "url": "https://www.edx.org/learn/python", "certificate": True},
            {"title": "The Complete Python Bootcamp", "provider": "Udemy", "url": "https://www.udemy.com/topic/python/", "certificate": True},
        ],
        "project": "Build a student marks analyzer using Python, Pandas, and Matplotlib.",
    },
    "data preprocessing": {
        "aliases": ["data exploration", "data preprocessing", "data cleaning", "pre-processing", "eda"],
        "prerequisites": ["python"],
        "videos": {
            "beginner": [
                {"title": "Data Analysis with Python Course", "channel": "freeCodeCamp.org", "url": "https://www.youtube.com/watch?v=r-uOLxNrNk8"},
                {"title": "Exploratory Data Analysis", "channel": "Krish Naik", "url": "https://www.youtube.com/watch?v=-o3AxdVcUtQ"},
            ],
            "intermediate": [
                {"title": "Feature Engineering and Data Cleaning", "channel": "Krish Naik", "url": "https://www.youtube.com/watch?v=0xVqLJe9_CY"},
                {"title": "Machine Learning Preprocessing Pipeline", "channel": "Data School", "url": "https://www.youtube.com/watch?v=0B5eIE_1vpU"},
            ],
            "advanced": [
                {"title": "End-to-End ML Preprocessing", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=lyDLAutA88s"},
                {"title": "Data Preparation for Machine Learning", "channel": "freeCodeCamp.org", "url": "https://www.youtube.com/watch?v=vmEHCJofslg"},
            ],
        },
        "courses": [
            {"title": "Data Analysis with Python", "provider": "IBM / Coursera", "url": "https://www.coursera.org/learn/data-analysis-with-python", "certificate": True},
            {"title": "Data Science: Machine Learning", "provider": "HarvardX / edX", "url": "https://www.edx.org/learn/machine-learning/harvard-university-data-science-machine-learning", "certificate": True},
        ],
        "project": "Clean a raw student performance CSV, handle missing values, encode categories, and visualize insights.",
    },
    "linear regression": {
        "aliases": ["linear regression", "regression", "lasso", "ridge regression", "ridge", "lasso regression"],
        "prerequisites": ["python", "data preprocessing"],
        "videos": {
            "beginner": [
                {"title": "Linear Regression Clearly Explained", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=nk2CQITm_eo"},
                {"title": "Machine Learning with Python: Linear Regression", "channel": "freeCodeCamp.org", "url": "https://www.youtube.com/watch?v=i_LwzRVP7bg"},
            ],
            "intermediate": [
                {"title": "Ridge and Lasso Regression", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=Q81RR3yKn30"},
                {"title": "Regularization in ML", "channel": "Krish Naik", "url": "https://www.youtube.com/watch?v=NGf0voTMlcs"},
            ],
            "advanced": [
                {"title": "Regression Model Evaluation", "channel": "Data School", "url": "https://www.youtube.com/watch?v=2AQKmw14mHM"},
                {"title": "Feature Engineering for Regression", "channel": "Krish Naik", "url": "https://www.youtube.com/watch?v=smN4R6JHrR8"},
            ],
        },
        "courses": [
            {"title": "Machine Learning Specialization", "provider": "Stanford / Coursera", "url": "https://www.coursera.org/specializations/machine-learning-introduction", "certificate": True},
            {"title": "Applied Machine Learning in Python", "provider": "Coursera", "url": "https://www.coursera.org/learn/python-machine-learning", "certificate": True},
            {"title": "Intro to Machine Learning", "provider": "Kaggle Learn", "url": "https://www.kaggle.com/learn/intro-to-machine-learning", "certificate": False},
        ],
        "project": "Predict student exam scores from study hours, attendance, and assignment completion using linear, ridge, and lasso regression.",
    },
    "classification": {
        "aliases": ["logistic regression", "svm", "support vector machine", "knn", "binary classifier", "classification"],
        "prerequisites": ["python", "data preprocessing", "linear regression"],
        "videos": {
            "beginner": [
                {"title": "Logistic Regression Clearly Explained", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=yIYKR4sgzI8"},
                {"title": "KNN Algorithm Explained", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=HVXime0nQeI"},
            ],
            "intermediate": [
                {"title": "Support Vector Machines Clearly Explained", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=efR1C6CvhmE"},
                {"title": "Classification in Machine Learning", "channel": "Krish Naik", "url": "https://www.youtube.com/watch?v=fiz1ORTBGpY"},
            ],
            "advanced": [
                {"title": "Model Evaluation Metrics", "channel": "Data School", "url": "https://www.youtube.com/watch?v=85dtiMz9tSo"},
                {"title": "Advanced Classification with Scikit-learn", "channel": "freeCodeCamp.org", "url": "https://www.youtube.com/watch?v=7eh4d6sabA0"},
            ],
        },
        "courses": [
            {"title": "Supervised Machine Learning: Classification", "provider": "Coursera", "url": "https://www.coursera.org/learn/machine-learning", "certificate": True},
            {"title": "Machine Learning Fundamentals", "provider": "IBM Skills Network", "url": "https://www.coursera.org/learn/machine-learning-with-python", "certificate": True},
        ],
        "project": "Build a classifier to predict whether a student needs extra support using Logistic Regression, SVM, and KNN.",
    },
    "decision trees": {
        "aliases": ["decision tree", "tree-based algorithm", "pruning", "random forest", "extra trees"],
        "prerequisites": ["python", "data preprocessing", "classification"],
        "videos": {
            "beginner": [
                {"title": "Decision Trees, Clearly Explained", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=7VeUPuFGJHk"},
                {"title": "Random Forest Clearly Explained", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=J4Wdy0Wc_xQ"},
            ],
            "intermediate": [
                {"title": "Decision Tree Pruning", "channel": "Krish Naik", "url": "https://www.youtube.com/watch?v=wpNl-JwwplA"},
                {"title": "Ensemble Learning", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=9P04KMAwafY"},
            ],
            "advanced": [
                {"title": "XGBoost Part 1", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=OtD8wVaFm6E"},
                {"title": "Gradient Boosting Explained", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=3CC4N4z3GJc"},
            ],
        },
        "courses": [
            {"title": "Trees, Random Forests and Boosting", "provider": "Coursera", "url": "https://www.coursera.org/learn/trees-random-forests-and-boosting", "certificate": True},
            {"title": "Machine Learning Explainability", "provider": "Coursera", "url": "https://www.coursera.org/learn/machine-learning-explainability", "certificate": True},
        ],
        "project": "Predict student placement readiness using Decision Tree, Random Forest, and Gradient Boosting, then compare feature importance.",
    },
    "clustering": {
        "aliases": ["k means", "k-means", "agglomerative", "clustering", "dendrogram"],
        "prerequisites": ["python", "data preprocessing"],
        "videos": {
            "beginner": [
                {"title": "K-means Clustering Clearly Explained", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=4b5d3muPQmA"},
                {"title": "Hierarchical Clustering Explained", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=7xHsRkOdVwo"},
            ],
            "intermediate": [
                {"title": "Clustering in Machine Learning", "channel": "Krish Naik", "url": "https://www.youtube.com/watch?v=5I3Ei69I40s"},
                {"title": "Dendrogram Tutorial", "channel": "codebasics", "url": "https://www.youtube.com/watch?v=7xHsRkOdVwo"},
            ],
            "advanced": [
                {"title": "Choosing K in Clustering", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=HMOI_lkzW08"},
                {"title": "Customer Segmentation Project", "channel": "Krish Naik", "url": "https://www.youtube.com/watch?v=EItlUEPCIzM"},
            ],
        },
        "courses": [
            {"title": "Unsupervised Learning, Recommenders, Reinforcement Learning", "provider": "Coursera", "url": "https://www.coursera.org/learn/unsupervised-learning-recommenders-reinforcement-learning", "certificate": True},
            {"title": "Clustering and Retrieval", "provider": "Coursera", "url": "https://www.coursera.org/learn/ml-clustering-and-retrieval", "certificate": True},
        ],
        "project": "Cluster students by learning style and engagement using K-Means and Agglomerative Clustering.",
    },
    "dimensionality reduction": {
        "aliases": ["pca", "lda", "dimensionality reduction"],
        "prerequisites": ["python", "data preprocessing", "classification"],
        "videos": {
            "beginner": [
                {"title": "Principal Component Analysis (PCA), Step-by-Step", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=FgakZw6K1QQ"},
                {"title": "Linear Discriminant Analysis", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=azXCzI57Yfc"},
            ],
            "intermediate": [
                {"title": "PCA in Machine Learning", "channel": "Krish Naik", "url": "https://www.youtube.com/watch?v=HMOI_lkzW08"},
                {"title": "LDA for Classification", "channel": "Krish Naik", "url": "https://www.youtube.com/watch?v=_UVHneBUBW0"},
            ],
            "advanced": [
                {"title": "When to Use PCA vs Feature Selection", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=HMOI_lkzW08"},
                {"title": "Dimensionality Reduction Project", "channel": "Data School", "url": "https://www.youtube.com/watch?v=FgakZw6K1QQ"},
            ],
        },
        "courses": [
            {"title": "Feature Engineering", "provider": "Coursera", "url": "https://www.coursera.org/learn/feature-engineering", "certificate": True},
            {"title": "Applied Data Science with Python", "provider": "Coursera", "url": "https://www.coursera.org/specializations/data-science-python", "certificate": True},
        ],
        "project": "Reduce student feature dimensions using PCA and compare classification accuracy before and after reduction.",
    },
    "naive bayes": {
        "aliases": ["naive bayes", "bayesian", "bayesian network", "heart disease"],
        "prerequisites": ["python", "classification"],
        "videos": {
            "beginner": [
                {"title": "Naive Bayes, Clearly Explained", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=O2L2Uv9pdDA"},
                {"title": "Bayesian Networks in AI", "channel": "Simplilearn", "url": "https://www.youtube.com/watch?v=3q9x7Q0vT2Q"},
            ],
            "intermediate": [
                {"title": "Naive Bayes for Classification", "channel": "Krish Naik", "url": "https://www.youtube.com/watch?v=temQ8m4nM2w"},
                {"title": "Probabilistic Graphical Models", "channel": "Stanford Online", "url": "https://www.youtube.com/watch?v=JmWJfw6YVnA"},
            ],
            "advanced": [
                {"title": "Bayesian Reasoning for Diagnosis", "channel": "MIT OpenCourseWare", "url": "https://www.youtube.com/watch?v=BrK7X_XlGB8"},
                {"title": "Medical Prediction with Naive Bayes", "channel": "codebasics", "url": "https://www.youtube.com/watch?v=TemQ8m4nM2w"},
            ],
        },
        "courses": [
            {"title": "Probabilistic Graphical Models", "provider": "Stanford Online", "url": "https://online.stanford.edu/courses/soe-yprobgraficalprobabilistic-graphical-models-1-representation", "certificate": True},
            {"title": "Machine Learning with Python", "provider": "IBM / Coursera", "url": "https://www.coursera.org/learn/machine-learning-with-python", "certificate": True},
        ],
        "project": "Build a heart disease risk predictor using Naive Bayes and explain the conditional probabilities.",
    },
    "neural networks": {
        "aliases": ["neural network", "deep learning", "activation function", "optimisation"],
        "prerequisites": ["python", "classification", "linear regression"],
        "videos": {
            "beginner": [
                {"title": "But what is a Neural Network?", "channel": "3Blue1Brown", "url": "https://www.youtube.com/watch?v=aircAruvnKk"},
                {"title": "Deep Learning Explained", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=CqOfi41LfDw"},
            ],
            "intermediate": [
                {"title": "Activation Functions Explained", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=-7scQpJT7uo"},
                {"title": "Neural Networks with Keras", "channel": "freeCodeCamp.org", "url": "https://www.youtube.com/watch?v=qFJeN9V1ZsI"},
            ],
            "advanced": [
                {"title": "Optimization in Deep Learning", "channel": "DeepLearningAI", "url": "https://www.youtube.com/watch?v=mdKjMPmcWjY"},
                {"title": "Modern Neural Networks in Practice", "channel": "freeCodeCamp.org", "url": "https://www.youtube.com/watch?v=VyWAvY2CF9c"},
            ],
        },
        "courses": [
            {"title": "Deep Learning Specialization", "provider": "DeepLearning.AI / Coursera", "url": "https://www.coursera.org/specializations/deep-learning", "certificate": True},
            {"title": "Practical Deep Learning for Coders", "provider": "fast.ai", "url": "https://course.fast.ai/", "certificate": False},
        ],
        "project": "Build a neural network to predict student learning level from quiz, attendance, and practice data.",
    },
    "automl": {
        "aliases": ["automl", "autogluon", "h2o automl", "gradient boosting", "xgboost", "lightgbm", "catboost"],
        "prerequisites": ["python", "data preprocessing", "classification", "decision trees"],
        "videos": {
            "beginner": [
                {"title": "What is AutoML?", "channel": "Google Cloud Tech", "url": "https://www.youtube.com/watch?v=0rMkH0vQn6Y"},
                {"title": "Gradient Boosting Explained", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=3CC4N4z3GJc"},
            ],
            "intermediate": [
                {"title": "XGBoost Clearly Explained", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=OtD8wVaFm6E"},
                {"title": "CatBoost Explained", "channel": "Yandex Research", "url": "https://www.youtube.com/watch?v=KXOTSkPL2X4"},
            ],
            "advanced": [
                {"title": "AutoML with H2O", "channel": "H2O.ai", "url": "https://www.youtube.com/watch?v=8C4sW2bYO8M"},
                {"title": "AutoGluon Tutorial", "channel": "AWS Developers", "url": "https://www.youtube.com/watch?v=Hj4e0w9mN8E"},
            ],
        },
        "courses": [
            {"title": "Machine Learning Engineering for Production", "provider": "DeepLearning.AI / Coursera", "url": "https://www.coursera.org/specializations/machine-learning-engineering-for-production-mlops", "certificate": True},
            {"title": "Introduction to AutoML", "provider": "Google Cloud Skills Boost", "url": "https://www.cloudskillsboost.google/", "certificate": True},
        ],
        "project": "Compare Logistic Regression, Random Forest, Gradient Boosting, and Extra Trees on student performance data, then choose the best model automatically.",
    },
}

QUIZ_QUESTIONS = {
    "python": [
        {"q": "Which library is mainly used for numerical arrays in Python?", "options": ["NumPy", "Flask", "OpenCV", "NLTK"], "answer": "NumPy"},
        {"q": "Which data structure stores key-value pairs?", "options": ["list", "tuple", "dictionary", "set"], "answer": "dictionary"},
    ],
    "data preprocessing": [
        {"q": "What is the main purpose of feature scaling?", "options": ["Increase rows", "Reduce model bias due to scale", "Delete outliers", "Encode labels"], "answer": "Reduce model bias due to scale"},
        {"q": "Handling missing values is part of?", "options": ["Deployment", "Data preprocessing", "Visualization only", "Testing only"], "answer": "Data preprocessing"},
    ],
    "linear regression": [
        {"q": "Linear regression is mainly used for?", "options": ["Clustering", "Regression", "Association rules", "Image segmentation"], "answer": "Regression"},
        {"q": "Ridge and Lasso are mainly used for?", "options": ["Data collection", "Regularization", "Label encoding", "Dendrograms"], "answer": "Regularization"},
    ],
    "classification": [
        {"q": "Logistic Regression is mainly used for?", "options": ["Continuous prediction", "Classification", "Clustering", "Dimensionality reduction"], "answer": "Classification"},
        {"q": "KNN predicts using?", "options": ["Nearest neighbors", "Gradient descent only", "Random guessing", "SQL queries"], "answer": "Nearest neighbors"},
    ],
    "decision trees": [
        {"q": "Decision trees are popular because they are?", "options": ["Interpretable", "Always fastest", "Unsupervised", "Only for images"], "answer": "Interpretable"},
        {"q": "Pruning is used to?", "options": ["Increase overfitting", "Reduce overfitting", "Create more features", "Shuffle data"], "answer": "Reduce overfitting"},
    ],
    "clustering": [
        {"q": "K-Means is an example of?", "options": ["Supervised learning", "Unsupervised learning", "Reinforcement learning", "Rule-based AI"], "answer": "Unsupervised learning"},
        {"q": "A dendrogram is commonly used in?", "options": ["Linear regression", "Agglomerative clustering", "Naive Bayes", "KNN"], "answer": "Agglomerative clustering"},
    ],
    "dimensionality reduction": [
        {"q": "PCA is mainly used to?", "options": ["Increase dimensions", "Reduce dimensions", "Generate labels", "Create rules"], "answer": "Reduce dimensions"},
        {"q": "LDA is useful for?", "options": ["Supervised dimensionality reduction", "Random forests", "Hyperparameter tuning", "Clustering only"], "answer": "Supervised dimensionality reduction"},
    ],
    "naive bayes": [
        {"q": "Naive Bayes is based on?", "options": ["Conditional probability", "Backpropagation", "Path planning", "Sorting"], "answer": "Conditional probability"},
        {"q": "Bayesian networks are useful for?", "options": ["Reasoning under uncertainty", "Video editing", "Path compression", "Clustering"], "answer": "Reasoning under uncertainty"},
    ],
    "neural networks": [
        {"q": "An activation function is used to add?", "options": ["Noise", "Non-linearity", "Rows", "Classes"], "answer": "Non-linearity"},
        {"q": "Which is a common optimizer?", "options": ["Adam", "Merge Sort", "KNN", "One-hot"], "answer": "Adam"},
    ],
    "automl": [
        {"q": "AutoML mainly helps with?", "options": ["Automated model selection and tuning", "Only plotting", "Only data entry", "Only web design"], "answer": "Automated model selection and tuning"},
        {"q": "Gradient boosting combines?", "options": ["Weak learners into a strong model", "Only clusters", "Only SQL tables", "Only dictionaries"], "answer": "Weak learners into a strong model"},
    ],
}


ADDITIONAL_TOPICS = {
    "statistics": {
        "aliases": ["statistics", "mean median mode", "variance", "standard deviation", "descriptive statistics"],
        "prerequisites": ["python"],
        "videos": {
            "beginner": [
                {"title": "Statistics Fundamentals", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=xxpc-HPKN28"},
                {"title": "Mean Median Mode Explained", "channel": "Khan Academy", "url": "https://www.youtube.com/watch?v=uhxtUt_-GyM"}
            ],
            "intermediate": [
                {"title": "Probability and Statistics for ML", "channel": "freeCodeCamp.org", "url": "https://www.youtube.com/watch?v=KyIrJeK2DKY"},
                {"title": "Standard Deviation and Variance", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=SzZ6GpcfoQY"}
            ],
            "advanced": [
                {"title": "Inferential Statistics", "channel": "Khan Academy", "url": "https://www.youtube.com/watch?v=8idr1WZ1A7Q"},
                {"title": "Statistics for Data Science", "channel": "CampusX", "url": "https://www.youtube.com/watch?v=tpCFfeUEGs8"}
            ]
        },
        "courses": [
            {"title": "Basic Statistics", "provider": "Coursera", "url": "https://www.coursera.org/learn/basic-statistics", "certificate": True},
            {"title": "Intro to Statistics", "provider": "Khan Academy", "url": "https://www.khanacademy.org/math/statistics-probability", "certificate": False}
        ],
        "project": "Analyze a student marks dataset and compute mean, median, variance, and standard deviation with visual charts."
    },
    "probability": {
        "aliases": ["probability", "bayes theorem", "random variable", "expected value"],
        "prerequisites": ["statistics"],
        "videos": {
            "beginner": [
                {"title": "Probability Basics", "channel": "Khan Academy", "url": "https://www.youtube.com/watch?v=uzkc-qNVoOk"},
                {"title": "Bayes Theorem", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=HZGCoVF3YvM"}
            ],
            "intermediate": [
                {"title": "Probability for Machine Learning", "channel": "Krish Naik", "url": "https://www.youtube.com/watch?v=uzkc-qNVoOk"},
                {"title": "Expected Value Explained", "channel": "Khan Academy", "url": "https://www.youtube.com/watch?v=aZAxXqJ4rE0"}
            ],
            "advanced": [
                {"title": "Conditional Probability", "channel": "MIT OpenCourseWare", "url": "https://www.youtube.com/watch?v=E8B3RmMIW0A"},
                {"title": "Probability Distributions", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=oI3hZJqXJuc"}
            ]
        },
        "courses": [
            {"title": "Probability and Statistics", "provider": "Coursera", "url": "https://www.coursera.org/learn/mathematics-for-machine-learning-probability", "certificate": True},
            {"title": "Statistics and Probability", "provider": "Khan Academy", "url": "https://www.khanacademy.org/math/statistics-probability", "certificate": False}
        ],
        "project": "Simulate dice and card experiments in Python to understand probability distributions and Bayes theorem."
    },
    "feature engineering": {
        "aliases": ["feature engineering", "feature selection", "one hot encoding", "encoding", "scaling"],
        "prerequisites": ["python", "data preprocessing", "statistics"],
        "videos": {
            "beginner": [
                {"title": "Feature Engineering Basics", "channel": "Krish Naik", "url": "https://www.youtube.com/watch?v=0xVqLJe9_CY"},
                {"title": "Encoding Categorical Data", "channel": "Data School", "url": "https://www.youtube.com/watch?v=0B5eIE_1vpU"}
            ],
            "intermediate": [
                {"title": "Feature Selection for ML", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=HMOI_lkzW08"},
                {"title": "Pipeline and Preprocessing", "channel": "Data School", "url": "https://www.youtube.com/watch?v=0B5eIE_1vpU"}
            ],
            "advanced": [
                {"title": "Advanced Feature Engineering", "channel": "Kaggle", "url": "https://www.youtube.com/watch?v=N9fDIAflCMY"},
                {"title": "Feature Store Concepts", "channel": "Tecton", "url": "https://www.youtube.com/watch?v=1x3jvGJuRkQ"}
            ]
        },
        "courses": [
            {"title": "Feature Engineering", "provider": "Coursera", "url": "https://www.coursera.org/learn/feature-engineering", "certificate": True},
            {"title": "Intermediate Machine Learning", "provider": "Kaggle Learn", "url": "https://www.kaggle.com/learn/intermediate-machine-learning", "certificate": False}
        ],
        "project": "Create an ML preprocessing pipeline with encoding, scaling, feature selection, and train-test transformation."
    },
    "model evaluation": {
        "aliases": ["model evaluation", "precision recall", "f1 score", "roc auc", "cross validation", "confusion matrix"],
        "prerequisites": ["classification", "linear regression"],
        "videos": {
            "beginner": [
                {"title": "Confusion Matrix Explained", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=Kdsp6soqA7o"},
                {"title": "Precision and Recall", "channel": "Google Developers", "url": "https://www.youtube.com/watch?v=4jRBRDbJemM"}
            ],
            "intermediate": [
                {"title": "ROC and AUC", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=4jRBRDbJemM"},
                {"title": "Cross Validation", "channel": "Data School", "url": "https://www.youtube.com/watch?v=fSytzGwwBVw"}
            ],
            "advanced": [
                {"title": "Model Selection and Validation", "channel": "MIT OpenCourseWare", "url": "https://www.youtube.com/watch?v=0GrciaGYzV0"},
                {"title": "Advanced Evaluation Metrics", "channel": "Krish Naik", "url": "https://www.youtube.com/watch?v=85dtiMz9tSo"}
            ]
        },
        "courses": [
            {"title": "Machine Learning Model Evaluation", "provider": "Coursera", "url": "https://www.coursera.org/learn/machine-learning-projects", "certificate": True},
            {"title": "Intro to ML", "provider": "Kaggle Learn", "url": "https://www.kaggle.com/learn/intro-to-machine-learning", "certificate": False}
        ],
        "project": "Evaluate multiple classifiers using confusion matrix, ROC-AUC, precision, recall, and cross-validation."
    },
    "computer vision": {
        "aliases": ["computer vision", "image processing", "opencv", "vision"],
        "prerequisites": ["python", "neural networks"],
        "videos": {
            "beginner": [
                {"title": "Computer Vision Basics", "channel": "freeCodeCamp.org", "url": "https://www.youtube.com/watch?v=01sAkU_NvOY"},
                {"title": "OpenCV Crash Course", "channel": "Murtaza's Workshop", "url": "https://www.youtube.com/watch?v=WQeoO7MI0Bs"}
            ],
            "intermediate": [
                {"title": "CNN for Image Classification", "channel": "DeepLearningAI", "url": "https://www.youtube.com/watch?v=YRhxdVk_sIs"},
                {"title": "Image Augmentation", "channel": "TensorFlow", "url": "https://www.youtube.com/watch?v=0u7mYQfF2kY"}
            ],
            "advanced": [
                {"title": "Object Detection Explained", "channel": "Aladdin Persson", "url": "https://www.youtube.com/watch?v=YqkISICHH-U"},
                {"title": "Transfer Learning for Vision", "channel": "TensorFlow", "url": "https://www.youtube.com/watch?v=yofjFQddwHE"}
            ]
        },
        "courses": [
            {"title": "Deep Learning for Computer Vision", "provider": "Coursera", "url": "https://www.coursera.org/learn/convolutional-neural-networks", "certificate": True},
            {"title": "Practical CV with Python", "provider": "Udemy", "url": "https://www.udemy.com/topic/computer-vision/", "certificate": True}
        ],
        "project": "Build an image classifier for handwritten digits or fruits using OpenCV and CNNs."
    },
    "nlp": {
        "aliases": ["nlp", "natural language processing", "text mining", "tokenization"],
        "prerequisites": ["python", "neural networks"],
        "videos": {
            "beginner": [
                {"title": "NLP for Beginners", "channel": "freeCodeCamp.org", "url": "https://www.youtube.com/watch?v=CMrHM8a3hqw"},
                {"title": "Tokenization and Text Cleaning", "channel": "Krish Naik", "url": "https://www.youtube.com/watch?v=vyOgWhwUmec"}
            ],
            "intermediate": [
                {"title": "Word Embeddings Explained", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=viZrOnJclY0"},
                {"title": "Sentiment Analysis Project", "channel": "CampusX", "url": "https://www.youtube.com/watch?v=dXxQ0LR-3Hg"}
            ],
            "advanced": [
                {"title": "Attention and Transformers", "channel": "3Blue1Brown", "url": "https://www.youtube.com/watch?v=eMlx5fFNoYc"},
                {"title": "BERT Explained", "channel": "Hugging Face", "url": "https://www.youtube.com/watch?v=xI0HHN5XKDo"}
            ]
        },
        "courses": [
            {"title": "Natural Language Processing Specialization", "provider": "DeepLearning.AI / Coursera", "url": "https://www.coursera.org/specializations/natural-language-processing", "certificate": True},
            {"title": "NLP with Python", "provider": "Udemy", "url": "https://www.udemy.com/topic/natural-language-processing/", "certificate": True}
        ],
        "project": "Build a sentiment analysis app for movie or product reviews using TF-IDF and a classifier."
    },
    "transformers": {
        "aliases": ["transformer", "transformers", "attention", "bert", "gpt"],
        "prerequisites": ["nlp", "neural networks"],
        "videos": {
            "beginner": [
                {"title": "Transformers Explained Visually", "channel": "3Blue1Brown", "url": "https://www.youtube.com/watch?v=wjZofJX0v4M"},
                {"title": "Attention is All You Need", "channel": "Yannic Kilcher", "url": "https://www.youtube.com/watch?v=iDulhoQ2pro"}
            ],
            "intermediate": [
                {"title": "BERT and GPT Explained", "channel": "Hugging Face", "url": "https://www.youtube.com/watch?v=7xTGNNLPyMI"},
                {"title": "Fine-tuning Transformers", "channel": "Hugging Face", "url": "https://www.youtube.com/watch?v=Q8IpJdPxWkE"}
            ],
            "advanced": [
                {"title": "Large Language Models", "channel": "Andrej Karpathy", "url": "https://www.youtube.com/watch?v=zjkBMFhNj_g"},
                {"title": "Transformers in Practice", "channel": "DeepLearningAI", "url": "https://www.youtube.com/watch?v=kCc8FmEb1nY"}
            ]
        },
        "courses": [
            {"title": "Transformers for NLP", "provider": "Coursera", "url": "https://www.coursera.org/learn/transformers", "certificate": True},
            {"title": "Hugging Face NLP Course", "provider": "Hugging Face", "url": "https://huggingface.co/learn/nlp-course", "certificate": False}
        ],
        "project": "Fine-tune a small transformer model for text classification or question answering."
    },
    "llm": {
        "aliases": ["llm", "large language model", "chatgpt", "gpt", "language model"],
        "prerequisites": ["transformers", "nlp"],
        "videos": {
            "beginner": [
                {"title": "What is an LLM?", "channel": "IBM Technology", "url": "https://www.youtube.com/watch?v=5sLYAQS9sWQ"},
                {"title": "LLM Basics", "channel": "DeepLearningAI", "url": "https://www.youtube.com/watch?v=zjkBMFhNj_g"}
            ],
            "intermediate": [
                {"title": "Prompting and RAG", "channel": "LangChain", "url": "https://www.youtube.com/watch?v=2TJxpyO3ei4"},
                {"title": "Fine-tuning LLMs", "channel": "Hugging Face", "url": "https://www.youtube.com/watch?v=eC6Hd1hFvos"}
            ],
            "advanced": [
                {"title": "Serving LLMs", "channel": "vLLM", "url": "https://www.youtube.com/watch?v=LvBef4wGSNk"},
                {"title": "Evaluation of LLMs", "channel": "Weights & Biases", "url": "https://www.youtube.com/watch?v=oeQPPm5A83I"}
            ]
        },
        "courses": [
            {"title": "Generative AI with LLMs", "provider": "DeepLearning.AI / Coursera", "url": "https://www.coursera.org/learn/generative-ai-with-llms", "certificate": True},
            {"title": "Intro to Large Language Models", "provider": "Google Cloud Skills Boost", "url": "https://www.cloudskillsboost.google/", "certificate": True}
        ],
        "project": "Build a topic Q&A tutor using embeddings or retrieval-augmented generation over your notes."
    },
    "prompt engineering": {
        "aliases": ["prompt engineering", "prompting", "few shot prompting", "chain of thought"],
        "prerequisites": ["llm"],
        "videos": {
            "beginner": [
                {"title": "Prompt Engineering Basics", "channel": "DeepLearningAI", "url": "https://www.youtube.com/watch?v=dOxUroR57xs"},
                {"title": "Effective Prompting", "channel": "Google Cloud Tech", "url": "https://www.youtube.com/watch?v=VJX0LyxRV0E"}
            ],
            "intermediate": [
                {"title": "Few-shot Prompting", "channel": "Weights & Biases", "url": "https://www.youtube.com/watch?v=J0m4rcx0of4"},
                {"title": "Prompt Patterns", "channel": "Microsoft Reactor", "url": "https://www.youtube.com/watch?v=ePzJd79JZsU"}
            ],
            "advanced": [
                {"title": "Prompt Evaluation", "channel": "LangChain", "url": "https://www.youtube.com/watch?v=igUE2pwM2uY"},
                {"title": "Agents and Tool Use", "channel": "DeepLearningAI", "url": "https://www.youtube.com/watch?v=sal78ACtGTc"}
            ]
        },
        "courses": [
            {"title": "ChatGPT Prompt Engineering for Developers", "provider": "DeepLearning.AI", "url": "https://www.deeplearning.ai/short-courses/chatgpt-prompt-engineering-for-developers/", "certificate": False},
            {"title": "Prompt Design in Vertex AI", "provider": "Google Cloud", "url": "https://www.cloudskillsboost.google/", "certificate": True}
        ],
        "project": "Design a prompt library for syllabus explanation, quiz generation, and doubt-solving workflows."
    },
    "generative ai": {
        "aliases": ["generative ai", "genai", "diffusion", "foundation model"],
        "prerequisites": ["llm", "neural networks"],
        "videos": {
            "beginner": [
                {"title": "Generative AI Explained", "channel": "IBM Technology", "url": "https://www.youtube.com/watch?v=G2fqAlgmoPo"},
                {"title": "Foundation Models", "channel": "Google Cloud Tech", "url": "https://www.youtube.com/watch?v=mEsleV16qdo"}
            ],
            "intermediate": [
                {"title": "Diffusion Models", "channel": "Two Minute Papers", "url": "https://www.youtube.com/watch?v=HoKDTa5jHvg"},
                {"title": "RAG Explained", "channel": "Weights & Biases", "url": "https://www.youtube.com/watch?v=T-D1OfcDW1M"}
            ],
            "advanced": [
                {"title": "Advanced GenAI Systems", "channel": "DeepLearningAI", "url": "https://www.youtube.com/watch?v=2TJxpyO3ei4"},
                {"title": "Evaluating Generative Models", "channel": "Hugging Face", "url": "https://www.youtube.com/watch?v=9Tb3XfB7JZ4"}
            ]
        },
        "courses": [
            {"title": "Generative AI Learning Path", "provider": "Google Cloud", "url": "https://www.cloudskillsboost.google/", "certificate": True},
            {"title": "Introduction to Generative AI", "provider": "Coursera", "url": "https://www.coursera.org/learn/introduction-to-generative-ai", "certificate": True}
        ],
        "project": "Build a note summarizer or image prompt assistant using an LLM API and evaluation rubric."
    },
    "reinforcement learning": {
        "aliases": ["reinforcement learning", "q learning", "policy gradient", "agent"],
        "prerequisites": ["probability", "neural networks"],
        "videos": {
            "beginner": [
                {"title": "Reinforcement Learning Explained", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=FgzM3zpZ55o"},
                {"title": "Q-Learning Basics", "channel": "freeCodeCamp.org", "url": "https://www.youtube.com/watch?v=JgvyzIkgxF0"}
            ],
            "intermediate": [
                {"title": "Markov Decision Processes", "channel": "DeepLizard", "url": "https://www.youtube.com/watch?v=IuiTVaSncwc"},
                {"title": "Policy Gradient", "channel": "Hugging Face", "url": "https://www.youtube.com/watch?v=5P7I-xPq8u8"}
            ],
            "advanced": [
                {"title": "Deep Reinforcement Learning", "channel": "DeepMind", "url": "https://www.youtube.com/watch?v=2pWv7GOvuf0"},
                {"title": "RL in Practice", "channel": "OpenAI", "url": "https://www.youtube.com/watch?v=Qe9aQfW8j5g"}
            ]
        },
        "courses": [
            {"title": "Reinforcement Learning Specialization", "provider": "Coursera", "url": "https://www.coursera.org/specializations/reinforcement-learning", "certificate": True},
            {"title": "Deep RL Course", "provider": "Hugging Face", "url": "https://huggingface.co/learn/deep-rl-course/", "certificate": False}
        ],
        "project": "Train an agent to solve a simple grid-world or balancing game using Q-learning."
    },
    "model deployment": {
        "aliases": ["model deployment", "mlops", "serving", "deployment", "fastapi", "flask api"],
        "prerequisites": ["model evaluation", "automl"],
        "videos": {
            "beginner": [
                {"title": "Deploy ML Models with Flask", "channel": "Krish Naik", "url": "https://www.youtube.com/watch?v=UbCWoMf80PY"},
                {"title": "FastAPI for ML", "channel": "freeCodeCamp.org", "url": "https://www.youtube.com/watch?v=0sOvCWFmrtA"}
            ],
            "intermediate": [
                {"title": "MLflow and Experiment Tracking", "channel": "Databricks", "url": "https://www.youtube.com/watch?v=859OxXrt_TI"},
                {"title": "Docker for ML Deployment", "channel": "TechWorld with Nana", "url": "https://www.youtube.com/watch?v=pg19Z8LL06w"}
            ],
            "advanced": [
                {"title": "MLOps Pipeline", "channel": "Google Cloud Tech", "url": "https://www.youtube.com/watch?v=06-AZXmwHjo"},
                {"title": "Monitoring ML Models", "channel": "Weights & Biases", "url": "https://www.youtube.com/watch?v=02ed2cF6y1c"}
            ]
        },
        "courses": [
            {"title": "Machine Learning Engineering for Production", "provider": "Coursera", "url": "https://www.coursera.org/specializations/machine-learning-engineering-for-production-mlops", "certificate": True},
            {"title": "MLOps Zoomcamp", "provider": "DataTalksClub", "url": "https://github.com/DataTalksClub/mlops-zoomcamp", "certificate": False}
        ],
        "project": "Deploy a trained classifier as a REST API with prediction logging and a simple React dashboard."
    },
}

TOPIC_CATALOG.update(ADDITIONAL_TOPICS)

ADDITIONAL_QUIZ_QUESTIONS = {
    "statistics": [
        {"q": "Which measure shows the average value of a dataset?", "options": ["Mean", "Confusion matrix", "Entropy", "Recall"], "answer": "Mean"},
        {"q": "Standard deviation tells you about?", "options": ["Spread of data", "Model deployment", "Label count", "Activation function"], "answer": "Spread of data"},
    ],
    "probability": [
        {"q": "Probability values usually lie between?", "options": ["0 and 1", "1 and 10", "-1 and 1", "Any value"], "answer": "0 and 1"},
        {"q": "Bayes theorem is used to update?", "options": ["Probabilities after evidence", "HTML pages", "SQL indexes", "Video duration"], "answer": "Probabilities after evidence"},
    ],
    "feature engineering": [
        {"q": "One-hot encoding is mainly used for?", "options": ["Categorical variables", "Images only", "Sorting", "Neural pruning"], "answer": "Categorical variables"},
        {"q": "Feature selection helps by?", "options": ["Removing less useful features", "Increasing labels", "Adding noise", "Changing optimizer"], "answer": "Removing less useful features"},
    ],
    "model evaluation": [
        {"q": "Precision measures?", "options": ["How many predicted positives were correct", "How many rows are present", "Training time only", "Number of classes"], "answer": "How many predicted positives were correct"},
        {"q": "Cross-validation helps estimate?", "options": ["Generalization performance", "CSS design", "File size", "Video quality"], "answer": "Generalization performance"},
    ],
    "computer vision": [
        {"q": "OpenCV is commonly used for?", "options": ["Image processing", "Database joins", "Email sending", "Compiler design"], "answer": "Image processing"},
        {"q": "CNNs are especially strong for?", "options": ["Image tasks", "Sorting arrays", "SQL backups", "PDF editing"], "answer": "Image tasks"},
    ],
    "nlp": [
        {"q": "Tokenization splits text into?", "options": ["Smaller units", "Images", "Decision trees", "Gradients"], "answer": "Smaller units"},
        {"q": "Sentiment analysis predicts?", "options": ["Opinion polarity", "Pixel values", "Audio pitch", "Learning rate"], "answer": "Opinion polarity"},
    ],
    "transformers": [
        {"q": "Transformers are built around the idea of?", "options": ["Attention", "Sorting", "Backtracking", "Greedy pruning"], "answer": "Attention"},
        {"q": "BERT is mainly known for?", "options": ["Understanding text context", "Clustering customers", "Video rendering", "OS scheduling"], "answer": "Understanding text context"},
    ],
    "llm": [
        {"q": "LLM stands for?", "options": ["Large Language Model", "Low Level Memory", "Linear Logic Machine", "Local Learning Module"], "answer": "Large Language Model"},
        {"q": "RAG improves an LLM by adding?", "options": ["External retrieved knowledge", "More CSS", "Extra pixels", "USB drivers"], "answer": "External retrieved knowledge"},
    ],
    "prompt engineering": [
        {"q": "Few-shot prompting means?", "options": ["Giving examples in the prompt", "Using fewer GPUs", "Reducing file size", "Skipping training data"], "answer": "Giving examples in the prompt"},
        {"q": "A good prompt usually improves?", "options": ["Answer quality", "Disk speed", "Battery size", "Compiler warnings"], "answer": "Answer quality"},
    ],
    "generative ai": [
        {"q": "Generative AI is used to?", "options": ["Create new content", "Only sort data", "Only delete rows", "Only compress files"], "answer": "Create new content"},
        {"q": "Foundation models are typically?", "options": ["Pretrained on large data", "Manually hard-coded", "Only for images", "Only offline apps"], "answer": "Pretrained on large data"},
    ],
    "reinforcement learning": [
        {"q": "In RL, an agent learns by receiving?", "options": ["Rewards", "Only labels", "Only HTML", "Only images"], "answer": "Rewards"},
        {"q": "Q-learning updates a table of?", "options": ["State-action values", "Video frames", "Model cards", "CSV rows"], "answer": "State-action values"},
    ],
    "model deployment": [
        {"q": "Model deployment means?", "options": ["Making a model available for real use", "Deleting the model", "Only training again", "Only plotting results"], "answer": "Making a model available for real use"},
        {"q": "An API endpoint helps users or apps to?", "options": ["Send input and get predictions", "Only write CSS", "Only rename files", "Only draw graphs"], "answer": "Send input and get predictions"},
    ],
}

QUIZ_QUESTIONS.update(ADDITIONAL_QUIZ_QUESTIONS)


def normalize_topic(text: str) -> str:
    lowered = text.strip().lower()
    for topic, meta in TOPIC_CATALOG.items():
        if lowered == topic:
            return topic
        if lowered in [a.lower() for a in meta["aliases"]]:
            return topic
    return lowered


def match_topics_from_text(text: str) -> list[str]:
    content = text.lower()
    found: list[str] = []
    for topic, meta in TOPIC_CATALOG.items():
        keys = [topic] + meta["aliases"]
        if any(k.lower() in content for k in keys):
            found.append(topic)
    # if bullets or commas contain unknown topics, add cleaned tokens
    if not found:
        for token in [t.strip().lower() for t in text.replace("\n", ",").split(",") if t.strip()]:
            if token:
                found.append(token)
    return list(dict.fromkeys(found))

MORE_TOPICS = {
    "svm": {
        "aliases": ["svm", "support vector machine", "support vector machines"],
        "prerequisites": ["classification", "statistics"],
        "videos": {"beginner": [{"title": "Support Vector Machines Clearly Explained", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=efR1C6CvhmE"}]},
        "courses": [{"title": "Support Vector Machines in Python", "provider": "Coursera", "url": "https://www.coursera.org/", "certificate": True}],
        "project": "Train an SVM classifier on a student risk dataset and compare it with logistic regression.",
    },
    "ensemble methods": {
        "aliases": ["ensemble methods", "bagging", "boosting", "random forest", "xgboost"],
        "prerequisites": ["decision trees", "classification"],
        "videos": {"beginner": [{"title": "Ensemble Learning Explained", "channel": "StatQuest", "url": "https://www.youtube.com/watch?v=sQ870aTKqiM"}]},
        "courses": [{"title": "Ensemble Methods for Machine Learning", "provider": "Coursera", "url": "https://www.coursera.org/", "certificate": True}],
        "project": "Compare random forest, extra trees, and gradient boosting for performance prediction.",
    },
    "hyperparameter tuning": {
        "aliases": ["hyperparameter tuning", "grid search", "random search", "bayesian optimization"],
        "prerequisites": ["model evaluation", "classification"],
        "videos": {"beginner": [{"title": "Hyperparameter Tuning Explained", "channel": "Google Developers", "url": "https://www.youtube.com/watch?v=1PMM4CmxL7I"}]},
        "courses": [{"title": "Machine Learning Model Tuning", "provider": "Udemy", "url": "https://www.udemy.com/", "certificate": True}],
        "project": "Tune a student-score prediction model using grid search and compare the accuracy gain.",
    },
    "search algorithms": {
        "aliases": ["search algorithms", "bfs", "dfs", "a*", "a star"],
        "prerequisites": ["python"],
        "videos": {"beginner": [{"title": "Search Algorithms in AI", "channel": "Gate Smashers", "url": "https://www.youtube.com/watch?v=KfoXvD7zW8Q"}]},
        "courses": [{"title": "Artificial Intelligence Search Methods", "provider": "edX", "url": "https://www.edx.org/", "certificate": True}],
        "project": "Build BFS, DFS, and A* visualizations for a pathfinding grid.",
    },
    "knowledge representation": {
        "aliases": ["knowledge representation", "semantic network", "ontology", "facts and rules"],
        "prerequisites": ["search algorithms"],
        "videos": {"beginner": [{"title": "Knowledge Representation in AI", "channel": "Neso Academy", "url": "https://www.youtube.com/watch?v=z0mYTU4gW74"}]},
        "courses": [{"title": "Knowledge Representation and Reasoning", "provider": "Coursera", "url": "https://www.coursera.org/", "certificate": True}],
        "project": "Create a rule-based knowledge base for course and topic recommendations.",
    },
    "expert systems": {
        "aliases": ["expert systems", "inference engine", "rule based ai"],
        "prerequisites": ["knowledge representation"],
        "videos": {"beginner": [{"title": "Expert Systems in AI", "channel": "Gate Smashers", "url": "https://www.youtube.com/watch?v=lyXkQzP8Z0Y"}]},
        "courses": [{"title": "Introduction to Expert Systems", "provider": "Udemy", "url": "https://www.udemy.com/", "certificate": True}],
        "project": "Build a rule-based tutor that suggests next topics from a knowledge base.",
    },
    "fuzzy logic": {
        "aliases": ["fuzzy logic", "fuzzy set", "membership function"],
        "prerequisites": ["statistics"],
        "videos": {"beginner": [{"title": "Fuzzy Logic Basics", "channel": "Neso Academy", "url": "https://www.youtube.com/watch?v=IHzwL4q6P8w"}]},
        "courses": [{"title": "Fuzzy Logic Fundamentals", "provider": "Coursera", "url": "https://www.coursera.org/", "certificate": True}],
        "project": "Use fuzzy rules to estimate learner confidence and difficulty adaptation.",
    },
    "rag": {
        "aliases": ["rag", "retrieval augmented generation", "retrieval-augmented generation"],
        "prerequisites": ["llm", "nlp", "prompt engineering"],
        "videos": {"beginner": [{"title": "RAG Explained", "channel": "DeepLearningAI", "url": "https://www.youtube.com/watch?v=T-D1OfcDW1M"}]},
        "courses": [{"title": "RAG Systems with LLMs", "provider": "DeepLearning.AI", "url": "https://www.deeplearning.ai/", "certificate": True}],
        "project": "Build a syllabus PDF assistant that retrieves relevant chunks before answering.",
    },
}
TOPIC_CATALOG.update(MORE_TOPICS)
MORE_QUIZ = {
    "svm": [{"q": "SVM mainly tries to maximize the?", "options": ["Margin between classes", "Number of labels", "Training epochs", "Database joins"], "answer": "Margin between classes"}],
    "ensemble methods": [{"q": "Boosting mainly combines models in a?", "options": ["Sequential way", "Random file order", "Database-only way", "Static template"], "answer": "Sequential way"}],
    "hyperparameter tuning": [{"q": "Grid search is used to?", "options": ["Try multiple hyperparameter combinations", "Resize images", "Label data manually", "Deploy APIs"], "answer": "Try multiple hyperparameter combinations"}],
    "search algorithms": [{"q": "BFS explores nodes?", "options": ["Level by level", "Only from the end", "Randomly", "By clustering"], "answer": "Level by level"}],
    "knowledge representation": [{"q": "Knowledge representation is mainly about?", "options": ["Storing facts and relations for reasoning", "Only plotting graphs", "Compressing images", "GPU tuning"], "answer": "Storing facts and relations for reasoning"}],
    "expert systems": [{"q": "An expert system typically uses a?", "options": ["Knowledge base and inference engine", "Only CNN", "Only database trigger", "Compiler optimizer"], "answer": "Knowledge base and inference engine"}],
    "fuzzy logic": [{"q": "Fuzzy logic is useful when truth is?", "options": ["Partial and gradual", "Always binary only", "Unknown forever", "Equal to zero"], "answer": "Partial and gradual"}],
    "rag": [{"q": "RAG improves answers by adding?", "options": ["Retrieved external context", "More CSS", "More image pixels", "Faster compiler flags"], "answer": "Retrieved external context"}],
}
QUIZ_QUESTIONS.update(MORE_QUIZ)
