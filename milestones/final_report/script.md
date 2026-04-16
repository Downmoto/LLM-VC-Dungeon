# presentation script — llm-vc-dungeon

**total target time: 10–15 minutes (including demo)**

---

## slide 1 — title slide
**speaker: mahboobeh** · *~30 sec*

> "Hi everyone — we're Team LLM-VC-Dungeon. I'm Mahboobeh, and with me today are Arad and Johnpaul. We built a natural language text adventure game powered by LLMs, and over the next 10 to 15 minutes we'll walk you through what that means, how it works, and show you a live demo."

---

## slide 2 — the problem
**speaker: mahboobeh** · *~1 min*

> "To understand what we built, you need to understand what we were replacing. Classic text adventure games have been around since the 70s — but every single one of them suffers from the same problem. They use rigid command parsers that only accept exact verb-noun syntax.

> If you type `examine chest`, that works. But if you type `look at the chest`, the game just says 'I don't understand that.' Same intent — completely different outcome. Players spend more time fighting the parser than actually playing the game. It breaks immersion constantly and it's a terrible user experience."

---

## slide 3 — our solution
**speaker: mahboobeh** · *~1 min*

> "Our solution was to throw away the parser entirely and replace it with natural language understanding. Instead of `get key`, you can say 'I grab whatever's on the ground.' Instead of `attack goblin`, you can say 'I swing my sword at the goblin.'
>
> Our original vision was actually voice-first — speak to the game and hear it respond. We pivoted to text input, but the classification problem that voice requires is exactly what we solved. The foundation is there. I'll hand it over to Arad now to walk through how we built it."

---

## slide 4 — system architecture
**speaker: arad** · *~1.5 min*

> "Thanks Mahboobeh. So architecturally, the system has two main pieces — a SvelteKit frontend that renders a terminal-style interface in the browser, and a FastAPI backend that runs all the game logic.
>
> Every time a player types something, it goes over HTTP to the backend. The backend classifies intent, runs the game engine, and optionally calls an LLM to generate the narrative response, then sends it all back.
>
> One of the most important design decisions we made was supporting three runtime modes. Programmatic mode makes zero LLM calls — it's fully deterministic. Hybrid mode uses a Python parser for obvious commands and only calls the LLM for ambiguous input. And strict LLM mode routes everything through the model. This means the game runs reliably even when there's no API key or network access."

---

## slide 5 — key technical decisions
**speaker: arad** · *~1.5 min*

> "Three decisions shaped the whole architecture.
>
> First — deterministic-first design. LLMs on the critical path fail in production. We learned that early. Latency of 800 to 1500 milliseconds per turn, quota exhaustion, inconsistent JSON output. So we built a Python parser that handles clear commands directly, and only fall back to the LLM when we actually need it.
>
> Second — hybrid dungeon generation. We have procedural biome tables for mines, crypts, arcane towers, and volcanic zones. Those guarantee a playable dungeon in any mode. A single LLM call on top of that adds thematic coherence. So even if the LLM is down, the dungeon still generates.
>
> Third — quota-aware throttling. We parse LLM error responses for retry delays. When a provider hits quota, we mark it unavailable for that window. The game degrades gracefully — it never crashes."

---

## slide 6 — live demo
**speaker: arad** · *~3–4 min*

> "Alright, let me show you the actual game."

*[open the app in the browser — the terminal interface should be visible]*

> "So this is the terminal interface. It's intentionally minimal — it looks like a classic dungeon crawler. Let me start a new game."

*[type a natural language command, e.g. `I want to look around`]*

> "Notice I didn't type `look` or `examine room` — I just described what I want to do. The intent classifier maps that to the correct game action, the engine updates state, and the LLM writes the narrative response."

*[move to another room, e.g. `let's head north` or `I go through the doorway`]*

> "I can phrase movement however I want. The parser handles the common cases, and the LLM handles anything ambiguous."

*[pick up an item or attack an enemy if present]*

> "Combat and item interaction work the same way."

*[show the map command if time allows]*

> "There's also an ASCII map of discovered rooms — pretty classic dungeon crawler feel. That's the full loop — explore, fight, collect, survive."

---

## slide 7 — testing & validation
**speaker: arad** · *~1 min*

> "On the testing side — we have 43 backend tests covering the most critical paths in the system.
>
> The intent tests validate parser correctness, fuzzy matching, and LLM retry fallback behavior. The game turn tests cover movement, combat, game over conditions, history truncation, and mode switching. The generator tests verify biome tables and difficulty scaling. And the API map tests check the endpoint contract and specifically test for path traversal prevention — a security concern we flagged early.
>
> All 43 pass clean."

---

## slide 8 — project evolution
**speaker: johnpaul** · *~1 min*

> "The project went through four milestones across the semester. We started in January with a voice-first concept and a dual-stack design — we even did a financial model projecting about $0.00063 per game turn.
>
> In February we added save and load, procedural generation, and Ollama support for local models. In March we introduced the GAME_MODE flag, rebuilt the parser, and added the biome tables along with the first test suite. And in the final milestone we containerized everything with Docker Compose, hardened the API, and got to 43 tests.
>
> Each milestone was a real evolution — the architecture changed significantly at each step."

---

## slide 9 — challenges & lessons learned
**speaker: johnpaul** · *~1 min*

> "A few honest lessons.
>
> The biggest one — LLMs on the critical path fail in production. That's not theoretical, we hit it. Quota exhaustion mid-demo, JSON responses that didn't parse, inconsistent behavior across providers. The programmatic mode exists because of that experience.
>
> The second lesson was state ownership. Early versions let the LLM describe state it didn't actually track. The engine would say one thing, the narrative would say another. We fixed that by making the engine the single source of truth — it owns all mutations, the LLM only narrates what it's told.
>
> And third — API contracts before parallel work. When Arad and I were working on backend and frontend simultaneously, silent breakage happened because shapes evolved independently. Writing the schema first would have saved us time."

---

## slide 10 — future work
**speaker: johnpaul** · *~45 sec*

> "A few concrete next steps. Voice input is the obvious one — the classification problem is solved, so voice is really just a frontend integration layer on the existing turn API. We'd also like Playwright end-to-end tests since the frontend has zero automated coverage right now. Streaming LLM responses via server-sent events would fit the terminal aesthetic really well. And building out a proper intent classification benchmark — we designed a 200 to 300 pair evaluation dataset in Milestone 1 but never built it. That would give us concrete accuracy numbers for the parser."

---

## slide 11 — conclusion
**speaker: mahboobeh** · *~45 sec*

> "So to wrap up — we set out to fix the syntax friction that makes text adventure interfaces feel like obstacles. What we built is a game engine where the parser is invisible and the story is the interface.
>
> The generalizable pattern we landed on is: deterministic core plus LLM enrichment layer equals a resilient AI-augmented system. The engine is correct by default. The LLM makes it richer when it can. The game never breaks when it can't.
>
> And the original voice vision is genuinely reachable from here — completing it is an integration milestone, not a research problem. Thank you."

---

## slide 12 — questions

---