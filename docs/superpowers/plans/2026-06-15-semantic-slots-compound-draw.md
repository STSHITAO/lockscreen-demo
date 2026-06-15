# Semantic Slots And Compound Draw Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove fallback content collisions and add controlled agent-generated compound illustrations for missing materials.

**Architecture:** A semantic composition validator reconciles layer sources, unique roles, and card-group ownership after every validation pass. A compound draw agent converts unknown missing targets into bounded primitive plans that share one JSON representation across backend validation, Vue rendering, and SVG export.

**Tech Stack:** Python, FastAPI, pytest, Vue 3, JavaScript, Node test runner, SVG

---

### Task 1: Semantic Slot Regression Tests

**Files:**
- Create: `backend/tests/test_composition_validator.py`
- Modify: `backend/tests/test_orchestrator.py`

- [ ] Test that model weather replaces fallback weather.
- [ ] Test that duplicate time keeps the higher-priority layer.
- [ ] Test that an independent bottom weather card is adopted or removed when
      a card group owns the region.
- [ ] Test that successful generated DSL contains no global fallback layers.
- [ ] Run focused tests and confirm failure.

### Task 2: Semantic Composition Validator

**Files:**
- Create: `backend/validators/composition_validator.py`
- Modify: `backend/validators/__init__.py`
- Modify: `backend/orchestrator.py`
- Modify: `backend/llm_client.py`
- Modify: `src/core/fallbackDSL.js`
- Modify: `backend/agents/repair_agent.py`

- [ ] Normalize layer sources.
- [ ] Reconcile unique semantic slots by source priority.
- [ ] Reconcile card-group region ownership.
- [ ] Remove time, date, and weather from global fallback DSLs.
- [ ] Mark repair-created layers with `source: repair`.
- [ ] Run focused tests and confirm pass.

### Task 3: Compound Draw Backend

**Files:**
- Create: `backend/agents/compound_draw_agent.py`
- Modify: `backend/llm_client.py`
- Modify: `backend/orchestrator.py`
- Modify: `backend/validators/schema_validator.py`
- Modify: `backend/validators/layout_validator.py`
- Modify: `backend/validators/error_policy.py`
- Create: `backend/tests/test_compound_draw_agent.py`
- Modify: `backend/tests/test_orchestrator.py`

- [ ] Test primitive clamping and the 24-part budget.
- [ ] Test drawing an unknown target through an injected planner.
- [ ] Test invalid plans fail without corrupting the DSL.
- [ ] Add `compoundShape` to the controlled DSL and composition prompt.
- [ ] Integrate unknown missing targets into fallback drawing.
- [ ] Run focused backend tests.

### Task 4: Vue And SVG Rendering

**Files:**
- Modify: `src/components/LockScreenPreview.vue`
- Modify: `src/core/exportSvg.js`
- Modify: `test/interactionComponents.test.js`
- Modify: `test/exportSvg.test.js`

- [ ] Add failing tests for compound rendering and export.
- [ ] Render compound parts through a nested SVG in Vue.
- [ ] Convert compound parts to SVG primitives in XML export.
- [ ] Run focused frontend tests.

### Task 5: Full And End-To-End Verification

**Files:**
- No expected production changes.

- [ ] Run `python -m pytest -q`.
- [ ] Run `npm.cmd test`.
- [ ] Run `npm.cmd run build`.
- [ ] Test a three-card prompt and verify no independent weather/time overlap.
- [ ] Test an unknown-object prompt and verify a material or compound drawing
      is returned without global fallback.
- [ ] Confirm PNG/JPEG DOM rendering and SVG export remain available.
