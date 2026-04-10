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

```bash
# backend
cd src/api
pip install -r requirements.txt
uvicorn app.main:app --reload

# frontend
cd src/svelte
npm install
npm run dev
```

## team

- arad fadaei
- mahboobeh yasini
- johnpaul tamburro