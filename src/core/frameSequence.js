export function frameIndexAtElapsed(
  elapsedMs,
  frameCount,
  fps,
  loop = true,
) {
  const count = Math.max(0, Math.floor(Number(frameCount) || 0))
  if (count <= 1) return 0

  const safeFps = Math.min(24, Math.max(1, Number(fps) || 6))
  const elapsed = Math.max(0, Number(elapsedMs) || 0)
  const index = Math.floor((elapsed / 1000) * safeFps)
  return loop ? index % count : Math.min(index, count - 1)
}
