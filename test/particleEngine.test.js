import assert from 'node:assert/strict'
import test from 'node:test'

import { createBurstParticles } from '../src/core/particleEngine.js'


test('creates controlled shape particles around the source layer', () => {
  const particles = createBurstParticles(
    {
      particleSource: { type: 'shape', shape: 'heart' },
      count: 6,
      duration: 800,
    },
    { id: 'heart', x: 280, y: 80, width: 52, height: 48 },
  )

  assert.equal(particles.length, 6)
  assert.equal(particles[0].source.shape, 'heart')
  assert.equal(particles[0].originX, 306)
  assert.equal(particles[0].originY, 104)
})


test('preserves trusted asset particle source supplied by the backend', () => {
  const particles = createBurstParticles(
    {
      particleSource: {
        type: 'asset',
        assetId: 'doodle-143',
        src: '/materials/svg/doodle-143.svg',
      },
      count: 4,
    },
    { id: 'heart', x: 100, y: 100, width: 40, height: 40 },
  )

  assert.deepEqual(particles[0].source, {
    type: 'asset',
    assetId: 'doodle-143',
    src: '/materials/svg/doodle-143.svg',
  })
})
