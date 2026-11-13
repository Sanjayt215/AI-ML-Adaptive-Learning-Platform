import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import HomePage from './pages/HomePage';
import LearnHubPage from './pages/LearnHubPage';
import LearningPlanPage from './pages/LearningPlanPage';
import AssessmentsPage from './pages/AssessmentsPage';
import AITutorPage from './pages/AITutorPage';
import MyProgressPage from './pages/MyProgressPage';
import ResourcesPage from './pages/ResourcesPage';
import RLIntelligencePage from './pages/RLIntelligencePage';
import StartPage from './pages/StartPage';
import QuizPage from './pages/QuizPage';

export default function App() {
  return (
    <Router>
      <div className="min-h-screen bg-mesh grid-bg">
        <Routes>
          <Route path="/" element={<Layout />}>
            {/* Core 7-Hub Student-Centric Navigation */}
            <Route index element={<HomePage />} />
            <Route path="learn" element={<LearnHubPage />} />
            <Route path="learning-plan" element={<LearningPlanPage />} />
            <Route path="assessments" element={<AssessmentsPage />} />
            <Route path="ai-tutor" element={<AITutorPage />} />
            <Route path="my-progress" element={<MyProgressPage />} />
            <Route path="resources" element={<ResourcesPage />} />

            {/* Research Mode Dedicated Hub */}
            <Route path="research/rl-intelligence" element={<RLIntelligencePage />} />

            {/* Backward Compatibility Redirects & Mounts */}
            <Route path="goals" element={<Navigate to="/learning-plan" replace />} />
            <Route path="path" element={<Navigate to="/learning-plan" replace />} />
            <Route path="assessment" element={<Navigate to="/assessments" replace />} />
            <Route path="knowledge-intelligence" element={<Navigate to="/my-progress" replace />} />
            <Route path="dashboard" element={<Navigate to="/my-progress" replace />} />
            <Route path="mastery" element={<Navigate to="/my-progress" replace />} />
            <Route path="weak-topics" element={<Navigate to="/learn?mode=weak_topics" replace />} />
            <Route path="exam-prep" element={<Navigate to="/learn?mode=exam_prep" replace />} />
            <Route path="revision" element={<Navigate to="/learn?mode=revision" replace />} />
            <Route path="tutor" element={<Navigate to="/ai-tutor" replace />} />
            <Route path="rl-intelligence" element={<Navigate to="/research/rl-intelligence" replace />} />

            {/* Legacy Quiz Flow */}
            <Route path="start" element={<StartPage />} />
            <Route path="quiz" element={<QuizPage />} />

            {/* Catch-All */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </div>
    </Router>
  );
}
