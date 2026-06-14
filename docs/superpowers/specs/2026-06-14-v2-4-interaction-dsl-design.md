# V2.4 Interaction DSL Design

## Goal

Extend LockScreen DSL with safe, reusable visual interactions generated from
natural language. The model describes triggers and controlled actions; it never
returns JavaScript, CSS, event-handler code, or free-form SVG.

## DSL

The existing `layers` remain the visual source of truth. V2.4 adds:

```json
{
  "cardGroups": [],
  "interactions": [],
  "interactionNotices": []
}
```

An interaction references a visual layer or card group by stable ID:

```json
{
  "id": "heart-triple-tap",
  "targetId": "main-heart",
  "trigger": {
    "type": "multiTap",
    "count": 3,
    "withinMs": 1200
  },
  "actions": [
    {
      "type": "animate",
      "animation": "pulse",
      "duration": 600,
      "speed": 2,
      "intensity": 1.5
    },
    {
      "type": "burst",
      "particleSource": {"type": "shape", "shape": "heart"},
      "count": 12,
      "duration": 800,
      "afterEffect": "restore"
    }
  ]
}
```

## Controlled Vocabulary

Triggers:

- `tap`
- `multiTap`
- `longPressStart`
- `longPressEnd`
- `swipeLeft`
- `swipeRight`

Actions:

- `animate`
- `stopAnimation`
- `setAnimationSpeed`
- `burst`
- `switchCard`
- `setVisibility`
- `reset`

Particles prefer `heart`, `star`, `sparkle`, or `circle`. A particle may use a
trusted local SVG only through a catalog-validated `assetId`.

## Defaults And Limits

- Ambiguous repeated tapping means three taps.
- Explicit tap counts are preserved and clamped to `1..10`.
- `multiTap.withinMs` defaults to 1200 and is clamped to `300..3000`.
- Long press defaults to 500 ms and is clamped to `250..3000`.
- Particle count defaults to 12 and is clamped to `1..40`.
- Action duration is clamped to `80..5000` ms.
- Effects restart when the same visual interaction is triggered again.
- Card transitions ignore repeated swipes while a transition is active.
- Burst defaults to `afterEffect: "restore"`. It only hides the source when
  the user explicitly asks for disappearance.

## Card Groups

Card groups reference existing widget or glass-card layer IDs. Only one card is
visible at a time. `swipeLeft` selects the next card and `swipeRight` selects
the previous card. V2.4 does not switch the complete lock-screen scene.

## Backend Flow

```text
prompt
  -> intent extraction, including interactionRequirements
  -> material and visual composition
  -> animation fallback
  -> interaction fallback/normalization
  -> schema, asset, layout, semantic, interaction validators
  -> repair loop
  -> final DSL
```

The interaction stage may bind a requirement to an existing matching layer. If
a simple supported target is missing, it may ask the existing Fallback Draw
Agent for a controlled shape. Unsupported interactions are removed and
reported through `interactionNotices`; they do not force a full-screen fallback.

## Frontend Runtime

The Vue preview keeps runtime state separate from the immutable DSL:

- active animation overrides by layer ID
- hidden layer IDs
- active card index by group ID
- pointer/tap/long-press state
- transient burst particles

Pointer events support mouse and touch through the same handlers. Action arrays
run sequentially. Long-press start actions remain active until release when
their `until` value is `release`.

## Export

PNG and JPEG capture the currently visible runtime state, including particles.
SVG remains deterministic and exports the DSL's stable visual state without
JavaScript or interaction handlers. The interaction definitions remain
available in the DSL JSON.

## Validation And Repair

The interaction validator:

- rejects unknown triggers and actions
- resolves or removes missing targets
- clamps unsafe timing, count, speed, and intensity values
- validates card membership and direction
- validates local particle `assetId`
- removes empty interactions and duplicate IDs
- prevents non-terminating action configurations

Every validator mutation produces a structured error so the existing repair
loop can revalidate the corrected DSL.

## Acceptance Scenarios

1. Tap a heart to pulse.
2. Triple-tap a heart to pulse, burst, and restore.
3. Five taps burst a heart and hide it when explicitly requested.
4. Hold a star to accelerate twinkling; release to burst and restore.
5. Swipe between weather, schedule, and quote cards.
6. Burst with a trusted local SVG particle source.
7. Invalid target/action/asset references are repaired or removed.
8. Unsupported complex interactions produce a notice without replacing the
   whole lock screen.
