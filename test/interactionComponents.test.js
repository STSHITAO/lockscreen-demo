import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import test from 'node:test'


test('lockscreen preview wires pointer gestures and interaction particles', async () => {
  const source = await readFile(
    new URL('../src/components/LockScreenPreview.vue', import.meta.url),
    'utf8',
  )

  assert.match(source, /createInteractionRuntime/)
  assert.match(source, /createGestureRecognizer/)
  assert.match(source, /InteractionParticle/)
  assert.match(source, /pointerdown/)
})


test('card group component exposes swipe pointer handlers', async () => {
  const source = await readFile(
    new URL('../src/components/CardGroup.vue', import.meta.url),
    'utf8',
  )

  assert.match(source, /pointerdown/)
  assert.match(source, /swipeLeft/)
  assert.match(source, /swipeRight/)
})


test('lockscreen preview renders controlled compound shapes', async () => {
  const source = await readFile(
    new URL('../src/components/LockScreenPreview.vue', import.meta.url),
    'utf8',
  )

  assert.match(source, /compoundShape/)
  assert.match(source, /compound-shape-svg/)
  assert.match(source, /compoundPart/)
})
