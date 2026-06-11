import { toJpeg, toPng } from 'html-to-image'

function downloadDataUrl(dataUrl, filename) {
  const link = document.createElement('a')
  link.download = filename
  link.href = dataUrl
  link.click()
}

function exportOptions() {
  return {
    width: 390,
    height: 844,
    pixelRatio: 2,
    cacheBust: true,
  }
}

export async function exportPng(element) {
  if (!element) throw new Error('锁屏预览尚未准备好')
  const dataUrl = await toPng(element, exportOptions())
  downloadDataUrl(dataUrl, 'lockscreen.png')
}

export async function exportJpeg(element) {
  if (!element) throw new Error('锁屏预览尚未准备好')
  const dataUrl = await toJpeg(element, {
    ...exportOptions(),
    quality: 0.95,
    backgroundColor: '#020617',
  })
  downloadDataUrl(dataUrl, 'lockscreen.jpeg')
}
