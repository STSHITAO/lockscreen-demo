# Validator + Repair Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade lockscreen generation to validate and repair draft DSL at most twice before returning a renderable result or fallback.

**Architecture:** Keep the existing two-stage LLM and material-candidate flow. Add four focused validators with one result contract, a deterministic-first repair agent, and an orchestrator that owns bounded retries and `_debug` metadata. The existing frontend continues receiving a top-level DSL object.

**Tech Stack:** Python, FastAPI, requests, pytest, Vue 3.

---

### Task 1: Validator Contracts

**Files:**
- Create: `backend/validators/__init__.py`
- Create: `backend/validators/schema_validator.py`
- Create: `backend/validators/asset_validator.py`
- Create: `backend/validators/layout_validator.py`
- Create: `backend/validators/semantic_validator.py`
- Test: `backend/tests/test_validators.py`

- [ ] Write failing tests for schema defaults, duplicate IDs, invalid assets, layout bounds/regions, and semantic requirements.
- [ ] Run `python -m pytest backend/tests/test_validators.py -v` and confirm missing-module failures.
- [ ] Implement each validator as `{"ok", "errors", "dsl"}` with defensive deep-copy fixes.
- [ ] Re-run the validator tests and confirm they pass.

### Task 2: Draft Generation and Repair Agent

**Files:**
- Modify: `backend/llm_client.py`
- Create: `backend/agents/__init__.py`
- Create: `backend/agents/repair_agent.py`
- Test: `backend/tests/test_repair_agent.py`

- [ ] Add a draft-generation entry point that preserves raw DSL and material context.
- [ ] Test deterministic repairs for missing weather and requested positions.
- [ ] Implement deterministic repairs first and optional JSON-only LLM repair second.
- [ ] Confirm repair tests and existing LLM tests pass.

### Task 3: Bounded Orchestrator

**Files:**
- Create: `backend/orchestrator.py`
- Create: `backend/tests/test_orchestrator.py`

- [ ] Write failing tests proving no more than two repairs and fallback after unresolved errors.
- [ ] Implement sequential validation, error collection, retry bounds, and `_debug`.
- [ ] Confirm orchestrator tests pass.

### Task 4: API and Frontend Compatibility

**Files:**
- Modify: `backend/main.py`
- Modify: `src/App.vue`
- Modify: `backend/requirements.txt`

- [ ] Route generation through `generate_lockscreen_with_agent_loop`.
- [ ] Accept either top-level DSL or `{dsl, debug}` responses while displaying debug JSON.
- [ ] Add pytest to backend development/runtime requirements used by the requested command.

### Task 5: Verification

**Files:**
- Modify: `README.md`

- [ ] Run `python -m pytest backend/tests -v`.
- [ ] Run `npm test`.
- [ ] Run `npm run build`.
- [ ] Start both servers and exercise the three acceptance prompts.
- [ ] Confirm invalid assets are removed, repair count never exceeds two, and fallback remains renderable.
