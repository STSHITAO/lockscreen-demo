export const SUPPORTED_LAYER_ANIMATIONS = new Set([
  'float',
  'pulse',
  'rotate',
  'twinkle',
  'drift-left',
  'drift-right',
  'sway',
  'bounce',
  'fade',
  'breathe',
])

export function animationClassName(animation) {
  return SUPPORTED_LAYER_ANIMATIONS.has(animation)
    ? `animation-${animation}`
    : ''
}
