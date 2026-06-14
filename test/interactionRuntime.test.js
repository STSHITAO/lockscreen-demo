import assert from 'node:assert/strict'
import test from 'node:test'

import { createInteractionRuntime } from '../src/core/interactionRuntime.js'


function createScheduler() {
  const tasks = []
  return {
    schedule(callback, delay) {
      tasks.push({ callback, delay })
      return tasks.length
    },
    cancel() {},
    flush() {
      while (tasks.length) tasks.shift().callback()
    },
  }
}


test('runs a multi-tap interaction only after the requested count', () => {
  const scheduler = createScheduler()
  const runtime = createInteractionRuntime(
    {
      layers: [
        {
          id: 'heart',
          type: 'shape',
          shape: 'heart',
          x: 280,
          y: 80,
          width: 52,
          height: 48,
        },
      ],
      interactions: [
        {
          id: 'heart-three',
          targetId: 'heart',
          trigger: { type: 'multiTap', count: 3, withinMs: 1200 },
          actions: [
            {
              type: 'animate',
              animation: 'pulse',
              duration: 600,
              speed: 2,
              intensity: 1.5,
            },
          ],
        },
      ],
    },
    scheduler,
  )

  runtime.trigger({ targetId: 'heart', type: 'tap', timestamp: 0 })
  runtime.trigger({ targetId: 'heart', type: 'tap', timestamp: 300 })
  assert.equal(runtime.snapshot().effects.heart, undefined)
  runtime.trigger({ targetId: 'heart', type: 'tap', timestamp: 600 })

  assert.equal(runtime.snapshot().effects.heart.animation, 'pulse')
})


test('long press start accelerates and release bursts', () => {
  const scheduler = createScheduler()
  const runtime = createInteractionRuntime(
    {
      layers: [
        {
          id: 'star',
          type: 'shape',
          shape: 'star',
          x: 280,
          y: 80,
          width: 40,
          height: 40,
        },
      ],
      interactions: [
        {
          id: 'star-hold',
          targetId: 'star',
          trigger: { type: 'longPressStart', durationMs: 500 },
          actions: [
            {
              type: 'animate',
              animation: 'twinkle',
              speed: 3,
              intensity: 1.5,
              duration: 600,
              until: 'release',
            },
          ],
        },
        {
          id: 'star-release',
          targetId: 'star',
          trigger: { type: 'longPressEnd' },
          actions: [
            { type: 'stopAnimation' },
            {
              type: 'burst',
              particleSource: { type: 'shape', shape: 'star' },
              count: 8,
              duration: 700,
              afterEffect: 'restore',
            },
          ],
        },
      ],
    },
    scheduler,
  )

  runtime.trigger({ targetId: 'star', type: 'longPressStart', timestamp: 0 })
  assert.equal(runtime.snapshot().effects.star.speed, 3)
  runtime.trigger({ targetId: 'star', type: 'longPressEnd', timestamp: 800 })
  assert.equal(runtime.snapshot().effects.star, undefined)
  assert.equal(runtime.snapshot().particles.length, 8)
})


test('setAnimationSpeed accelerates the layer base animation', () => {
  const runtime = createInteractionRuntime({
    layers: [
      {
        id: 'star',
        type: 'shape',
        shape: 'star',
        animation: 'twinkle',
      },
    ],
    interactions: [
      {
        id: 'star-hold',
        targetId: 'star',
        trigger: { type: 'longPressStart', durationMs: 500 },
        actions: [{ type: 'setAnimationSpeed', speed: 3 }],
      },
    ],
  })

  runtime.trigger({
    targetId: 'star',
    type: 'longPressStart',
    timestamp: 0,
  })

  assert.deepEqual(runtime.snapshot().effects.star, {
    animation: 'twinkle',
    speed: 3,
    intensity: 1,
  })
  runtime.destroy()
})


test('burst can hide the source and card swipe is transition locked', () => {
  const scheduler = createScheduler()
  const runtime = createInteractionRuntime(
    {
      layers: [
        {
          id: 'heart',
          type: 'shape',
          shape: 'heart',
          x: 280,
          y: 80,
          width: 52,
          height: 48,
        },
        { id: 'weather', type: 'widget' },
        { id: 'schedule', type: 'glassCard' },
      ],
      cardGroups: [
        {
          id: 'info-cards',
          cardIds: ['weather', 'schedule'],
          activeIndex: 0,
          loop: true,
          transition: 'slide',
        },
      ],
      interactions: [
        {
          id: 'heart-tap',
          targetId: 'heart',
          trigger: { type: 'tap' },
          actions: [
            {
              type: 'burst',
              particleSource: { type: 'shape', shape: 'heart' },
              count: 4,
              duration: 500,
              afterEffect: 'hide',
            },
          ],
        },
        {
          id: 'next',
          targetId: 'info-cards',
          trigger: { type: 'swipeLeft' },
          actions: [{ type: 'switchCard', direction: 'next' }],
        },
      ],
    },
    scheduler,
  )

  runtime.trigger({ targetId: 'heart', type: 'tap', timestamp: 0 })
  scheduler.flush()
  assert.equal(runtime.snapshot().hiddenLayerIds.includes('heart'), true)

  runtime.trigger({
    targetId: 'info-cards',
    type: 'swipeLeft',
    timestamp: 0,
  })
  runtime.trigger({
    targetId: 'info-cards',
    type: 'swipeLeft',
    timestamp: 20,
  })
  assert.equal(runtime.snapshot().activeCards['info-cards'], 1)
})
