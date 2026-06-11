function list(value) {
  return Array.isArray(value) ? value : []
}

function normalize(value) {
  return String(value || '').trim().toLowerCase()
}

function matchesFilter(asset, field, requested) {
  const filters = list(requested).map(normalize).filter(Boolean)
  if (!filters.length) return true
  const values = list(asset[field]).map(normalize)
  return filters.every((filter) => values.includes(filter))
}

function searchableTerms(asset) {
  return [
    asset.assetId,
    asset.name?.zh,
    asset.name?.en,
    asset.description,
    asset.category,
    ...list(asset.subjects),
    ...list(asset.keywords),
    ...list(asset.themes),
    ...list(asset.moods),
    ...list(asset.roles),
    ...list(asset.colors),
    ...list(asset.style),
  ]
    .map(normalize)
    .filter(Boolean)
}

export function searchAssets(assets, options = {}) {
  const query = normalize(options.query)
  const queryTokens = query.split(/\s+/).filter(Boolean)
  const limit = Math.max(1, Number(options.limit) || 20)

  return list(assets)
    .filter((asset) => matchesFilter(asset, 'themes', options.themes))
    .filter((asset) => matchesFilter(asset, 'subjects', options.subjects))
    .filter((asset) => matchesFilter(asset, 'roles', options.roles))
    .filter((asset) => matchesFilter(asset, 'moods', options.moods))
    .filter((asset) => matchesFilter(asset, 'colors', options.colors))
    .filter((asset) => {
      const categories = list(options.categories).map(normalize).filter(Boolean)
      return !categories.length || categories.includes(normalize(asset.category))
    })
    .map((asset) => {
      const terms = searchableTerms(asset)
      const haystack = terms.join(' ')
      let score = 0

      for (const token of queryTokens) {
        if (haystack.includes(token)) score += 8
      }
      for (const term of terms) {
        if (query && (query.includes(term) || term.includes(query))) score += 3
      }
      if (query && normalize(asset.name?.zh) && query.includes(normalize(asset.name.zh))) {
        score += 12
      }
      if (query && normalize(asset.name?.en) && query.includes(normalize(asset.name.en))) {
        score += 12
      }

      return { asset, score }
    })
    .filter(({ score }) => !query || score > 0)
    .sort((left, right) => right.score - left.score || left.asset.assetId.localeCompare(right.asset.assetId))
    .slice(0, limit)
    .map(({ asset }) => asset)
}
