export function createSseParser(onEvent) {
  let buffer = ''

  function parseBlock(block) {
    const dataLines = block
      .split(/\r?\n/)
      .filter((line) => line.startsWith('data:'))
      .map((line) => line.slice(5).trimStart())
    if (!dataLines.length) return

    let event
    try {
      event = JSON.parse(dataLines.join('\n'))
    } catch {
      return
    }
    onEvent(event)
  }

  function drain(final = false) {
    const blocks = buffer.split(/\r?\n\r?\n/)
    buffer = final ? '' : blocks.pop() || ''
    for (const block of blocks) parseBlock(block)
    if (final && buffer.trim()) parseBlock(buffer)
  }

  return {
    push(chunk) {
      buffer += chunk
      drain()
    },
    finish() {
      drain(true)
    },
  }
}
