// api client for fastapi backend
export const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
  llm_model: string;
  endpoints: {
    generate: string;
    classify: string;
  };
}

export interface GameTurnRequest {
  user_input: string;
}

export interface GameTurnAction {
  action?: string;
  target?: string;
  direction?: string;
  game_over?: boolean;
  [key: string]: any;
}

export interface GameTurnState {
  current_room_id: string;
  player_hp: number;
  player_max_hp: number;
  inventory_size: number;
  history_size: number;
}

export interface GameTurnResponse {
  narrative: string;
  action?: GameTurnAction;
  state?: GameTurnState;
}

export interface NewGameRequest {
  save_path?: string;
}

export interface NewGameResponse {
  message: string;
  game_id: string;
  initial_room: string;
}

export interface LoadGameRequest {
  save_path?: string;
}

export interface LoadGameResponse {
  message: string;
  game_id: string;
  current_room: string;
}

export interface MapRoomResponse {
  id: string;
  exits: Record<string, string>;
  is_generated: boolean;
  is_visited: boolean;
}

export interface GameMapResponse {
  theme: string;
  current_room_id: string;
  rooms: MapRoomResponse[];
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
  const hasBody = options?.body !== undefined && options?.body !== null;
  const mergedHeaders: Record<string, string> = {
    ...(options?.headers as Record<string, string> | undefined),
  };
  if (hasBody && !mergedHeaders['Content-Type']) {
    mergedHeaders['Content-Type'] = 'application/json';
  }
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: mergedHeaders,
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

  // start a new game
  async newGame(request: NewGameRequest = {}): Promise<NewGameResponse> {
    return apiFetch<NewGameResponse>('/api/new-game', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  async loadGame(request: LoadGameRequest = {}): Promise<LoadGameResponse> {
    return apiFetch<LoadGameResponse>('/api/load-game', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  },

  // fetch current dungeon map graph
  async getGameMap(): Promise<GameMapResponse> {
    return apiFetch<GameMapResponse>('/api/game/map');
  },
};
