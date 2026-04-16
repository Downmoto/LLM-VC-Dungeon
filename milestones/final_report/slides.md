---
marp: true
theme: default
paginate: true
style: |
  section {
    font-family: 'Segoe UI', sans-serif;
    background: #0d0d0d;
    color: #e0e0e0;
  }
  h1 {
    color: #00ff88;
    font-size: 2rem;
    border-bottom: 2px solid #00ff88;
    padding-bottom: 0.25em;
  }
  h2 {
    color: #00cc66;
    font-size: 1.5rem;
  }
  h3 {
    color: #00aa55;
  }
  strong {
    color: #00ff88;
  }
  table {
    font-size: 0.85rem;
    width: 100%;
    border-collapse: collapse;
  }
  th {
    background: #1a1a1a;
    color: #00ff88;
    padding: 0.4em 0.8em;
    border: 1px solid #333;
  }
  td {
    padding: 0.4em 0.8em;
    border: 1px solid #333;
    background: #111;
  }
  code {
    background: #1a1a1a;
    color: #00ff88;
    padding: 0.1em 0.4em;
    border-radius: 3px;
    font-size: 0.9em;
  }
  pre {
    background: #1a1a1a;
    color: #00ff88;
    padding: 0.5em 0.8em;
    border-radius: 6px;
    border-left: 3px solid #00ff88;
    font-size: 0.8em;
  }
  ul, ol {
    line-height: 1.5;
  }
  li {
    margin: 0.1em 0;
  }
  .columns {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2em;
  }
  footer {
    color: #444;
    font-size: 0.75rem;
  }
  section.title-slide h1 {
    font-size: 2.8rem;
    border: none;
    text-align: center;
    margin-top: 0.5em;
  }
  section.title-slide p {
    text-align: center;
    color: #888;
  }
  section.title-slide h3 {
    text-align: center;
    color: #555;
    font-weight: normal;
  }
  section.demo-slide {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    text-align: center;
  }
  section.demo-slide h1 {
    font-size: 3.5rem;
    border: none;
  }
  section.demo-slide p {
    color: #888;
    font-size: 1.1rem;
  }
  section.impl-slide {
    font-size: 1.05rem;
    padding: 2rem 2.5rem;
  }
  section.impl-slide h1 {
    font-size: 2rem;
    margin-bottom: 0.6em;
  }
  section.impl-slide .columns {
    gap: 2em;
    margin: 1em 0;
  }
  section.impl-slide ul, section.impl-slide ol {
    line-height: 1.8;
    padding-left: 1.4em;
  }
  section.impl-slide li {
    margin: 0.25em 0;
  }
  section.impl-slide p {
    margin: 0.7em 0;
  }
  section.impl-slide strong {
    font-size: 1.05em;
  }
  .tag {
    display: inline-block;
    background: #1a1a1a;
    border: 1px solid #00ff88;
    color: #00ff88;
    padding: 0.15em 0.6em;
    border-radius: 4px;
    font-size: 0.85em;
    margin: 0.15em;
  }
---

<!-- _class: title-slide -->

# LLM-VC-Dungeon

### An AI-Powered Natural Language Text Adventure

<br>

**Arad Fadaei · Mahboobeh Yasini · Johnpaul Tamburro**

April 10, 2026

---

# The Problem

Traditional text adventure parsers demand **exact syntax**

```
> examine chest      ✓  accepted
> look at the chest  ✗  "I don't understand that."
> open chest         ✓  accepted
> try to open it     ✗  "I don't understand that."
```

<br>

- Players must **memorize vocabulary** rather than play
- **One wrong word** breaks immersion entirely

---

# Our Solution

Replace the rigid parser with **natural language understanding**

<div class="columns">

**Then**
- `look north`
- `get key`
- `attack goblin`

**Now**
- *"I want to scout what's ahead"*
- *"I grab whatever's on the ground"*
- *"I swing my sword at the goblin"*

</div>

**Original goal:** voice-first, speak to the game and hear it respond
**Delivered:** text natural language, the classification problem solved

---

# System Architecture

```
┌─────────────────────┐         ┌──────────────────────────┐
│   Browser Terminal  │  HTTP   │      FastAPI Backend      │
│   (SvelteKit)       │ ──────► │  Intent → Logic → Narrate │
│                     │ ◄────── │                           │
└─────────────────────┘         └──────────┬───────────────┘
                                            │
                          ┌─────────────────┼──────────────┐
                          │                 │              │
                    OpenAI/Gemini        Ollama      (none — programmatic)
```

**Three runtime modes**

| Mode | Behaviour |
|------|-----------|
| `programmatic` | zero LLM calls — fully deterministic |
| `hybrid` | parser first → LLM only for ambiguous input |
| `llm` | LLM on every turn, fails loud if unavailable |

---

# Key Technical Decisions

**1 — Deterministic-first design**
LLMs on the critical path are unreliable (latency, quota, bad JSON).
A Python parser handles obvious input, LLM parses ambiguous input. LLM is also an enrichment layer narrativly;

**2 — Hybrid dungeon generation**
Procedural biome tables (mine / crypt / arcane / volcanic) guarantee a playable dungeon in any mode.
LLM single-call generation adds thematic coherence.

**3 — Quota-aware LLM throttling**
Error messages are parsed for retry delays. When quota is hit, the provider is marked unavailable for that window, the game never crashes, it degrades.

---

<!-- _class: demo-slide -->

# `> _`

## Live Demo

*explore*

---

<!-- _class: impl-slide -->

# Game Engine & State Model

`process_turn(input, state) → TurnResponse` — the single entry point

<div class="columns">
<div>

**Action execution**

- **Move** — validate exit, update room, trigger background gen
- **Look** — return description + visible entities
- **Take** — token-overlap match against room items
- **Attack** — damage calc; enemies retaliate; HP=0 sets `game_over`
- **Query** — check `extra_info` cache → LLM on miss, store result

</div>
<div>

**State model (Pydantic)**

- `GameState` → `PlayerState` + `Room[]`
- `Room` / `Enemy` / `Item` each carry `extra_info: dict`
- `extra_info` is the **persistent fact cache** — LLM answers stored on first query, returned instantly on repeat
- History: last **8 turns** full + rolling **700-char summary**

</div>
</div>

---

<!-- _class: impl-slide -->

# Intent Classification — Dual Path

Both paths emit the same structured schema: `{ action, target }`

<div class="columns">
<div>

**Programmatic parser**

1. Lowercase + strip punctuation
2. Match verb roots against known set
3. Extract direction via alias table (`"left"` → `west`)
4. Score entity candidates by token overlap
5. No match → `unknown` action

</div>
<div>

**Classifier tool-binding**

1. Each action is a `@tool`-decorated function
2. Model receives input + room context
3. Selects the correct tool → structured JSON
4. Retry up to 3× on malformed output
5. Falls back to `unknown` on persistent failure

</div>
</div>

**Hybrid mode:** parser runs first — LLM is invoked only when the parser returns `unknown`

---

<!-- _class: impl-slide -->

# Dungeon Generation

**Topology** — BFS on a 2D grid, 10-room connected graph, always bidirectional exits

<div class="columns">
<div>

**LLM path** *(when available)*

- Single prompt → all 10 rooms in one call
- Validated against schema; up to 3 retries
- Thematic coherence across the whole dungeon

</div>
<div>

**Programmatic path** *(always available)*

- Biome inferred from theme string
- Content tables per biome: mine · crypt · arcane · volcanic
- Difficulty scales with room index: later rooms → higher enemy HP band

</div>
</div>

**Incremental expansion** — when a player enters an unvisited room, `BackgroundTasks` populates that room and its unvisited neighbors without blocking the turn response

---

# Testing & Validation

43 backend tests covering all the important bits!
<br>
| Module | Tests | Coverage focus |
|--------|------:|----------------|
| `test_intent.py` | 14 | parser correctness, fuzzy match, LLM retry fallback |
| `test_game_turns.py` | 18 | move, combat, game-over, history truncation, fallback modes |
| `test_generator_programmatic.py` | 6 | biome tables, difficulty scaling, full dungeon roundtrip |
| `test_api_map.py` | 5 | map endpoint contract, **path traversal prevention** |

---

# Project Evolution
<br>

| | Milestone 1 · Jan | Milestone 2 · Feb | Milestone 3 · Mar | Milestone 4 · Mar |
|-|-------------------|-------------------|-------------------|-------------------|
| **Theme** | Voice-first concept | Hybrid commands | Programmatic migration | Containerized MVP |
| **Key work** | Dual-stack design, financial model ($0.00063/turn) | `/save` `/load` `/theme`, procedural gen, Ollama | `GAME_MODE` flag, parser, biome tables, test suite intro | Docker Compose, API hardening, combat/query maturity |
| **Tests** | — | — | First suite | **43 total** |

---

# Challenges & Lessons Learned

**LLMs on the critical path fail in production**
Quota exhaustion, inconsistent JSON, 800–1500 ms latency per turn.
→ Build deterministic first. Use LLM where failure is recoverable.

**State ownership must be explicit**
Early versions let the LLM describe state it didn't actually track.
→ The engine owns all mutations. The LLM only narrates what it's told.

**API contracts need to come before parallel work**
Implicit contracts caused silent frontend breakage as backend shapes evolved.
→ Write the schema first, code second.

---

# Future Work

- **Voice input** — classification is done; voice is a frontend integration layer on the existing turn API
- **Playwright E2E tests** — frontend has no automated coverage today
- **Streaming LLM responses** — token-by-token via SSE suits the terminal aesthetic
- **Cloud persistence + multi-user** — `GameState` serializes to JSON; document store migration is straightforward
- **Intent classification benchmark** — the M1 evaluation dataset (200–300 pairs) was never built; would give concrete parser accuracy metrics

---

# Conclusion

**The problem:** syntax friction makes text adventure interfaces opaque obstacles.

**What we built:** a natural language game engine where the parser is invisible and the story is the interface.

**The generalizable pattern:**

> *Deterministic core + LLM enrichment layer = resilient AI-augmented system*

The engine is correct by default. The LLM makes it richer when it can. The game never breaks when it can't.


**The original voice vision is reachable** — the classification problem is solved. Completing it is an integration milestone, not a research problem.

---

<!-- _class: title-slide -->

# Questions?

<br>

**Repo:** `Downmoto/LLM-VC-Dungeon`
**Branch:** `main`

<br>

*Arad Fadaei · Mahboobeh Yasini · Johnpaul Tamburro*
