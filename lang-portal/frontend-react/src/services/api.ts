const API_BASE_URL = 'http://localhost:8000/api';

// Group types
export interface Group {
  id: number;
  group_name: string;
  description: string;
  word_count: number;
}

export interface GroupsResponse {
  groups: Group[];
  total_pages: number;
  current_page: number;
}

// Word types
export interface Word {
  id: number;
  french: string;
  english: string;
  gender: string;
  parts: string;
  correct_count?: number;
  wrong_count?: number;
}

export interface WordResponse {
  word: Word;
}

export interface WordsResponse {
  words: Word[];
  pagination: {
    current_page: number;
    total_pages: number;
    total_words: number;
    words_per_page: number;
  };
}

// Study Session types
export interface StudySession {
  id: number;
  group_id: number;
  group_name: string;
  activity_id: number;
  activity_name: string;
  start_time: string;
  end_time: string | null;
  review_items_count: number;
  correct_count: number;
}

export interface WordReview {
  word_id: number;
  is_correct: boolean;
}

// Dashboard types
export interface RecentSession {
  id: number;
  group_id: number;
  activity_name: string;
  created_at: string;
  correct_count: number;
  wrong_count: number;
}

export interface StudyStats {
  total_vocabulary: number;
  total_words_studied: number;
  mastered_words: number;
  success_rate: number;
  total_sessions: number;
  active_groups: number;
  current_streak: number;
}

// Group API
export const fetchGroups = async (
  page: number = 1,
  sortBy: string = 'name',
  order: 'asc' | 'desc' = 'asc'
): Promise<GroupsResponse> => {
  const response = await fetch(
    `/api/groups?page=${page}&sort_by=${sortBy}&order=${order}`
  );
  if (!response.ok) {
    throw new Error('Failed to fetch groups');
  }
  return response.json();
};

export interface GroupDetails {
  id: number;
  group_name: string;
  word_count: number;
}

export interface GroupWordsResponse {
  words: Word[];
  total_pages: number;
  current_page: number;
}

export const fetchGroupDetails = async (
  groupId: number,
  page: number = 1,
  sortBy: string = 'kanji',
  order: 'asc' | 'desc' = 'asc'
): Promise<GroupDetails> => {
  const response = await fetch(`/api/groups/${groupId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch group details');
  }
  return response.json();
};

export const fetchGroupWords = async (
  groupId: number,
  page: number = 1,
  sortBy: string = 'kanji',
  order: 'asc' | 'desc' = 'asc'
): Promise<GroupWordsResponse> => {
  const response = await fetch(
    `/api/groups/${groupId}/words?page=${page}&sort_by=${sortBy}&order=${order}`
  );
  if (!response.ok) {
    throw new Error('Failed to fetch group words');
  }
  return response.json();
};

// API functions for words
export async function fetchWords(
  page: number = 1,
  sortBy: string = 'french',
  order: 'asc' | 'desc' = 'asc'
): Promise<WordsResponse> {
  const response = await fetch(
    `/api/words?page=${page}&sort_by=${sortBy}&order=${order}`
  );
  if (!response.ok) {
    throw new Error('Failed to fetch words');
  }
  return response.json();
}

export async function fetchWordDetails(wordId: number): Promise<WordResponse> {
  const response = await fetch(`/api/words/${wordId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch word details');
  }
  return response.json();
}

export async function createWord(
  word: Omit<Word, 'id'>
): Promise<{ message: string; id: number }> {
  const response = await fetch('/api/words', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(word),
  });
  if (!response.ok) {
    throw new Error('Failed to create word');
  }
  return response.json();
}

// Study Session API
export async function createStudySession(
  groupId: number,
  studyActivityId: number
): Promise<{ session_id: number }> {
  const response = await fetch('/api/study-sessions', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      group_id: groupId,
      study_activity_id: studyActivityId,
    }),
  });
  if (!response.ok) {
    throw new Error('Failed to create study session');
  }
  return response.json();
}

export async function submitStudySessionReview(
  sessionId: number,
  reviews: WordReview[]
): Promise<void> {
  const response = await fetch(`/api/study-sessions/${sessionId}/review`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ reviews }),
  });
  if (!response.ok) {
    throw new Error('Failed to submit study session review');
  }
}

export interface StudySessionsResponse {
  study_sessions: StudySession[];
  total_pages: number;
  current_page: number;
}

export async function fetchStudySessions(
  page: number = 1,
  perPage: number = 10
): Promise<StudySessionsResponse> {
  const response = await fetch(
    `${API_BASE_URL}/study-sessions?page=${page}&per_page=${perPage}`
  );
  if (!response.ok) {
    throw new Error('Failed to fetch study sessions');
  }
  return response.json();
}

export async function fetchGroupStudySessions(
  groupId: number,
  page: number = 1,
  sortBy: string = 'created_at',
  order: 'asc' | 'desc' = 'desc'
): Promise<StudySessionsResponse> {
  const response = await fetch(
    `/api/groups/${groupId}/study-sessions?page=${page}&sort_by=${sortBy}&order=${order}`
  );
  if (!response.ok) {
    throw new Error('Failed to fetch group study sessions');
  }
  return response.json();
}

// Study Activities API
export interface StudyActivity {
  id: number;
  preview_url: string;
  title: string;
  launch_url: string;
}

export async function fetchStudyActivities(): Promise<StudyActivity[]> {
  const response = await fetch(`${API_BASE_URL}/study-activities`);
  if (!response.ok) {
    throw new Error('Failed to fetch study activities');
  }
  return response.json();
}

// Dashboard API
export async function fetchRecentStudySession(): Promise<RecentSession | null> {
  const response = await fetch('/api/dashboard/last-study-session');
  if (!response.ok) {
    throw new Error('Failed to fetch recent study session');
  }
  const data = await response.json();
  return data.session || null;
}

export async function fetchStudyStats(): Promise<StudyStats> {
  const response = await fetch('/api/dashboard/quick-stats');
  if (!response.ok) {
    throw new Error('Failed to fetch study stats');
  }
  return response.json();
}
