# LLM-VC-Dungeon

a voice-first adventure game powered by large language models

## overview

traditional text adventures force players to memorize specific commands and syntax. this project eliminates that friction by letting you simply speak your intentions in natural language. an ai dungeon master translates your voice into game logic and responds with dynamic audio narration.

## architecture

dual-stack design supporting both cloud and self-hosted deployment:

**cloud stack** (saas deployment)
- stt: groq whisper-large-v3-turbo
- logic router: function-gemma-it (self-hosted)
- narrative: groq llama-3.3-70b
- tts: lemonfox.ai
- frontend: svelte 5 (vercel)
- backend: python fastapi (railway/render)

**self-hosted stack** (local docker)
- stt: faster-whisper
- logic: function-gemma-it (gguf)
- narrative: llama-3-8b-instruct (gguf)
- tts: piper tts
- all components run locally in a single container

## tech stack

- **frontend**: svelte 5 with typescript
- **backend**: python with fastapi
- **transport**: websockets for real-time audio streaming
- **models**: function gemma for intent classification, llama for narrative generation

## how it works

1. speak your command into the browser
2. audio transcribed to text (stt)
3. llm translates natural language to structured json function calls
4. game state updates based on the action
5. narrative llm generates story response
6. text converted to speech and played back

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