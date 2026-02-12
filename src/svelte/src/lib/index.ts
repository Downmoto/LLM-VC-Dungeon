// place files you want to import through the `$lib` alias in this folder.

// export api client
export { apiClient, ApiError } from './api/client';
export type { 
  GenerateTextRequest, 
  GenerateTextResponse, 
  ClassifyIntentRequest, 
  ClassifyIntentResponse,
  HealthResponse,
  GameTurnRequest,
  GameTurnResponse
} from './api/client';

// export components
export { default as ApiStatus } from './components/ApiStatus.svelte';
export { default as TextGenerator } from './components/TextGenerator.svelte';
export { default as IntentClassifier } from './components/IntentClassifier.svelte';
export { default as GameTurn } from './components/GameTurn.svelte';
