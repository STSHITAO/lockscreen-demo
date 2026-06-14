import { readdir, writeFile } from 'node:fs/promises'
import path from 'node:path'
import { fileURLToPath } from 'node:url'

const rootDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..')
const materialsDir = path.join(rootDir, 'public', 'materials')
const directory = 'star_twinkle'
const frameDir = path.join(materialsDir, 'frames', directory)
const frameFiles = (await readdir(frameDir))
  .filter((file) => file.toLowerCase().endsWith('.png'))
  .sort()

if (frameFiles.length !== 5) {
  throw new Error(`star_twinkle requires 5 PNG frames, found ${frameFiles.length}`)
}

const frames = frameFiles.map(
  (file) => `/materials/frames/${directory}/${file}`,
)
const animations = [
  {
    assetId: 'frame-star-twinkle-001',
    assetType: 'frameSequence',
    directory,
    name: {
      zh: '闪烁发光星星',
      en: 'Twinkling glowing star',
    },
    description:
      '黄色五角星由小变大并发出柔和光晕与放射光芒，再缩小复位的透明背景循环序列帧，适合作为动态锁屏的星光装饰。',
    category: 'space',
    subjects: ['star', 'sparkle'],
    keywords: [
      '星星',
      '闪烁',
      '发光',
      '星光',
      '闪光',
      '五角星',
      'twinkle',
      'glowing star',
      'sparkle',
    ],
    themes: ['night', 'space', 'cute', 'dreamy'],
    moods: ['magical', 'cheerful', 'dreamy'],
    roles: ['decoration', 'animated-accent'],
    colors: ['yellow', 'gold'],
    recommendedPositions: ['top-left', 'top-right', 'around'],
    visualWeight: 'light',
    style: ['soft-glow', 'minimal', 'celestial'],
    width: 1254,
    height: 1254,
    transparent: true,
    recolorable: false,
    containsText: false,
    frameCount: frames.length,
    fps: 6,
    loop: true,
    frames,
    poster: frames[2],
  },
]

await writeFile(
  path.join(materialsDir, 'animations.json'),
  `${JSON.stringify(animations, null, 2)}\n`,
  'utf8',
)
console.log(`Generated ${animations.length} animation material record.`)
