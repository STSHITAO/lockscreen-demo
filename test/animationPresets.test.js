import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'

import {
  animationClassName,
  SUPPORTED_LAYER_ANIMATIONS,
} from '../src/core/animationPresets.js'

test('maps controlled animation names to CSS classes', () => {
  for (const name of [
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
  ]) {
    assert.ok(SUPPORTED_LAYER_ANIMATIONS.has(name))
    assert.equal(animationClassName(name), `animation-${name}`)
  }
  assert.equal(animationClassName('transform-and-fly'), '')
})

test('lockscreen preview defines every controlled animation keyframe', async () => {
  const component = await readFile(
    new URL('../src/components/LockScreenPreview.vue', import.meta.url),
    'utf8',
  )

  for (const name of [
    'twinkle',
    'driftLeft',
    'driftRight',
    'sway',
    'bounce',
    'fade',
    'breathe',
  ]) {
    assert.match(component, new RegExp(`@keyframes ${name}`))
  }
})
