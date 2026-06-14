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

test('exports controlled fallback shapes as SVG primitives', async () => {
  const dsl = {
    canvas: { width: 390, height: 844 },
    background: { type: 'color', value: '#020617' },
    layers: [
      { id: 'moon', type: 'shape', shape: 'crescent', x: 30, y: 70, width: 64, height: 64 },
      { id: 'star', type: 'shape', shape: 'star', x: 290, y: 90, width: 24, height: 24 },
      { id: 'heart', type: 'shape', shape: 'heart', x: 320, y: 140, width: 34, height: 30 },
      { id: 'cloud', type: 'shape', shape: 'cloud', x: 24, y: 300, width: 90, height: 48 },
      { id: 'sparkle', type: 'shape', shape: 'sparkle', x: 300, y: 340, width: 28, height: 28 },
      { id: 'planet', type: 'shape', shape: 'planet', x: 140, y: 430, width: 88, height: 70 },
    ],
  }

  const svg = await dslToSvg(dsl)

  assert.match(svg, /data-shape="crescent"/)
  assert.match(svg, /data-shape="star"/)
  assert.match(svg, /data-shape="heart"/)
  assert.match(svg, /data-shape="cloud"/)
  assert.match(svg, /data-shape="sparkle"/)
  assert.match(svg, /data-shape="planet"/)
  assert.match(svg, /<path/)
  assert.match(svg, /<ellipse/)
})

test('exports a frame animation as its embedded poster frame', async () => {
  const dsl = {
    canvas: { width: 390, height: 844 },
    background: { type: 'color', value: '#020617' },
    layers: [
      {
        id: 'twinkle',
        type: 'frameAnimation',
        assetId: 'frame-star-twinkle-001',
        frames: ['/materials/frames/star_twinkle/01.png'],
        poster: '/materials/frames/star_twinkle/03.png',
        x: 270,
        y: 280,
        width: 92,
        height: 92,
        opacity: 0.9,
      },
    ],
  }

  const svg = await dslToSvg(dsl, {
    loadFrameDataUrl: async () => 'data:image/png;base64,AAAA',
  })

  assert.match(svg, /data-asset-id="frame-star-twinkle-001"/)
  assert.match(svg, /href="data:image\/png;base64,AAAA"/)
  assert.match(svg, /x="270" y="280" width="92" height="92"/)
})

test('exports a stable visual state without interaction handlers', async () => {
  const svg = await dslToSvg({
    canvas: { width: 390, height: 844 },
    background: { type: 'color', value: '#020617' },
    layers: [
      {
        id: 'heart',
        type: 'shape',
        shape: 'heart',
        x: 280,
        y: 80,
        width: 52,
        height: 48,
        color: '#fb7185',
      },
    ],
    interactions: [
      {
        id: 'heart-tap',
        targetId: 'heart',
        trigger: { type: 'tap' },
        actions: [{ type: 'animate', animation: 'pulse' }],
      },
    ],
  })

  assert.match(svg, /data-shape="heart"/)
  assert.doesNotMatch(svg, /heart-tap|onclick|script|interaction/)
})
