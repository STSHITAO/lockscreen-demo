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
  return `<g data-shape="star"><polygon points="${points}" fill="${escapeXml(layer.color || '#ffffff')}" opacity="${number(layer.opacity, 1)}"/></g>`
}

function renderCrescent(layer, x, y, width, height, fill, opacity) {
  const radius = Math.min(width, height) / 2
  const cx = x + width / 2
  const cy = y + height / 2
  const maskId = `crescent-${safeId(layer.id || `${x}-${y}`)}`
  return [
    `<g data-shape="crescent" opacity="${opacity}">`,
    `<mask id="${maskId}"><rect x="${x}" y="${y}" width="${width}" height="${height}" fill="#ffffff"/><circle cx="${x + width * 0.68}" cy="${y + height * 0.36}" r="${radius * 0.82}" fill="#000000"/></mask>`,
    `<circle cx="${cx}" cy="${cy}" r="${radius}" fill="${fill}" mask="url(#${maskId})"/>`,
    '</g>',
  ].join('')
}

function renderHeart(x, y, width, height, fill, opacity) {
  const cx = x + width / 2
  const path = [
    `M ${cx} ${y + height}`,
    `C ${x + width * 0.12} ${y + height * 0.72}, ${x} ${y + height * 0.46}, ${x} ${y + height * 0.28}`,
    `C ${x} ${y + height * 0.06}, ${x + width * 0.25} ${y}, ${cx} ${y + height * 0.23}`,
    `C ${x + width * 0.75} ${y}, ${x + width} ${y + height * 0.06}, ${x + width} ${y + height * 0.28}`,
    `C ${x + width} ${y + height * 0.46}, ${x + width * 0.88} ${y + height * 0.72}, ${cx} ${y + height}`,
    'Z',
  ].join(' ')
  return `<g data-shape="heart"><path d="${path}" fill="${fill}" opacity="${opacity}"/></g>`
}

function renderCloud(x, y, width, height, fill, opacity) {
  return [
    `<g data-shape="cloud" fill="${fill}" opacity="${opacity}">`,
    `<ellipse cx="${x + width * 0.5}" cy="${y + height * 0.68}" rx="${width * 0.46}" ry="${height * 0.28}"/>`,
    `<circle cx="${x + width * 0.3}" cy="${y + height * 0.48}" r="${height * 0.28}"/>`,
    `<circle cx="${x + width * 0.52}" cy="${y + height * 0.34}" r="${height * 0.35}"/>`,
    `<circle cx="${x + width * 0.72}" cy="${y + height * 0.5}" r="${height * 0.25}"/>`,
    '</g>',
  ].join('')
}

function renderSparkle(x, y, width, height, fill, opacity) {
  const cx = x + width / 2
  const cy = y + height / 2
  return [
    `<g data-shape="sparkle" stroke="${fill}" stroke-linecap="round" opacity="${opacity}">`,
    `<line x1="${cx}" y1="${y}" x2="${cx}" y2="${y + height}" stroke-width="${Math.max(2, width * 0.12)}"/>`,
    `<line x1="${x}" y1="${cy}" x2="${x + width}" y2="${cy}" stroke-width="${Math.max(2, height * 0.12)}"/>`,
    `<circle cx="${cx}" cy="${cy}" r="${Math.max(1.5, Math.min(width, height) * 0.1)}" fill="${fill}" stroke="none"/>`,
    '</g>',
  ].join('')
}

function renderPlanet(x, y, width, height, fill, opacity) {
  const cx = x + width / 2
  const cy = y + height / 2
  const radius = Math.min(width, height) * 0.34
  return [
    `<g data-shape="planet" opacity="${opacity}">`,
    `<circle cx="${cx}" cy="${cy}" r="${radius}" fill="${fill}"/>`,
    `<ellipse cx="${cx}" cy="${cy}" rx="${width * 0.48}" ry="${height * 0.18}" fill="none" stroke="${fill}" stroke-width="${Math.max(2, width * 0.06)}" transform="rotate(-18 ${cx} ${cy})"/>`,
    '</g>',
  ].join('')
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
  if (layer.shape === 'crescent') return renderCrescent(layer, x, y, width, height, fill, opacity)
  if (layer.shape === 'heart') return renderHeart(x, y, width, height, fill, opacity)
  if (layer.shape === 'cloud') return renderCloud(x, y, width, height, fill, opacity)
  if (layer.shape === 'sparkle') return renderSparkle(x, y, width, height, fill, opacity)
  if (layer.shape === 'planet') return renderPlanet(x, y, width, height, fill, opacity)
  if (layer.shape === 'blob') {
    return `<ellipse cx="${x + width / 2}" cy="${y + height / 2}" rx="${width / 2}" ry="${height / 2}" fill="${fill}" opacity="${opacity}" filter="url(#soft-blur)"/>`
  }
  return `<rect x="${x}" y="${y}" width="${width}" height="${height}" rx="${number(layer.radius, 24)}" fill="${fill}" opacity="${opacity}"/>`
}

function normalized(value, fallback = 0) {
  return Math.max(0, Math.min(1, number(value, fallback)))
}

function compoundTransform(part, x, y, width, height) {
  const rotation = number(part.rotation)
  if (!rotation) return ''
  const centerX = x + width / 2
  const centerY = y + height / 2
  return ` transform="rotate(${rotation} ${centerX} ${centerY})"`
}

function renderCompoundPart(part, width, height) {
  const x = normalized(part.x) * width
  const y = normalized(part.y) * height
  const partWidth = normalized(part.width) * width
  const partHeight = normalized(part.height) * height
  const fill = escapeXml(part.fill || 'transparent')
  const stroke = escapeXml(part.stroke || 'transparent')
  const opacity = normalized(part.opacity, 1)
  const strokeWidth = Math.max(
    0,
    normalized(part.strokeWidth) * Math.min(width, height),
  )
  const transform = compoundTransform(
    part,
    x,
    y,
    partWidth,
    partHeight,
  )

  if (part.shape === 'circle') {
    return `<circle cx="${x + partWidth / 2}" cy="${y + partHeight / 2}" r="${Math.min(partWidth, partHeight) / 2}" fill="${fill}" stroke="${stroke}" stroke-width="${strokeWidth}" opacity="${opacity}"${transform}/>`
  }
  if (part.shape === 'ellipse') {
    return `<ellipse cx="${x + partWidth / 2}" cy="${y + partHeight / 2}" rx="${partWidth / 2}" ry="${partHeight / 2}" fill="${fill}" stroke="${stroke}" stroke-width="${strokeWidth}" opacity="${opacity}"${transform}/>`
  }
  if (part.shape === 'rect' || part.shape === 'roundedRect') {
    const radius = part.shape === 'roundedRect'
      ? normalized(part.radius, 0.12) * Math.min(width, height)
      : 0
    return `<rect x="${x}" y="${y}" width="${partWidth}" height="${partHeight}" rx="${radius}" fill="${fill}" stroke="${stroke}" stroke-width="${strokeWidth}" opacity="${opacity}"${transform}/>`
  }
  if (part.shape === 'triangle' || part.shape === 'polygon') {
    const points = (part.points || [])
      .map((point) => `${normalized(point?.[0]) * width},${normalized(point?.[1]) * height}`)
      .join(' ')
    return `<polygon points="${points}" fill="${fill}" stroke="${stroke}" stroke-width="${strokeWidth}" opacity="${opacity}"/>`
  }
  if (part.shape === 'line') {
    return `<line x1="${x}" y1="${y}" x2="${x + partWidth}" y2="${y + partHeight}" stroke="${escapeXml(part.stroke || part.fill || '#ffffff')}" stroke-width="${Math.max(0.5, strokeWidth)}" stroke-linecap="round" opacity="${opacity}"${transform}/>`
  }
  return ''
}

function renderCompoundShape(layer) {
  const x = number(layer.x)
  const y = number(layer.y)
  const width = number(layer.width, 168)
  const height = number(layer.height, 176)
  const parts = Array.isArray(layer.parts)
    ? layer.parts
        .map((part) => renderCompoundPart(part, width, height))
        .join('')
    : ''
  return `<g data-compound-target="${escapeXml(layer.target || layer.id || '')}" transform="translate(${x} ${y})" opacity="${number(layer.opacity, 1)}">${parts}</g>`
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

function safeId(value = '') {
  return String(value).replace(/[^a-zA-Z0-9_-]/g, '-')
}

function namespaceSvgClasses(svg, assetId) {
  const prefix = `asset-${safeId(assetId)}-`
  return svg
    .replaceAll(/\.cls-/g, `.${prefix}cls-`)
    .replaceAll(/class=(["'])cls-/g, `class=$1${prefix}cls-`)
}

function embeddedSvgMarkup(svgText, layer) {
  const cleaned = String(svgText || '')
    .replace(/<\?xml[\s\S]*?\?>/gi, '')
    .replace(/<!--[\s\S]*?-->/g, '')
    .trim()
  const match = cleaned.match(/<svg\b([^>]*)>([\s\S]*?)<\/svg>\s*$/i)
  if (!match) throw new Error(`素材 ${layer.assetId || layer.src} 不是有效 SVG`)

  const viewBoxMatch = match[1].match(/\bviewBox=(["'])(.*?)\1/i)
  const viewBox = viewBoxMatch?.[2] || '0 0 600 600'
  const x = number(layer.x)
  const y = number(layer.y)
  const width = number(layer.width, 120)
  const height = number(layer.height, width)
  const rotation = number(layer.rotation)
  const opacity = number(layer.opacity, 1)
  const centerX = x + width / 2
  const centerY = y + height / 2
  const inner = namespaceSvgClasses(match[2], layer.assetId || layer.id)

  return `<svg data-asset-id="${escapeXml(layer.assetId)}" x="${x}" y="${y}" width="${width}" height="${height}" viewBox="${escapeXml(viewBox)}" preserveAspectRatio="xMidYMid meet" opacity="${opacity}" transform="rotate(${rotation} ${centerX} ${centerY})">${inner}</svg>`
}

async function defaultAssetLoader(src) {
  const response = await fetch(src)
  if (!response.ok) {
    throw new Error(`读取素材失败：${src} (${response.status})`)
  }
  return response.text()
}

async function defaultFrameDataUrl(src) {
  const response = await fetch(src)
  if (!response.ok) {
    throw new Error(`读取动画代表帧失败：${src} (${response.status})`)
  }
  const blob = await response.blob()
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => resolve(String(reader.result || ''))
    reader.onerror = () => reject(reader.error || new Error(`读取动画代表帧失败：${src}`))
    reader.readAsDataURL(blob)
  })
}

async function renderAsset(layer, loadAssetSvg) {
  if (!layer.src || !layer.assetId) return ''
  const svgText = await loadAssetSvg(layer.src, layer)
  return embeddedSvgMarkup(svgText, layer)
}

async function renderFrameAnimation(layer, loadFrameDataUrl) {
  const frames = Array.isArray(layer.frames) ? layer.frames : []
  const poster = layer.poster || frames[Math.floor(frames.length / 2)] || frames[0]
  if (!poster) return ''

  const dataUrl = await loadFrameDataUrl(poster, layer)
  const x = number(layer.x)
  const y = number(layer.y)
  const width = number(layer.width, 120)
  const height = number(layer.height, width)
  const opacity = number(layer.opacity, 1)
  const rotation = number(layer.rotation)
  const centerX = x + width / 2
  const centerY = y + height / 2
  const preserveAspectRatio = layer.fit === 'cover' ? 'xMidYMid slice' : 'xMidYMid meet'
  return `<image data-asset-id="${escapeXml(layer.assetId)}" x="${x}" y="${y}" width="${width}" height="${height}" href="${escapeXml(dataUrl)}" preserveAspectRatio="${preserveAspectRatio}" opacity="${opacity}" transform="rotate(${rotation} ${centerX} ${centerY})"/>`
}

async function renderLayer(layer, loadAssetSvg, loadFrameDataUrl) {
  if (layer?.type === 'text') return renderText(layer)
  if (layer?.type === 'shape') return renderShape(layer)
  if (layer?.type === 'compoundShape') return renderCompoundShape(layer)
  if (layer?.type === 'widget' || layer?.type === 'glassCard') return renderCard(layer)
  if (layer?.type === 'asset') return renderAsset(layer, loadAssetSvg)
  if (layer?.type === 'frameAnimation') {
    return renderFrameAnimation(layer, loadFrameDataUrl)
  }
  return ''
}

export async function dslToSvg(dsl, options = {}) {
  const width = number(dsl?.canvas?.width, 390)
  const height = number(dsl?.canvas?.height, 844)
  const background = backgroundMarkup(dsl?.background, width, height)
  const loadAssetSvg = options.loadAssetSvg || defaultAssetLoader
  const loadFrameDataUrl = options.loadFrameDataUrl || defaultFrameDataUrl
  const renderedLayers = Array.isArray(dsl?.layers)
    ? await Promise.all(
        dsl.layers.map((layer) =>
          renderLayer(layer, loadAssetSvg, loadFrameDataUrl),
        ),
      )
    : []
  const layers = renderedLayers.join('')

  return [
    '<?xml version="1.0" encoding="UTF-8"?>',
    `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">`,
    `<defs>${background.defs}<filter id="soft-blur"><feGaussianBlur stdDeviation="24"/></filter></defs>`,
    background.markup,
    layers,
    '</svg>',
  ].join('')
}

export async function downloadSvg(dsl) {
  const svg = await dslToSvg(dsl)
  const blob = new Blob([svg], { type: 'image/svg+xml;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.download = 'lockscreen.svg'
  link.href = url
  link.click()
  URL.revokeObjectURL(url)
}
