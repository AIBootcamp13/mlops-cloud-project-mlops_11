import axios from 'axios';

const API_ENDPOINT = process.env.REACT_APP_API_ENDPOINT || 'http://localhost:8000';

// API 클라이언트 설정
const apiClient = axios.create({
  baseURL: API_ENDPOINT,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  }
});

// 응답 인터셉터 (에러 처리)
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// ==========================================
// 추천 API
// ==========================================

export async function getRecommendContents(k = 10, userId = null) {
  try {
    console.log('API 호출:', API_ENDPOINT);
    
    // v1 API 우선 시도
    try {
      const response = await apiClient.get('/api/v1/recommendations', {
        params: {
          k: k,
          user_id: userId
        }
      });
      
      console.log('v1 API 응답:', response.data);
      return response.data.recommendations || [];
    } catch (v1Error) {
      console.warn('v1 API 실패, 레거시 API로 폴백:', v1Error.message);
      
      // 레거시 API로 폴백
      const response = await apiClient.get('/recommendations', {
        params: { k: k }
      });
      
      console.log('레거시 API 응답:', response.data);
      return response.data.recommended_content_id || [];
    }
    
  } catch (error) {
    console.error('모든 API 호출 실패:', error);
    return [];
  }
}

// ==========================================
// 영화 정보 API
// ==========================================

export async function getMovies(limit = 10, offset = 0) {
  try {
    const response = await apiClient.get('/api/v1/movies', {
      params: {
        limit: limit,
        offset: offset
      }
    });
    
    return {
      movies: response.data.movies || [],
      pagination: response.data.pagination || {}
    };
  } catch (error) {
    console.error('영화 목록 조회 실패:', error);
    return { movies: [], pagination: {} };
  }
}

export async function getMovieDetails(movieId) {
  try {
    const response = await apiClient.get(`/api/v1/movies/${movieId}`);
    return response.data;
  } catch (error) {
    console.error('영화 상세 정보 조회 실패:', error);
    return null;
  }
}

// ==========================================
// 피드백 API
// ==========================================

export async function submitFeedback(feedback) {
  try {
    const response = await apiClient.post('/api/v1/feedback', feedback);
    return response.data;
  } catch (error) {
    console.error('피드백 제출 실패:', error);
    throw error;
  }
}

export async function getUserFeedback(userId, limit = 10) {
  try {
    const response = await apiClient.get(`/api/v1/feedback/${userId}`, {
      params: { limit: limit }
    });
    return response.data;
  } catch (error) {
    console.error('사용자 피드백 조회 실패:', error);
    return { feedback_history: [] };
  }
}

// ==========================================
// 이벤트 추적 API
// ==========================================

export async function trackUserInteraction(interaction) {
  try {
    const response = await apiClient.post('/api/v1/events/user-interaction', {
      user_id: interaction.userId || 'anonymous',
      movie_id: interaction.movieId,
      interaction_type: interaction.type || 'view',
      session_id: interaction.sessionId || generateSessionId(),
      device_type: getDeviceType(),
      duration_seconds: interaction.duration,
      page_url: window.location.href,
      referrer: document.referrer,
      metadata: interaction.metadata || {}
    });
    
    return response.data;
  } catch (error) {
    console.warn('사용자 상호작용 추적 실패:', error);
    // 이벤트 추적 실패는 사용자 경험에 영향을 주지 않아야 함
  }
}

// ==========================================
// 시스템 정보 API
// ==========================================

export async function getSystemHealth() {
  try {
    const response = await apiClient.get('/health');
    return response.data;
  } catch (error) {
    console.error('시스템 상태 확인 실패:', error);
    return { status: 'unknown' };
  }
}

export async function getModelInfo() {
  try {
    const response = await apiClient.get('/api/v1/model/info');
    return response.data;
  } catch (error) {
    console.error('모델 정보 조회 실패:', error);
    return null;
  }
}

// ==========================================
// 유틸리티 함수들
// ==========================================

function generateSessionId() {
  return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
}

function getDeviceType() {
  const userAgent = navigator.userAgent.toLowerCase();
  if (/mobile|android|iphone|ipad|phone/i.test(userAgent)) {
    return 'mobile';
  } else if (/tablet|ipad/i.test(userAgent)) {
    return 'tablet';
  } else {
    return 'desktop';
  }
}

// ==========================================
// 고급 기능들
// ==========================================

export async function getPersonalizedRecommendations(userId, preferences = {}) {
  try {
    const response = await apiClient.get('/api/v1/recommendations', {
      params: {
        k: preferences.count || 10,
        user_id: userId,
        ...preferences
      }
    });
    
    // 사용자 상호작용 추적
    await trackUserInteraction({
      userId: userId,
      type: 'recommendation_request',
      metadata: { preferences }
    });
    
    return response.data.recommendations || [];
  } catch (error) {
    console.error('개인화 추천 실패:', error);
    return [];
  }
}

export async function rateMoive(userId, movieId, rating, sessionId = null) {
  try {
    // 평점 피드백 제출
    await submitFeedback({
      user_id: userId,
      movie_id: movieId,
      interaction_type: 'rating',
      rating: rating,
      session_id: sessionId || generateSessionId()
    });
    
    // 사용자 상호작용 추적
    await trackUserInteraction({
      userId: userId,
      movieId: movieId,
      type: 'rating',
      metadata: { rating }
    });
    
    return true;
  } catch (error) {
    console.error('영화 평점 제출 실패:', error);
    return false;
  }
}

// ==========================================
// 기존 호환성 유지 (레거시)
// ==========================================

// 기존 코드와의 호환성을 위해 유지
export { getRecommendContents as getRecommendations };
