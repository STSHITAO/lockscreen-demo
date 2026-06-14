# Validation Degradation Design

## Goal

Prevent one invalid or automatically repaired interaction from replacing an
otherwise renderable generated lockscreen with the global fallback DSL.

## Error Policy

Validation results are split into two behavioral classes:

- Blocking issues mean the DSL cannot be rendered safely, such as a missing
  layer array or no supported layers after normalization.
- Recoverable issues mean the validator already repaired or removed the bad
  field, layer, card group, or interaction. They remain visible as warnings
  and debug information but do not fail the whole generation.

The global fallback DSL is reserved for generation failures and DSLs that have
no renderable layers after validation and repair.

## Interaction Compatibility

Interaction normalization accepts both the canonical trigger object and a
plain trigger string. Natural-language targets including `bottom cards`,
`cards`, `card carousel`, and their Chinese equivalents normalize to
`card-group`.

An invalid interaction is removed locally and reported as an interaction
notice. Valid layers, card groups, and other interactions are retained.

## Repair Loop

The repair loop continues to repair schema, asset, layout, and semantic
problems. After the configured rounds, a renderable DSL is returned with
remaining recoverable issues recorded in `_debug.errorsAfterRepair`.
Only a non-renderable DSL is replaced by the global fallback.

## Verification

Regression tests cover:

- `bottom cards` normalization and card group creation.
- String trigger normalization.
- Invalid interaction removal without global fallback.
- A renderable DSL surviving exhausted repair rounds.
- A non-renderable DSL still using the global fallback.
- A real-model end-to-end prompt containing frame animation, long press,
  multi-tap, card swiping, validation, rendering data, and export-safe layers.
