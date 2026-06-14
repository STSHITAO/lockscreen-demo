function numeric(value, fallback) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

export function createBurstParticles(action, layer) {
  const count = Math.max(1, Math.min(40, numeric(action?.count, 12)))
  const duration = Math.max(80, numeric(action?.duration, 800))
  const originX = numeric(layer?.x, 0) + numeric(layer?.width, 40) / 2
  const originY = numeric(layer?.y, 0) + numeric(layer?.height, 40) / 2
  const source =
    action?.particleSource && typeof action.particleSource === 'object'
      ? { ...action.particleSource }
      : { type: 'shape', shape: 'circle' }

  return Array.from({ length: count }, (_, index) => {
    const angle = (Math.PI * 2 * index) / count - Math.PI / 2
    const distance = 42 + (index % 4) * 13
    return {
      id: `${layer?.id || 'particle'}-${Date.now()}-${index}`,
      source: { ...source },
      originX,
      originY,
      dx: Math.cos(angle) * distance,
      dy: Math.sin(angle) * distance,
      rotation: (index * 137) % 360,
      delay: (index % 5) * 18,
      duration,
      size: 8 + (index % 4) * 3,
    }
  })
}
