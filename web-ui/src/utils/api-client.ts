/**
 * API Client for Backend Integration
 * Handles all communication with the Daemonium FastAPI backend
 */

export interface ApiResponse<T = any> {
  data?: T;
  error?: string;
  status: number;
}

export interface PaginatedResponse<T> {
  data: T[];
  pagination: {
    page: number;
    limit: number;
    total: number;
    pages: number;
  };
}

class ApiClient {
  private baseUrl: string;

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_BACKEND_API_URL || 'http://localhost:8000';
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const url = `${this.baseUrl}${endpoint}`;
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      const data = await response.json();

      if (!response.ok) {
        return {
          error: data.error || `HTTP ${response.status}`,
          status: response.status,
        };
      }

      return {
        data,
        status: response.status,
      };
    } catch (error) {
      return {
        error: error instanceof Error ? error.message : 'Network error',
        status: 0,
      };
    }
  }

  // Philosophers API
  async getPhilosophers(params?: {
    page?: number;
    limit?: number;
    era?: string;
    school?: string;
    search?: string;
    is_active_chat?: number;
  }): Promise<ApiResponse<PaginatedResponse<any>>> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    return this.request(`/api/v1/philosophers/?${searchParams.toString()}`);
  }

  async getPhilosopher(name: string): Promise<ApiResponse<any>> {
    return this.request(`/api/v1/philosophers/${encodeURIComponent(name)}`);
  }

  async getPhilosopherWithSchool(name: string): Promise<ApiResponse<any>> {
    return this.request(`/api/v1/philosophers/${encodeURIComponent(name)}/with-school`);
  }

  async getRelatedPhilosophers(name: string, params?: {
    is_active_chat?: number;
  }): Promise<ApiResponse<any>> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    return this.request(`/api/v1/philosophers/${encodeURIComponent(name)}/related?${searchParams.toString()}`);
  }

  // Chat API
  async getChatBlueprints(): Promise<ApiResponse<any[]>> {
    return this.request('/api/v1/chat/blueprints');
  }

  async getPhilosopherBots(): Promise<ApiResponse<any[]>> {
    return this.request('/api/v1/chat/philosopher-bots');
  }

  async getAvailablePhilosophers(): Promise<ApiResponse<any[]>> {
    return this.request('/api/v1/chat/available-philosophers');
  }

  async getPhilosopherPersonality(philosopher: string): Promise<ApiResponse<any>> {
    return this.request(`/api/v1/chat/personality/${encodeURIComponent(philosopher)}`);
  }

  async getConversationStarters(philosopher: string): Promise<ApiResponse<any>> {
    return this.request(`/api/v1/chat/conversation-starters/${encodeURIComponent(philosopher)}`);
  }

  // Search API
  async globalSearch(query: string, collections?: string[]): Promise<ApiResponse<any>> {
    const searchParams = new URLSearchParams({ query });
    if (collections) {
      collections.forEach(collection => searchParams.append('collections', collection));
    }
    
    return this.request(`/api/v1/search/global?${searchParams.toString()}`);
  }

  async searchPhilosophers(query: string, params?: {
    is_active_chat?: number;
  }): Promise<ApiResponse<any>> {
    const searchParams = new URLSearchParams({ query });
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    return this.request(`/api/v1/search/philosophers?${searchParams.toString()}`);
  }

  async getSearchSuggestions(query: string): Promise<ApiResponse<any>> {
    return this.request(`/api/v1/search/suggestions?query=${encodeURIComponent(query)}`);
  }

  // Books API
  async getBooks(params?: {
    page?: number;
    limit?: number;
    author?: string;
  }): Promise<ApiResponse<PaginatedResponse<any>>> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    return this.request(`/api/v1/books/?${searchParams.toString()}`);
  }

  async getBookSummaries(params?: {
    author?: string;
  }): Promise<ApiResponse<any[]>> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    return this.request(`/api/v1/books/summaries?${searchParams.toString()}`);
  }

  // Aphorisms API
  async getAphorisms(): Promise<ApiResponse<any[]>> {
    return this.request('/api/v1/aphorisms/');
  }

  async getRandomAphorisms(count: number = 5): Promise<ApiResponse<any[]>> {
    return this.request(`/api/v1/aphorisms/random?count=${count}`);
  }

  // Ideas API
  async getTopIdeas(): Promise<ApiResponse<any[]>> {
    return this.request('/api/v1/ideas/top-ten');
  }

  async getIdeaSummaries(): Promise<ApiResponse<any[]>> {
    return this.request('/api/v1/ideas/summaries');
  }

  // Philosophy Schools API
  async getPhilosophySchools(params?: {
    page?: number;
    limit?: number;
  }): Promise<ApiResponse<PaginatedResponse<any>>> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    return this.request(`/api/v1/philosophy-schools/?${searchParams.toString()}`);
  }

  async getPhilosophySchool(schoolId: string): Promise<ApiResponse<any>> {
    return this.request(`/api/v1/philosophy-schools/${schoolId}`);
  }

  async getPhilosophersBySchool(schoolId: string, params?: {
    is_active_chat?: number;
  }): Promise<ApiResponse<any[]>> {
    const searchParams = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) {
          searchParams.append(key, value.toString());
        }
      });
    }
    
    return this.request(`/api/v1/philosophy-schools/${schoolId}/philosophers?${searchParams.toString()}`);
  }

  // Health check
  async healthCheck(): Promise<ApiResponse<any>> {
    return this.request('/health');
  }
}

// Export singleton instance
export const apiClient = new ApiClient();

// Export class for testing
export { ApiClient };
