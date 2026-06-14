import assert from 'node:assert/strict'
import test from 'node:test'

import { frameIndexAtElapsed } from '../src/core/frameSequence.js'

test('frame sequence loops at the configured FPS', () => {
  assert.equal(frameIndexAtElapsed(0, 5, 5, true), 0)
  assert.equal(frameIndexAtElapsed(200, 5, 5, true), 1)
  assert.equal(frameIndexAtElapsed(1000, 5, 5, true), 0)
})

test('non-looping frame sequence stops at the final frame', () => {
  assert.equal(frameIndexAtElapsed(2000, 5, 5, false), 4)
})
