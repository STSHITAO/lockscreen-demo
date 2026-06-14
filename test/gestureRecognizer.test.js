import assert from 'node:assert/strict'
import test from 'node:test'

import { createGestureRecognizer } from '../src/core/gestureRecognizer.js'


test('emits tap for a short pointer gesture', () => {
  const events = []
  const recognizer = createGestureRecognizer({
    emit: (event) => events.push(event),
    schedule: () => 1,
    cancel: () => {},
  })

  recognizer.pointerDown('heart', 20, 20, 0)
  recognizer.pointerUp('heart', 22, 21, 120)

  assert.deepEqual(events, [
    { targetId: 'heart', type: 'tap', timestamp: 120 },
  ])
})


test('emits long press start and release', () => {
  const events = []
  let scheduled
  const recognizer = createGestureRecognizer({
    emit: (event) => events.push(event),
    schedule: (callback) => {
      scheduled = callback
      return 1
    },
    cancel: () => {},
  })

  recognizer.pointerDown('star', 20, 20, 0)
  scheduled()
  recognizer.pointerUp('star', 20, 20, 800)

  assert.deepEqual(events.map((event) => event.type), [
    'longPressStart',
    'longPressEnd',
  ])
})


test('emits horizontal swipe direction', () => {
  const events = []
  const recognizer = createGestureRecognizer({
    emit: (event) => events.push(event),
    schedule: () => 1,
    cancel: () => {},
  })

  recognizer.pointerDown('info-cards', 200, 700, 0)
  recognizer.pointerUp('info-cards', 120, 704, 180)

  assert.equal(events[0].type, 'swipeLeft')
})
