// Mock data fallbacks — used when Flask session data is not injected
// Flask injects real data via: window.__ASSESSMENT__ = {{ assessment | tojson }};

export const mockAssessment = [
  { topic: 'python', score_pct: 85, predicted_level: 'advanced', predicted_exam_score: 88, next_topics: ['numpy', 'pandas'] },
  { topic: 'statistics', score_pct: 62, predicted_level: 'intermediate', predicted_exam_score: 70, next_topics: ['linear regression'] },
  { topic: 'linear regression', score_pct: 40, predicted_level: 'beginner', predicted_exam_score: 52, next_topics: ['logistic regression'] },
  { topic: 'svm', score_pct: 30, predicted_level: 'beginner', predicted_exam_score: 45, next_topics: ['kernel trick', 'hyperparameters'] },
  { topic: 'neural networks', score_pct: 55, predicted_level: 'intermediate', predicted_exam_score: 65, next_topics: ['cnn', 'rnn'] },
];

export const mockProfile = {
  syllabus_text: 'Python, statistics, linear regression, logistic regression, SVM, neural networks, clustering, PCA',
  target_goal: 'ML for placement at top tech companies',
  topics: ['python', 'statistics', 'linear regression', 'logistic regression', 'svm', 'neural networks', 'clustering', 'pca'],
};

export const mockModelScores = {
  'Gradient Boosting': '94.2%',
  'Extra Trees': '91.7%',
  'Random Forest': '90.1%',
  'Logistic Regression': '82.3%',
  'SVM': '87.5%',
};

export const mockAccuracyTrend = [
  { day: 'Mon', accuracy: 42, target: 70 },
  { day: 'Tue', accuracy: 55, target: 70 },
  { day: 'Wed', accuracy: 51, target: 70 },
  { day: 'Thu', accuracy: 68, target: 70 },
  { day: 'Fri', accuracy: 73, target: 70 },
  { day: 'Sat', accuracy: 79, target: 70 },
  { day: 'Sun', accuracy: 85, target: 70 },
];

export const mockTopicMastery = [
  { topic: 'Python', mastery: 85 },
  { topic: 'Statistics', mastery: 62 },
  { topic: 'Lin. Reg.', mastery: 40 },
  { topic: 'SVM', mastery: 30 },
  { topic: 'Neural Net', mastery: 55 },
  { topic: 'Clustering', mastery: 48 },
];

export const mockLearningPath = [
  {
    topic: 'python',
    level: 'advanced',
    order: 1,
    status: 'completed',
    prerequisites: [],
    videos: [
      { title: 'Python for ML - Full Course', channel: 'freeCodeCamp', url: 'https://youtube.com/watch?v=rfscVS0vtbw', duration: '4h 26m' },
      { title: 'Python Data Science Handbook', channel: 'Jake VanderPlas', url: 'https://youtube.com/watch?v=1_fNFGwm7BA', duration: '2h 10m' },
    ],
    courses: [
      { title: 'Python for Everybody', provider: 'Coursera', url: '#', certificate: true, rating: 4.8 },
    ],
    project: 'Build a data analysis pipeline using Pandas and Matplotlib on a real dataset.',
  },
  {
    topic: 'statistics',
    level: 'intermediate',
    order: 2,
    status: 'in-progress',
    prerequisites: ['python'],
    videos: [
      { title: 'Statistics for Data Science', channel: 'StatQuest', url: 'https://youtube.com/watch?v=qBigTkBLU6g', duration: '1h 45m' },
    ],
    courses: [
      { title: 'Statistics with Python Specialization', provider: 'Coursera', url: '#', certificate: true, rating: 4.6 },
    ],
    project: 'Perform exploratory data analysis and hypothesis testing on a Kaggle dataset.',
  },
  {
    topic: 'linear regression',
    level: 'beginner',
    order: 3,
    status: 'recommended',
    prerequisites: ['statistics'],
    videos: [
      { title: 'Linear Regression - StatQuest', channel: 'StatQuest', url: 'https://youtube.com/watch?v=nk2CQITm_eo', duration: '22m' },
    ],
    courses: [
      { title: 'Machine Learning by Andrew Ng', provider: 'Coursera', url: '#', certificate: true, rating: 4.9 },
    ],
    project: 'Predict house prices using linear regression on the Boston Housing dataset.',
  },
  {
    topic: 'logistic regression',
    level: 'beginner',
    order: 4,
    status: 'locked',
    prerequisites: ['linear regression'],
    videos: [
      { title: 'Logistic Regression Explained', channel: 'StatQuest', url: 'https://youtube.com/watch?v=yIYKR4sgzI8', duration: '18m' },
    ],
    courses: [
      { title: 'ML A-Z: Hands-On Python', provider: 'Udemy', url: '#', certificate: true, rating: 4.5 },
    ],
    project: 'Binary classification: Titanic survival prediction.',
  },
  {
    topic: 'svm',
    level: 'beginner',
    order: 5,
    status: 'locked',
    prerequisites: ['logistic regression'],
    videos: [
      { title: 'Support Vector Machines', channel: 'Sentdex', url: 'https://youtube.com/watch?v=N1vOgolbjSc', duration: '30m' },
    ],
    courses: [
      { title: 'Advanced ML', provider: 'Coursera', url: '#', certificate: true, rating: 4.4 },
    ],
    project: 'Image classification with SVM on the MNIST dataset.',
  },
  {
    topic: 'neural networks',
    level: 'intermediate',
    order: 6,
    status: 'locked',
    prerequisites: ['linear regression', 'statistics'],
    videos: [
      { title: 'Neural Networks from Scratch', channel: '3Blue1Brown', url: 'https://youtube.com/watch?v=aircAruvnKk', duration: '19m' },
    ],
    courses: [
      { title: 'Deep Learning Specialization', provider: 'Coursera', url: '#', certificate: true, rating: 4.9 },
    ],
    project: 'Build a neural net from scratch using NumPy for digit recognition.',
  },
];

export const mockResources = [
  {
    topic: 'linear regression',
    level: 'beginner',
    video_source: 'hybrid',
    project: 'Predict house prices using linear regression on the Boston Housing dataset.',
    videos: [
      { title: 'Linear Regression - Full Tutorial', channel: 'StatQuest', url: 'https://www.youtube.com/watch?v=nk2CQITm_eo', viewCount: '2.1M', duration: '22m', rank_score: 9.8 },
      { title: 'Linear Regression with Python', channel: 'Sentdex', url: 'https://www.youtube.com/watch?v=JcI5Vnw0b2c', viewCount: '890K', duration: '35m', rank_score: 9.2 },
      { title: 'ML Crash Course: Linear Regression', channel: 'Google Developers', url: 'https://www.youtube.com/watch?v=4PHI11lX11I', viewCount: '1.4M', duration: '18m', rank_score: 9.0 },
    ],
    courses: [
      { title: 'Machine Learning by Andrew Ng', provider: 'Coursera', url: '#', certificate: true, verified: true, rating: 4.9, learners: '5.8M', duration_hours: 61, level: 'beginner', rank_score: 9.9 },
      { title: 'ML A-Z: Hands-On Python', provider: 'Udemy', url: '#', certificate: true, verified: true, rating: 4.5, learners: '850K', duration_hours: 44, level: 'beginner', rank_score: 9.1 },
      { title: 'Intro to Machine Learning', provider: 'Kaggle', url: '#', certificate: true, verified: true, rating: 4.7, learners: '300K', duration_hours: 5, level: 'beginner', rank_score: 8.8 },
    ],
    datasets: [
      { title: 'Boston Housing Dataset', source: 'Kaggle', level: 'beginner', url: '#', description: 'Classic dataset for regression. Predict median house values.' },
      { title: 'Ames Housing Dataset', source: 'Kaggle', level: 'beginner', url: '#', description: '79 features for house price prediction. Great for feature engineering.' },
      { title: 'California Housing Prices', source: 'Kaggle', level: 'intermediate', url: '#', description: 'Predict house prices from census data.' },
    ],
  },
  {
    topic: 'neural networks',
    level: 'intermediate',
    video_source: 'hybrid',
    project: 'Build a neural net from scratch using NumPy for digit recognition.',
    videos: [
      { title: 'But what is a neural network?', channel: '3Blue1Brown', url: 'https://www.youtube.com/watch?v=aircAruvnKk', viewCount: '15M', duration: '19m', rank_score: 9.9 },
      { title: 'Neural Networks from Scratch in Python', channel: 'Sentdex', url: 'https://www.youtube.com/watch?v=Wo5dMEP_BbI', viewCount: '1.2M', duration: '45m', rank_score: 9.4 },
    ],
    courses: [
      { title: 'Deep Learning Specialization', provider: 'Coursera', url: '#', certificate: true, verified: true, rating: 4.9, learners: '1.2M', duration_hours: 80, level: 'intermediate', rank_score: 9.9 },
      { title: 'Practical Deep Learning', provider: 'fast.ai', url: '#', certificate: false, verified: true, rating: 4.8, learners: '200K', duration_hours: 30, level: 'intermediate', rank_score: 9.3 },
    ],
    datasets: [
      { title: 'MNIST Handwritten Digits', source: 'Kaggle', level: 'beginner', url: '#', description: '70,000 images of handwritten digits. The "Hello World" of deep learning.' },
      { title: 'CIFAR-10', source: 'Kaggle', level: 'intermediate', url: '#', description: '60,000 32×32 colour images in 10 classes.' },
    ],
  },
];

export const mockChatHistory = [
  {
    role: 'ai',
    text: "Hi! I'm your AI Tutor. I've analyzed your quiz results and learning path. Ask me anything — what to study next, which resources to use, or how to improve your weak areas.",
    time: '09:41 AM',
  },
];

export const mockModernFeatures = [
  { name: 'Gradient Boosting', why: 'Strong on structured student data and excellent for ranking learning readiness.' },
  { name: 'Extra Trees', why: 'Fast ensemble baseline that handles mixed numeric and categorical learning signals well.' },
  { name: 'AutoML', why: 'Tries multiple models and selects the best one automatically for your dataset.' },
  { name: 'Hybrid Recommendation', why: 'Combines live YouTube API results with curated video and course datasets.' },
];
