import assert from 'node:assert/strict'
import test from 'node:test'

import { createSseParser } from '../src/core/streamEvents.js'

test('parses SSE JSON events across split network chunks', () => {
  const events = []
  const parser = createSseParser((event) => events.push(event))

  parser.push('data: {"type":"phase","phase":"intent"}\n')
  parser.push('\ndata: {"type":"thinking","delta":"分析')
  parser.push('主题"}\n\n')
  parser.finish()

  assert.deepEqual(events, [
    { type: 'phase', phase: 'intent' },
    { type: 'thinking', delta: '分析主题' },
  ])
})

test('ignores keep-alive and malformed SSE blocks', () => {
  const events = []
  const parser = createSseParser((event) => events.push(event))

  parser.push(': keep-alive\n\n')
  parser.push('data: not-json\n\n')
  parser.push('data: {"type":"final","dsl":{"layers":[]}}\n\n')
  parser.finish()

  assert.equal(events.length, 1)
  assert.equal(events[0].type, 'final')
})

test('flushes a final event without a trailing blank line', () => {
  const events = []
  const parser = createSseParser((event) => events.push(event))

  parser.push('data: {"type":"final","dsl":{"layers":[]}}')
  parser.finish()

  assert.equal(events.length, 1)
  assert.equal(events[0].type, 'final')
})

test('does not swallow errors from the event handler', () => {
  const parser = createSseParser(() => {
    throw new Error('invalid final DSL')
  })

  assert.throws(
    () => parser.push('data: {"type":"final"}\n\n'),
    /invalid final DSL/,
  )
})
