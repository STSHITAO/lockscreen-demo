const DEFAULT_BACKGROUND = '#020617'

function escapeXml(value = '') {
  return String(value)
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&apos;')
}

function number(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function parseGradient(value = '') {
  const match = String(value).match(
    /linear-gradient\(\s*([\d.]+)deg\s*,\s*(.+?)\s+([\d.]+)%\s*,\s*(.+?)\s+([\d.]+)%\s*\)/i,
  )
  if (!match) return null

  const angle = number(match[1], 180)
  const radians = ((angle - 90) * Math.PI) / 180
  const x = Math.cos(radians)
  const y = Math.sin(radians)

  return {
    x1: `${50 - x * 50}%`,
    y1: `${50 - y * 50}%`,
    x2: `${50 + x * 50}%`,
    y2: `${50 + y * 50}%`,
    startColor: match[2].trim(),
    startOffset: `${match[3]}%`,
    endColor: match[4].trim(),
    endOffset: `${match[5]}%`,
  }
}

function backgroundMarkup(background, width, height) {
  if (background?.type === 'gradient') {
    const gradient = parseGradient(background.value)
    if (gradient) {
      return {
        defs: `<linearGradient id="lockscreen-bg" x1="${gradient.x1}" y1="${gradient.y1}" x2="${gradient.x2}" y2="${gradient.y2}"><stop offset="${gradient.startOffset}" stop-color="${escapeXml(gradient.startColor)}"/><stop offset="${gradient.endOffset}" stop-color="${escapeXml(gradient.endColor)}"/></linearGradient>`,
        markup: `<rect width="${width}" height="${height}" fill="url(#lockscreen-bg)"/>`,
      }
    }
  }

  return {
    defs: '',
    markup: `<rect width="${width}" height="${height}" fill="${escapeXml(background?.value || DEFAULT_BACKGROUND)}"/>`,
  }
}

function textAnchor(align) {
  if (align === 'right') return 'end'
  if (align === 'left') return 'start'
  return 'middle'
}

function renderText(layer) {
  return `<text x="${number(layer.x)}" y="${number(layer.y)}" fill="${escapeXml(layer.color || '#ffffff')}" font-size="${number(layer.fontSize, 16)}" font-weight="${number(layer.fontWeight, 400)}" text-anchor="${textAnchor(layer.align)}" font-family="Inter, Segoe UI, Arial, sans-serif">${escapeXml(layer.content)}</text>`
}

function renderStar(layer) {
  const x = number(layer.x)
  const y = number(layer.y)
  const width = number(layer.width, 12)
  const height = number(layer.height, width)
  const cx = x + width / 2
  const cy = y + height / 2
  const outer = Math.min(width, height) / 2
  const inner = outer * 0.42
  const points = Array.from({ length: 10 }, (_, index) => {
    const radius = index % 2 === 0 ? outer : inner
    const angle = -Math.PI / 2 + (index * Math.PI) / 5
    return `${cx + Math.cos(angle) * radius},${cy + Math.sin(angle) * radius}`
  }).join(' ')
  return `<polygon points="${points}" fill="${escapeXml(layer.color || '#ffffff')}" opacity="${number(layer.opacity, 1)}"/>`
}

function renderShape(layer) {
  const x = number(layer.x)
  const y = number(layer.y)
  const width = number(layer.width, 20)
  const height = number(layer.height, width)
  const fill = escapeXml(layer.color || 'rgba(255,255,255,0.75)')
  const opacity = number(layer.opacity, 1)

  if (layer.shape === 'circle') {
    return `<circle cx="${x + width / 2}" cy="${y + height / 2}" r="${Math.min(width, height) / 2}" fill="${fill}" opacity="${opacity}"/>`
  }
  if (layer.shape === 'line') {
    return `<line x1="${x}" y1="${y}" x2="${x + width}" y2="${y + height}" stroke="${fill}" stroke-width="${number(layer.strokeWidth, 2)}" opacity="${opacity}" stroke-linecap="round"/>`
  }
  if (layer.shape === 'star') return renderStar(layer)
  if (layer.shape === 'blob') {
    return `<ellipse cx="${x + width / 2}" cy="${y + height / 2}" rx="${width / 2}" ry="${height / 2}" fill="${fill}" opacity="${opacity}" filter="url(#soft-blur)"/>`
  }
  return `<rect x="${x}" y="${y}" width="${width}" height="${height}" rx="${number(layer.radius, 24)}" fill="${fill}" opacity="${opacity}"/>`
}

function contentLines(content) {
  if (typeof content === 'string') return { title: '', main: content, subtitle: '', icon: '' }
  return {
    title: content?.title || '',
    main: content?.main || '',
    subtitle: content?.subtitle || '',
    icon: content?.icon || '',
  }
}

function renderCard(layer) {
  const x = number(layer.x)
  const y = number(layer.y)
  const width = number(layer.width, 326)
  const height = number(layer.height, 96)
  const content = contentLines(layer.content)
  const iconSpace = content.icon ? 56 : 0
  const textX = x + 20 + iconSpace
  const titleY = y + 30
  const mainY = y + 58
  const subtitleY = y + 80

  return [
    `<rect x="${x}" y="${y}" width="${width}" height="${height}" rx="${number(layer.radius, 24)}" fill="rgba(255,255,255,0.12)" stroke="rgba(255,255,255,0.22)" stroke-width="1"/>`,
    content.icon
      ? `<text x="${x + 24}" y="${y + height / 2 + 11}" fill="#ffffff" font-size="34" font-family="Segoe UI Symbol, Arial">${escapeXml(content.icon)}</text>`
      : '',
    content.title
      ? `<text x="${textX}" y="${titleY}" fill="rgba(255,255,255,0.7)" font-size="13" font-weight="500" font-family="Inter, Segoe UI, Arial">${escapeXml(content.title)}</text>`
      : '',
    content.main
      ? `<text x="${textX}" y="${mainY}" fill="#ffffff" font-size="19" font-weight="650" font-family="Inter, Segoe UI, Arial">${escapeXml(content.main)}</text>`
      : '',
    content.subtitle
      ? `<text x="${textX}" y="${subtitleY}" fill="rgba(255,255,255,0.65)" font-size="12" font-family="Inter, Segoe UI, Arial">${escapeXml(content.subtitle)}</text>`
      : '',
  ].join('')
}

function renderLayer(layer) {
  if (layer?.type === 'text') return renderText(layer)
  if (layer?.type === 'shape') return renderShape(layer)
  if (layer?.type === 'widget' || layer?.type === 'glassCard') return renderCard(layer)
  return ''
}

export function dslToSvg(dsl) {
  const width = number(dsl?.canvas?.width, 390)
  const height = number(dsl?.canvas?.height, 844)
  const background = backgroundMarkup(dsl?.background, width, height)
  const layers = Array.isArray(dsl?.layers) ? dsl.layers.map(renderLayer).join('') : ''

  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`,
    `<defs>${background.defs}<filter id="soft-blur"><feGaussianBlur stdDeviation="24"/></filter></defs>`,
    background.markup,
    layers,
    '</svg>',
  ].join('')
}

export function downloadSvg(dsl) {
  const blob = new Blob([dslToSvg(dsl)], { type: 'image/svg+xml;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.download = 'lockscreen.svg'
  link.href = url
  link.click()
  URL.revokeObjectURL(url)
}
