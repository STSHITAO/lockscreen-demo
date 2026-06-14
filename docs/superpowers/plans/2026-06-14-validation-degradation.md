# Validation Degradation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve usable model-generated lockscreen DSL when only recoverable interaction or validation issues remain.

**Architecture:** Normalize common model variations at the interaction boundary, classify validator output by whether the normalized DSL remains renderable, and make the orchestrator reserve global fallback for non-renderable results. Keep all remaining issues in debug output and expose local interaction failures as notices.

**Tech Stack:** Python, FastAPI, pytest, Vue 3, Node test runner, Vite

---

### Task 1: Reproduce Interaction Compatibility Failures

**Files:**
- Modify: `backend/tests/test_interaction_defaults.py`
- Modify: `backend/tests/test_interaction_validator.py`
- Modify: `backend/tests/test_orchestrator.py`

- [ ] Add a test proving `bottom cards` normalizes to `card-group`.
- [ ] Add a test proving a string trigger normalizes to its canonical object.
- [ ] Add a test proving a removed invalid interaction does not trigger global fallback.
- [ ] Run the focused tests and confirm they fail for the expected reasons.

### Task 2: Implement Local Interaction Degradation

**Files:**
- Modify: `backend/utils/interaction_defaults.py`
- Modify: `backend/validators/interaction_validator.py`

- [ ] Extend target and trigger normalization.
- [ ] Return interaction normalization/removal issues as warnings and notices.
- [ ] Run focused interaction tests and confirm they pass.

### Task 3: Implement Renderability-Aware Fallback

**Files:**
- Create: `backend/validators/error_policy.py`
- Modify: `backend/orchestrator.py`
- Modify: `backend/tests/test_orchestrator.py`
- Modify: `backend/tests/test_streaming.py`

- [ ] Add tests for preserving a renderable DSL after exhausted repairs.
- [ ] Add tests for retaining global fallback for a non-renderable DSL.
- [ ] Implement renderability checks and recoverable finalization.
- [ ] Verify synchronous and streaming orchestration behavior.

### Task 4: Full Verification and End-to-End Test

**Files:**
- No production file changes expected.

- [ ] Run `python -m pytest -q`.
- [ ] Run `npm.cmd test`.
- [ ] Run `npm.cmd run build`.
- [ ] Start FastAPI and Vue locally.
- [ ] Submit at least two real-model prompts and inspect final DSL features,
      repair status, fallback status, and HTTP/CORS behavior.
- [ ] Stop temporary services.

### Task 5: Review, Commit, and Push

**Files:**
- Review all changed files in the repository.

- [ ] Run `git diff --check`.
- [ ] Review for API keys and ensure `backend/.env` is not tracked.
- [ ] Commit the complete V2.1–V2.4 working tree plus this fix.
- [ ] Push `main` to `origin`.
