
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
  bktMastery: null,
};

function loadStored() {
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function normalizeResource(resource = {}) {
  if (!resource || typeof resource !== 'object') {
    return {
      topic: 'Unknown',
      level: 'beginner',
      videos: [],
      courses: [],
      datasets: [],
      project: 'Practice a small project on this topic.',
    };
  }

  return {
    ...resource,
    topic: resource.topic || 'Unknown',
    level: resource.level || 'beginner',
    project: typeof resource.project === 'string'
      ? resource.project
      : (resource.project?.project || 'Practice a small project on this topic.'),
    videos: (resource.videos || []).map(video => ({
      ...video,
      title: video.title || 'Untitled Video',
      channel: video.channel || 'Unknown Channel',
      url: video.url || '#',
      level: video.level || 'beginner',
    })),
    courses: (resource.courses || []).map(course => ({
      ...course,
      title: course.title || 'Untitled Course',
      provider: course.provider || course.platform || 'Unknown Provider',
      url: course.url || '#',
      level: course.level || 'beginner',
    })),
    datasets: (resource.datasets || []).map(dataset => ({
      ...dataset,
      title: dataset.title || 'Untitled Dataset',
      source: dataset.source || 'Unknown Source',
      url: dataset.url || '#',
      level: dataset.level || 'beginner',
    })),
  };
}

function normalizeState(state = {}) {
  const normalized = { ...state };
  if ('assessment' in state) {
    normalized.assessment = Array.isArray(state.assessment) ? state.assessment : [];
  }
  if ('resources' in state) {
    normalized.resources = Array.isArray(state.resources) ? state.resources.map(normalizeResource) : [];
  }
  if ('quizItems' in state) {
    normalized.quizItems = Array.isArray(state.quizItems) ? state.quizItems : [];
  }
  if ('learningPath' in state) {
    normalized.learningPath = Array.isArray(state.learningPath) ? state.learningPath : [];
  }
  if ('notifications' in state) {
    normalized.notifications = Array.isArray(state.notifications) ? state.notifications : [];
  }
  if ('pathProgress' in state) {
    normalized.pathProgress = state.pathProgress || {};
  }
  if ('dataInfo' in state) {
    normalized.dataInfo = state.dataInfo || { rows: 0, real_data_used: false };
  }
  return normalized;
}

export function useFlaskData() {
  const [state, setState] = useState(normalizeState({ ...fallbackState, ...loadStored() }));
  const [loading, setLoading] = useState(false);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const data = normalizeState(await apiFetch('/api/context'));
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
    const normalizedPartial = normalizeState(partial);
    setState(prev => {
      const next = { ...prev, ...normalizedPartial };
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
