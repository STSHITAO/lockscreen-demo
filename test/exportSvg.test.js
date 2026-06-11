import assert from 'node:assert/strict'
import test from 'node:test'

import { readFile } from 'node:fs/promises'

import { dslToSvg } from '../src/core/exportSvg.js'

test('converts gradient, text, shape, widget and glass card layers to SVG', async () => {
  const dsl = {
    canvas: { width: 390, height: 844 },
    background: {
      type: 'gradient',
      value: 'linear-gradient(180deg, #0f172a 0%, #020617 100%)',
    },
    layers: [
      {
        id: 'title',
        type: 'text',
        content: 'Night & Sky',
        x: 195,
        y: 120,
        fontSize: 30,
        color: '#fff',
        align: 'center',
      },
      { id: 'moon', type: 'shape', shape: 'circle', x: 280, y: 80, width: 50, height: 50 },
      { id: 'line', type: 'shape', shape: 'line', x: 20, y: 300, width: 100, height: 2 },
      {
        id: 'weather',
        type: 'widget',
        x: 32,
        y: 690,
        width: 326,
        height: 96,
        content: { title: 'Weather', main: '26 C', icon: '*' },
      },
      {
        id: 'card',
        type: 'glassCard',
        x: 32,
        y: 560,
        width: 326,
        height: 80,
        content: { title: 'Agenda', main: 'No events' },
      },
    ],
  }

  const svg = await dslToSvg(dsl)

  assert.match(svg, /<linearGradient/)
  assert.match(svg, /Night &amp; Sky/)
  assert.match(svg, /<circle/)
  assert.match(svg, /<line/)
  assert.match(svg, /Weather/)
  assert.match(svg, /Agenda/)
  assert.match(svg, /width="390" height="844"/)
})

test('embeds a catalog SVG asset into the exported lockscreen', async () => {
  const dsl = {
    canvas: { width: 390, height: 844 },
    background: { type: 'color', value: '#020617' },
    layers: [
      {
        id: 'rocket',
        type: 'asset',
        assetId: 'doodle-034',
        src: '/materials/svg/doodle-34.svg',
        x: 70,
        y: 330,
        width: 250,
        height: 250,
        rotation: -8,
        opacity: 0.9,
      },
    ],
  }

  const svg = await dslToSvg(dsl, {
    loadAssetSvg: async (src) =>
      readFile(new URL(`../public${src}`, import.meta.url), 'utf8'),
  })

  assert.match(svg, /data-asset-id="doodle-034"/)
  assert.match(svg, /<svg[^>]+x="70"[^>]+y="330"/)
  assert.match(svg, /rotate\(-8 195 455\)/)
  assert.doesNotMatch(svg, /href="\/materials\//)
})
