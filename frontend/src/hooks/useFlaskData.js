
import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  mockAssessment, mockProfile, mockModelScores,
  mockAccuracyTrend, mockLearningPath,
  mockResources, mockChatHistory, mockModernFeatures,
} from '../utils/mockData';
import { apiFetch } from '../utils/api';

const STORAGE_KEY = 'autolearn_context_v2';

const fallbackState = {
  assessment: [],
  profile: null,
  modelScores: [],
  dataInfo: { rows: 0, real_data_used: false },
  learningPath: [],
  resources: [],
  quizItems: [],
  modernFeatures: [],
  modelName: '',
  automlEngine: '',
  youtubeLive: false,
  notifications: [],
  learningScore: 0,
  pathProgress: {},
};

function loadStored() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

export function useFlaskData() {
  const [state, setState] = useState({ ...fallbackState, ...loadStored() });
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiFetch('/api/context');
      setState(prev => {
        const next = { ...prev, ...data };
        sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next));
        return next;
      });
      return data;
    } catch {
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const savePartial = useCallback((partial) => {
    setState(prev => {
      const next = { ...prev, ...partial };
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      return next;
    });
  }, []);

  return useMemo(() => {
    const avgScore = state.assessment.length
      ? Math.round((state.assessment.reduce((s, r) => s + r.score_pct, 0) / state.assessment.length) * 10) / 10
      : 0;
    const strengths = state.assessment.filter(r => r.score_pct >= 75).map(r => r.topic);
    const weakTopics = state.assessment.filter(r => r.score_pct < 45).map(r => r.topic);
    const accuracyTrend = mockAccuracyTrend;
    const topicMastery = state.assessment.map(r => ({
      topic: r.topic.length > 8 ? r.topic.slice(0, 8) + '.' : r.topic,
      mastery: r.score_pct,
    }));
    return {
      ...state,
      avgScore,
      strengths,
      weakTopics,
      accuracyTrend,
      topicMastery,
      chatHistory: mockChatHistory,
      loading,
      refresh,
      savePartial,
    };
  }, [state, loading, refresh, savePartial]);
}
