# presentation script — llm-vc-dungeon

**total target time: 10–15 minutes (including demo)**

---

## slide 1 — title slide
**speaker: mahboobeh** · *~30 sec*

> "Hi everyone, we're Team LLM-VC-Dungeon. I'm Mahboobeh, and with me today are Arad and Johnpaul. We built a natural language text adventure game powered by LLMs, and over the next 10 to 15 minutes we'll walk you through what that means, how it works, and show you a live demo."

---

## slide 2 — the problem
**speaker: mahboobeh** · *~1 min*

> "To understand what we built, you need to understand what we were replacing. Classic text adventure games have been around since the 70s, but every single one of them suffers from the same problem. They use rigid command parsers that only accept exact verb-noun syntax.
>
> If you type `examine chest`, that works. But if you type `look at the chest`, the game responds with something like: 'I don't understand that.' Same intent, but completely different outcome. Players spend a ton of time fighting the parser than actually playing the game. It breaks immersion constantly and it's a terrible user experience."

---

## slide 3 — our solution
**speaker: mahboobeh** · *~1 min*

> "Our solution was to throw away the classic parser and replace it with a natural language parser. Instead of `get key`, you can say 'I grab whatever's on the ground.' Instead of `attack goblin`, you can say 'I swing my sword at the goblin.'
>
> Our original vision was actually voice-first where we would speak to the game and hear it respond. We pivoted to text input, but the classification slash tooling problem that voice input would benifit from is what we created. In other words, the foundation is there. I'll hand it over to Arad now to walk through how we built it."

---

## slide 4 — system architecture
**speaker: arad** · *~1.5 min*

> "Thanks Mahboobeh. So architecturally, the system has two main pieces: a SvelteKit frontend that renders a terminal-style interface in the browser, and a FastAPI backend that runs all the game logic.
>
> Every time a player types something, it goes over HTTP to the backend. The backend classifies intent, runs appropriate tools, runs the game engine, and calls an LLM to generate the narrative response, then sends it all back.
>
> One of the most important design decisions we made was supporting three runtime modes. Programmatic mode makes zero LLM calls as it's fully deterministic. Hybrid mode uses a Python parser for obvious commands and only calls the LLM for ambiguous input. And strict LLM mode routes everything through the models. This means the game should run reliably even when there's no API key or network access although it falls back to no narrative prose, so its not exactly interesting."

---

## slide 5 — key technical decisions
**speaker: arad** · *~1.5 min*

> "Three decisions shaped the whole architecture.
>
> First — deterministic-first design. LLMs on the critical path can fail in production. We learned that early. Latency of 800 to 1500 milliseconds per turn, quota exhaustion, inconsistent JSON output. So we built a Python parser that handles clear commands directly, and only fall back to the LLM when we actually need it.
>
> Second — hybrid dungeon generation. We have procedural biome tables for mines, crypts, arcane towers, and volcanic zones. Those guarantee a playable dungeon in any mode. A single LLM call on top of that adds thematic coherence. So even if the LLM is down, the dungeon still generates.
>
> Third — quota-aware throttling. We parse LLM error responses for retry delays. When a provider hits quota, we mark it unavailable for that window. The game degrades gracefully so it never crashes."

---

## slide 6 — live demo
**speaker: arad** · *~3–4 min*

---

## slide 7 — game engine & state model
**speaker: arad** · *~1.5 min*

> "Let me go one level deeper into how the backend actually works. Every player input flows into a single function called `process_turn` in `game.py`. It takes the raw input string and the current game state, it runs everything, and it returns a complete turn response. That's the whole contract.
>
> Inside that function, each action type has its own execution path. Movement validates that the exit actually exists and triggers background generation of neighboring rooms so they're ready before the player gets there. Combat uses deterministic damage math s enemies with low HP go down in one hit, stronger enemies take random damage in a band, and if player HP hits zero the `game_over` flag gets set. Item pickup uses token-overlap scoring to match what the player typed against the actual item names in the room, which is what lets 'grab the glowing thing' work.
>
> The state itself is a hierarchy of Pydantic models — `GameState` at the root, holding `PlayerState` and a dictionary of rooms. Every room, enemy, and item has an `extra_info` dictionary. That's the persistent fact cache. When a player asks about something for the first time, we call the LLM and store the answer there. Every subsequent ask just returns the cached value with no LLM call.
>
> History is bounded: we keep the last eight turns in full and roll older turns into a 700-character rolling summary that goes to the LLM as context. So the context window never grows unboundedly regardless of session length."

---

## slide 8 — intent classification — dual path
**speaker: arad** · *~1.5 min*

> "The intent classifier is what maps natural language to those game actions. And we built two completely independent paths that both produce the same output schema — an action and an optional target.
>
> The programmatic parser runs first in hybrid mode. It lowercases and strips punctuation, tokenizes, then matches against a known set of verb roots. Direction words go through an alias lookup table — so 'left' maps to west, 'ahead' maps to north, and so on. For actions that need a target, it scores entity candidates from the current room using token overlap with whatever's left after removing stopwords. Highest score above a threshold wins.
>
> The LLM path uses LangChain's tool-binding interface. Each supported action is a `@tool`-decorated function. The model receives the player input and the current room context, and it selects the right tool call, returning structured JSON directly. If the model produces malformed output it retries up to three times before falling back to the `unknown` action.
>
> In hybrid mode, the parser runs first. The classifier model is only invoked when the parser returns `unknown`,  which in practice means genuinely ambiguous or complex phrasing. Common commands never touch the classifier model."

---

## slide 9 — dungeon generation
**speaker: arad** · *~1 min*

> "Dungeon generation has three pieces working together. The topology is always generated the same way: BFS on a 2D grid, 10 rooms, always with symmetric exits, so if there's a north exit out of a room, there's a south exit back. This gives you branching paths and dead ends without any planning algorithm.
>
> On top of that topology, we have two content paths. If an LLM is available, we issue a single prompt asking for all 10 rooms at once. That single-call approach is intentional — it means the LLM can produce thematically coherent content across the whole dungeon rather than generating each room in isolation. We validate the response against the schema and retry up to three times if it's malformed.
>
> The programmatic path infers a biome from the theme string and populates rooms from content tables — mines, crypts, arcane towers, volcanic zones, each with their own descriptors, items, and enemy types. Room difficulty scales with room index so earlier rooms are lighter and later rooms are harder.
>
> The last piece is incremental expansion. When a player enters an unvisited room, we use FastAPI's `BackgroundTasks` to populate that room and its neighbors without blocking the turn response. The next rooms are always ready before the player reaches them."

---

## slide 10 — testing & validation
**speaker: johnpaul** · *~1 min*

> "On the testing side,  we have 43 backend tests covering the most critical paths in the system.
>
> The intent tests validate parser correctness, fuzzy matching, and LLM retry fallback behavior. The game turn tests cover movement, combat, game over conditions, history truncation, and mode switching. The generator tests verify biome tables and difficulty scaling. And the API map tests check the endpoint contract and specifically test for path traversal prevention which was a security concern we flagged early.
>
> All 43 pass clean."

---

## slide 11 — project evolution
**speaker: johnpaul** · *~1 min*

> "The project went through four milestones across the semester. We started in January with a voice-first concept and a dual-stack design. We even did a financial model projecting about $0.00063 per game turn.
>
> In February we added save and load, procedural generation, and Ollama support for local models. In March we introduced the GAME_MODE flag, rebuilt the parser, and added the biome tables along with the first test suite. And in the final milestone we containerized everything with Docker Compose, hardened the API, and got to 43 tests.
>
> Each milestone was a real evolution that had the architecture change significantly at each step."

---

## slide 12 — challenges & lessons learned
**speaker: johnpaul** · *~1 min*

> "A few honest lessons.
>
> The biggest one: LLMs on the critical path can fail in production. That's not theoretical, we hit it. Quota exhaustion mid testing, JSON responses that didn't parse, inconsistent behavior across providers. The programmatic mode exists because of that experience.
>
> The second lesson was state ownership. Early versions let the LLM describe state it didn't actually track. The engine would say one thing, the narrative would say another. We fixed that by making the engine the single source of truth as it owns all mutations, the LLM only narrates what it's told.
>
> And third, API contracts before parallel work. When we were working on backend and frontend simultaneously, silent breakage happened because shapes evolved independently. Writing the schema first would have saved us time."

---

## slide 13 — future work
**speaker: mahboobeh** · *~45 sec*

> "A few concrete next steps. Voice input is the obvious one as the classification problem is solved, so voice is really just a frontend integration layer on the existing turn API. We'd also like Playwright end-to-end tests since the frontend has zero automated coverage right now. Streaming LLM responses via server-sent events would fit the terminal aesthetic really well. And building out a proper intent classification benchmark, something we designed as a 200 to 300 pair evaluation dataset in Milestone 1 but never built it. That would give us concrete accuracy numbers for the parser."

---

## slide 14 — conclusion
**speaker: mahboobeh** · *~45 sec*

> "So to wrap up, we set out to fix the syntax friction that makes text adventure interfaces feel like obstacles. What we built is a game engine where the parser is invisible and the story is the interface.
>
> The generalizable pattern we landed on is: deterministic core plus LLM enrichment layer equals a resilient AI-augmented system. The engine is correct by default. The LLM makes it richer when it can. The game never breaks when it can't.
>
> And the original voice vision is genuinely reachable from here and completing it is an integration milestone, not a research problem. Thank you."

---

## slide 15 — questions

---