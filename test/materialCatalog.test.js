import assert from 'node:assert/strict'
import { readdir, readFile } from 'node:fs/promises'
import test from 'node:test'

import { searchAssets } from '../src/core/materialSearch.js'

const materialsUrl = new URL('../public/materials/', import.meta.url)
const svgUrl = new URL('./svg/', materialsUrl)

async function loadAssets() {
  return JSON.parse(await readFile(new URL('./assets.json', materialsUrl), 'utf8'))
}

test('catalog contains exactly one complete record for every SVG file', async () => {
  const assets = await loadAssets()
  const svgFiles = (await readdir(svgUrl)).filter((file) => file.endsWith('.svg')).sort()
  const catalogFiles = assets.map((asset) => asset.file).sort()

  assert.equal(assets.length, 151)
  assert.deepEqual(catalogFiles, svgFiles)
  assert.equal(new Set(assets.map((asset) => asset.assetId)).size, assets.length)

  for (const asset of assets) {
    assert.match(asset.assetId, /^doodle-\d{3}$/)
    assert.equal(asset.width, 600)
    assert.equal(asset.height, 600)
    assert.equal(asset.transparent, true)
    assert.equal(asset.recolorable, true)
    assert.ok(asset.name.zh)
    assert.ok(asset.name.en)
    assert.ok(asset.description)
    assert.ok(asset.category)
    assert.ok(asset.subjects.length > 0)
    assert.ok(asset.keywords.length > 0)
    assert.ok(asset.themes.length > 0)
    assert.ok(asset.moods.length > 0)
    assert.ok(asset.roles.length > 0)
    assert.ok(asset.colors.length > 0)
    assert.ok(asset.recommendedPositions.length > 0)
    assert.ok(['light', 'medium', 'heavy'].includes(asset.visualWeight))
  }
})

test('search finds assets by Chinese keywords and structured filters', async () => {
  const assets = await loadAssets()

  const rocketResults = searchAssets(assets, {
    query: '可爱的太空火箭',
    themes: ['space'],
    roles: ['hero'],
    limit: 5,
  })

  assert.equal(rocketResults[0].assetId, 'doodle-034')

  const callouts = searchAssets(assets, {
    roles: ['callout'],
    limit: 20,
  })

  assert.ok(callouts.some((asset) => asset.assetId === 'doodle-150'))
  assert.ok(callouts.every((asset) => asset.roles.includes('callout')))

  const ufoResults = searchAssets(assets, {
    subjects: ['ufo'],
    limit: 10,
  })

  assert.deepEqual(ufoResults.map((asset) => asset.assetId), ['doodle-057'])
})
