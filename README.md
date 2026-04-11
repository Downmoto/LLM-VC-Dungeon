# LLM-VC-Dungeon

a web-based adventure game with a terminal-styled frontend powered by large language models

## overview

traditional text adventures force players to memorize specific commands and syntax. this project reduces that friction by allowing natural-language text input and translating it into structured game logic. an ai dungeon master layer interprets intent and produces narrative responses while deterministic backend rules preserve state consistency.

## architecture

current implementation focuses on a frontend/backend split:

- frontend: svelte 5 web ui with a terminal-styled interface
- backend: python fastapi game orchestration
- llm integration: local ollama-backed classification and generation flows
- persistence: json save/load game state

## tech stack

- **frontend**: svelte 5 with typescript
- **backend**: python with fastapi
- **transport**: http json api
- **models**: ollama-hosted models for intent classification and narrative generation

## how it works

1. enter a natural-language command in the web ui (terminal-styled interface)
2. llm classifies intent into structured game actions
3. backend updates deterministic game state
4. narrative llm generates a contextual story response
5. updated state is persisted for continued play

## scope note

voice input/output was explored in early planning milestones but is currently de-scoped and not supported in the active implementation.

## development

### docker single-launch (recommended for mvp)

```bash
cp .env.example .env
docker compose up --build
```

services:

- frontend: http://localhost:3000
- backend: http://localhost:8000

healthcheck notes:

- backend health endpoint: / on port 8000
- frontend health endpoint: / on port 3000

optional local ollama profile:

```bash
docker compose --profile with-ollama up --build
```

### local non-docker

```bash
# backend
cd src/api
cp ../../.env.example .env
pip install -r requirements.txt
uvicorn app.main:app --reload

# frontend
cd src/svelte
npm install
npm run dev
```

## backend environment

- backend reads settings from src/api/.env
- do not commit real api keys
- llm mode is strict: if provider credentials or model access are invalid, new game creation fails instead of falling back to programmatic generation

required provider variables:

- for google: LLM_PROVIDER=google and GOOGLE_API_KEY
- for openai: LLM_PROVIDER=openai and OPENAI_API_KEY
- for ollama: LLM_PROVIDER=ollama and a running ollama server

additional runtime controls:

- HISTORY_RECENT_TURNS controls how many latest action/result entries are passed directly to llm context
- HISTORY_SUMMARY_MAX_CHARS caps the rolling summary text length used for older turns

save/load path policy:

- api save and load paths are restricted to the backend data directory
- use relative names like savegame.json or nested paths under data/

## team

- arad fadaei
- mahboobeh yasini
- johnpaul tamburro