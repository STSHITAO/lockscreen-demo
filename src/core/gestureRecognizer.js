export function createGestureRecognizer({
  emit,
  schedule = (callback, delay) => window.setTimeout(callback, delay),
  cancel = (timer) => window.clearTimeout(timer),
  longPressMs = 500,
  swipeDistance = 40,
} = {}) {
  let press = null

  function pointerDown(targetId, x, y, timestamp = Date.now()) {
    if (!targetId) return
    if (press?.timer) cancel(press.timer)
    press = {
      targetId,
      x,
      y,
      timestamp,
      longPressed: false,
      timer: null,
    }
    press.timer = schedule(() => {
      if (!press) return
      press.longPressed = true
      emit?.({
        targetId: press.targetId,
        type: 'longPressStart',
        timestamp: press.timestamp + longPressMs,
      })
    }, longPressMs)
  }

  function pointerMove(targetId, x, y) {
    if (!press || press.targetId !== targetId) return
    press.currentX = x
    press.currentY = y
  }

  function pointerUp(targetId, x, y, timestamp = Date.now()) {
    if (!press || press.targetId !== targetId) return
    if (press.timer) cancel(press.timer)
    const active = press
    press = null
    if (active.longPressed) {
      emit?.({ targetId, type: 'longPressEnd', timestamp })
      return
    }
    const dx = x - active.x
    const dy = y - active.y
    if (Math.abs(dx) >= swipeDistance && Math.abs(dx) > Math.abs(dy)) {
      emit?.({
        targetId,
        type: dx < 0 ? 'swipeLeft' : 'swipeRight',
        timestamp,
      })
      return
    }
    emit?.({ targetId, type: 'tap', timestamp })
  }

  function cancelPointer() {
    if (press?.timer) cancel(press.timer)
    press = null
  }

  return {
    pointerDown,
    pointerMove,
    pointerUp,
    cancel: cancelPointer,
    destroy: cancelPointer,
  }
}
