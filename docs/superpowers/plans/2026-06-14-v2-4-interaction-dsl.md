# V2.4 Interaction DSL Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add validated natural-language visual interactions, card swiping, and controlled particle effects to the existing LockScreen DSL pipeline.

**Architecture:** Extend intent and final DSL with declarative interaction data. A deterministic backend interaction stage binds requirements to trusted layers, while a standalone Vue runtime interprets triggers and action sequences without executing model-authored code.

**Tech Stack:** FastAPI, Python validators and orchestrator, Vue 3, Pointer Events, CSS animations, Node test runner, pytest.

---

### Task 1: Interaction Defaults And Normalization

**Files:**
- Create: `backend/utils/interaction_defaults.py`
- Test: `backend/tests/test_interaction_defaults.py`

- [ ] Add failing tests for explicit and ambiguous tap counts, long-press
  requirements, swipe-card requirements, action defaults, and safety clamps.
- [ ] Run `python -m pytest backend/tests/test_interaction_defaults.py -q` and
  verify failure because the module does not exist.
- [ ] Implement trigger/action constants, prompt extraction, normalization, and
  numeric clamps.
- [ ] Re-run the focused tests and verify they pass.

### Task 2: Interaction Agent

**Files:**
- Create: `backend/agents/interaction_agent.py`
- Test: `backend/tests/test_interaction_agent.py`

- [ ] Add failing tests that bind heart and star requirements to existing
  layers, inject a supported fallback shape when missing, generate paired
  long-press start/end interactions, and create card groups.
- [ ] Verify the tests fail for the missing agent.
- [ ] Implement `apply_interaction_requirements(dsl, prompt, context)`.
- [ ] Verify generated interactions contain only the controlled DSL fields.

### Task 3: Interaction Validator And Repair Integration

**Files:**
- Create: `backend/validators/interaction_validator.py`
- Modify: `backend/validators/__init__.py`
- Modify: `backend/orchestrator.py`
- Modify: `backend/agents/repair_agent.py`
- Test: `backend/tests/test_interaction_validator.py`
- Modify: `backend/tests/test_orchestrator.py`
- Modify: `backend/tests/test_streaming.py`

- [ ] Add failing tests for target IDs, trigger/action whitelists, tap limits,
  trusted particle assets, card IDs, notices, and orchestrator events.
- [ ] Implement deterministic validation and corrections.
- [ ] Insert the interaction stage after animation fallback and include the
  validator in every validation round.
- [ ] Emit `interaction_ready` and `interaction_unavailable` stream events.
- [ ] Preserve notices in `_debug.interactionNotices`.
- [ ] Run focused backend tests.

### Task 4: LLM Intent And Composition Contract

**Files:**
- Modify: `backend/llm_client.py`
- Modify: `backend/tests/test_llm_client.py`

- [ ] Add failing tests for normalized `interactionRequirements`, preserved
  top-level `interactions`, `cardGroups`, and trusted particle assets.
- [ ] Extend intent and composition prompts with the controlled vocabulary and
  explicit prohibition against JavaScript/CSS/free SVG.
- [ ] Normalize interaction fields before the validator pipeline.
- [ ] Run focused LLM client tests.

### Task 5: Frontend Gesture And Action Runtime

**Files:**
- Create: `src/core/gestureRecognizer.js`
- Create: `src/core/interactionRuntime.js`
- Create: `src/core/particleEngine.js`
- Test: `test/gestureRecognizer.test.js`
- Test: `test/interactionRuntime.test.js`
- Test: `test/particleEngine.test.js`

- [ ] Add failing tests for single/multi tap, long press and release, swipe
  direction, sequential actions, restart behavior, card locks, particle shape,
  trusted asset particles, restore, and hide.
- [ ] Implement framework-independent state helpers using injected clocks where
  timing is required.
- [ ] Run focused Node tests.

### Task 6: Vue Preview Integration

**Files:**
- Create: `src/components/InteractionParticle.vue`
- Create: `src/components/CardGroup.vue`
- Modify: `src/components/LockScreenPreview.vue`
- Modify: `src/core/animationPresets.js`
- Modify: `src/App.vue`
- Test: `test/interactionComponents.test.js`

- [ ] Add source-level component contract tests for pointer handlers, particle
  rendering, card visibility, and interaction notices.
- [ ] Make interactive layers receive pointer events while preserving normal
  rendering for non-interactive layers.
- [ ] Apply runtime animation overrides, visibility, particles, and active card
  state without mutating the input DSL.
- [ ] Display interaction stream events in the existing agent timeline.
- [ ] Run frontend tests and production build.

### Task 7: Export And Documentation

**Files:**
- Modify: `src/core/exportSvg.js`
- Modify: `README.md`
- Test: `test/exportSvg.test.js`

- [ ] Add a test proving SVG export ignores interaction handlers and exports a
  stable visual state.
- [ ] Confirm PNG/JPEG target the live preview node and therefore capture the
  current runtime state.
- [ ] Document the V2.4 DSL, supported triggers/actions, limits, and export
  behavior.

### Task 8: Full Verification And End-To-End Acceptance

**Files:**
- Add or modify focused acceptance tests under `backend/tests/` and `test/`.

- [ ] Run `python -m pytest backend/tests -q`.
- [ ] Run `npm.cmd test`.
- [ ] Run `npm.cmd run build`.
- [ ] Run `python -m compileall -q backend`.
- [ ] Run `git diff --check`.
- [ ] Test at least two real-model prompts: heart multi-tap burst and star
  long-press acceleration/release burst.
- [ ] Test card-group left/right swipe with a deterministic DSL.
- [ ] Start local servers, perform HTTP/CORS checks, and inspect the preview in
  the in-app browser when the browser environment is available.
