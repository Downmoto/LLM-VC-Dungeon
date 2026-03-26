Created memory file [](file:///Users/arad/Library/Application%20Support/Code/User/workspaceStorage/10ceea539b046e3e33fbe0096be1a5ed/GitHub.copilot-chat/memory-tool/memories/N2IyM2ZjNmItMDRmZC00ZDQ2LTliZTItYjY0MWVhNDFlYjU3/plan.md)

## Plan: Final MVP Cohesive Dungeon + Container Launch

Recommended approach is to ship a production-like containerized MVP first, then harden narrative consistency by adding structured memory (rolling summary + recent turns), then improve room/enemy narration quality, and finally add a lightweight combat loop. This keeps deployment risk low while directly fixing the largest gameplay coherence issues you called out.

**Steps**
1. Phase 1: Container baseline for single launch system.
2. Create root container assets for one-command startup: backend image, frontend image, compose orchestration, env template, and ignore files.
3. Make runtime config container-safe: env-driven CORS, host/port correctness, save path compatibility, and health checks.
4. Adjust frontend build/runtime target for container serving while keeping current local dev scripts intact.
5. Phase 2: Narrative memory and tool-call consistency.
6. Add structured turn memory pipeline in the backend: rolling summary plus recent-turn window included in both classification and narration prompts.
7. Add memory budget controls: max window size, summary refresh cadence, truncation/token guards.
8. Harden LLM classification reliability: validate tool-call output, bounded retry with backoff, deterministic fallback to programmatic classifier.
9. Expand turn API response with additive state snapshot fields so frontend can reflect consistent game state per turn.
10. Phase 3: Adventure cohesion and text variety.
11. Use room visit tracking for first-entry vs re-entry narration behavior, with anti-duplication constraints.
12. Enforce enemy mention in narration whenever enemies are present via prompt constraints and post-generation guardrails.
13. Add biome/style guidance to reduce samey room prose and improve cross-room thematic continuity.
14. Phase 4: Lightweight combat loop.
15. Replace instant-kill attack with minimal loop: hit chance, damage, retaliation, hp updates, defeat outcomes, short combat narration.
16. Keep combat intentionally small for MVP (no status systems, no ability trees, no complex initiative).
17. Phase 5: Verification and release readiness.
18. Extend backend tests for memory inclusion, retry/fallback, revisit variety, enemy mention guarantees, and combat hp transitions.
19. Validate frontend integration for expanded turn payload and load-game command flow.
20. Run full compose verification: build, up, health checks, turn flow, save/load persistence across restart, optional Ollama profile smoke test.
21. Update launch docs so Docker Compose is primary MVP launch path and current script remains fallback.

**Relevant files**
- game.py for turn orchestration, prompts, memory injection, combat loop.
- llm.py for tool-call validation/retry/fallback and context-aware classification interface.
- models.py for persisted memory/combat state fields.
- generator.py for room variety/thematic cohesion and enemy narrative consistency hooks.
- main.py for expanded response contract and env-driven runtime behavior.
- config.py for memory window/summary/runtime knobs.
- storage.py for persistence compatibility.
- test_game_turns.py for behavior coverage of core gameplay changes.
- test_intent.py for classification resilience tests.
- client.ts for turn response typing updates.
- +page.svelte for command wiring and state display updates.
- svelte.config.js and package.json for container build/runtime compatibility.
- README.md and launch.sh for updated launch/runbook guidance.

**Verification**
1. Run backend test suite and confirm new memory/combat/revisit/tool-fallback tests pass.
2. Run frontend check/build and verify expanded response fields are consumed safely.
3. Bring stack up via compose and verify backend/frontend health plus gameplay loop from UI.
4. Validate persistence by playing turns, restarting stack, loading save, and checking history continuity.
5. Perform narrative quality checks: first entry vs re-entry contrast and explicit enemy presence in combat-capable rooms.
6. Simulate LLM/tool-call failures and verify deterministic fallback behavior.

**Decisions captured**
- Compose default: production-like.
- Ollama: optional compose profile.
- Combat: include lightweight loop now.
- Narrative memory: rolling summary plus recent-turn window.
- Out of scope for MVP: advanced combat systems and major world-generation architecture rewrite.

Plan has been saved to /memories/session/plan.md. If you want, I can refine this into a milestone-by-milestone execution checklist with rough hour estimates per step before handoff.