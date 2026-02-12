// api client for fastapi backend
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// type definitions matching backend pydantic models
export interface GenerateTextRequest {
  prompt: string;
  system_prompt?: string;
}

export interface GenerateTextResponse {
  text: string;
}

export interface ClassifyIntentRequest {
  user_input: string;
}

export interface ClassifyIntentResponse {
  action: string;
  target: string;
  confidence: number;
}

export interface HealthResponse {
  status: string;
  ollama_url: string;
  ollama_model: string;
  endpoints: {
    generate: string;
    classify: string;
  };
}

export interface GameTurnRequest {
  user_input: string;
}

export interface GameTurnResponse {
  narrative: string;
  action?: Record<string, any>;
}

// api error class
export class ApiError extends Error {
  constructor(
    public status: number,
    public detail: string
  ) {
    super(`API Error (${status}): ${detail}`);
    this.name = 'ApiError';
  }
}

// base fetch wrapper with error handling
async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new ApiError(response.status, errorData.detail || response.statusText);
    }

    return await response.json();
  } catch (error) {
    if (error instanceof ApiError) {
      throw error;
    }
    throw new Error(`Network error: ${error instanceof Error ? error.message : 'Unknown error'}`);
  }
}

// api client methods
export const apiClient = {
  // health check
  async healthCheck(): Promise<HealthResponse> {
    return apiFetch<HealthResponse>('/');
  },

  // generate narrative text
  async generateText(request: GenerateTextRequest): Promise<GenerateTextResponse> {
    return apiFetch<GenerateTextResponse>('/api/generate', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // classify user intent
  async classifyIntent(request: ClassifyIntentRequest): Promise<ClassifyIntentResponse> {
    return apiFetch<ClassifyIntentResponse>('/api/classify', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // process game turn
  async processGameTurn(request: GameTurnRequest): Promise<GameTurnResponse> {
    return apiFetch<GameTurnResponse>('/api/game/turn', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },
};
