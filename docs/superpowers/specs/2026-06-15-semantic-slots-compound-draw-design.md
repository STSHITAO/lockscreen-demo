# Semantic Slots And Compound Draw Design

## Goal

Prevent fallback time and weather layers from overlapping model-generated
content, while allowing the agent to draw recognizable simplified objects when
the material catalog has no suitable asset.

## Layer Sources

Every normalized layer has one controlled `source` value:

- `system`
- `user`
- `model`
- `material`
- `draw-agent`
- `repair`
- `fallback`

Conflict priority is:

`system > user > model > material > draw-agent > repair > fallback`.

Global fallback layers never merge into a successful generated DSL. Draw-agent
layers are not global fallback layers and may coexist with model content.

## Semantic Slots

The roles `time`, `date`, `weather`, `schedule`, and `music` are unique slots.
When duplicate slots exist, validation keeps the highest-priority layer.

Card groups own their card region. A card in the same region that is not a
member is either adopted into the group when its role is missing, or removed
when the group already contains that role. This prevents an independent repair
weather card from covering a three-card carousel.

## Global Fallback

Frontend and backend global fallback DSLs contain only a neutral background
decoration. They contain no time, date, or weather content. They are used only
when generation fails or no renderable DSL remains.

## Compound Shape DSL

Missing arbitrary objects may be represented by a controlled layer:

```json
{
  "id": "draw-cat",
  "type": "compoundShape",
  "target": "cat",
  "source": "draw-agent",
  "x": 110,
  "y": 260,
  "width": 170,
  "height": 190,
  "parts": [
    {
      "shape": "ellipse",
      "x": 0.2,
      "y": 0.05,
      "width": 0.6,
      "height": 0.48,
      "fill": "#f97316"
    }
  ]
}
```

Part coordinates and sizes are normalized from `0` to `1`. Supported
primitives are `circle`, `ellipse`, `rect`, `roundedRect`, `triangle`,
`polygon`, and `line`. Polygon points are normalized coordinate pairs.

The backend limits a compound layer to 24 parts and clamps all numeric values.
The LLM produces only a JSON drawing plan, never SVG, HTML, CSS, or path data.

## Drawing Policy

- Up to 8 parts: draw directly.
- 9 to 24 parts: simplify details and draw.
- More than 24 requested parts: ask the model for a silhouette or outline
  within the budget.
- Only requests requiring photorealistic texture, detailed human anatomy,
  complex perspective, or cinematic multi-stage motion are reported as
  unavailable.

## Pipeline

1. Generate and normalize the draft DSL.
2. Validate assets, layout, semantics, and interactions.
3. Use known controlled shapes for known simple targets.
4. Use the compound draw agent for unknown missing targets.
5. Repair remaining structural issues.
6. Apply semantic source and slot reconciliation.
7. Render the same compound plan in Vue and SVG export.

## Verification

Tests cover duplicate time/weather removal, card-group ownership, removal of
global fallback layers from successful DSLs, compound-plan validation,
unknown-object drawing, Vue rendering, SVG export, and two real-model
end-to-end prompts.
