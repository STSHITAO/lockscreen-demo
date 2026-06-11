<script setup>
import { ref } from 'vue'

import { exportJpeg, exportPng } from '../core/exportImage.js'
import { downloadSvg } from '../core/exportSvg.js'

const props = defineProps({
  dsl: {
    type: Object,
    required: true,
  },
  getTarget: {
    type: Function,
    required: true,
  },
})

const busy = ref('')
const error = ref('')

async function runExport(type) {
  busy.value = type
  error.value = ''
  try {
    if (type === 'svg') {
      await downloadSvg(props.dsl)
    } else if (type === 'png') {
      await exportPng(props.getTarget())
    } else {
      await exportJpeg(props.getTarget())
    }
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : '导出失败'
  } finally {
    busy.value = ''
  }
}
</script>

<template>
  <section class="export-panel">
    <div class="export-heading">
      <div>
        <span class="eyebrow">EXPORT</span>
        <h2>导出锁屏</h2>
      </div>
      <span class="export-size">390 × 844</span>
    </div>

    <div class="export-actions">
      <button type="button" :disabled="Boolean(busy)" @click="runExport('svg')">
        {{ busy === 'svg' ? '处理中…' : '导出 SVG/XML' }}
      </button>
      <button type="button" :disabled="Boolean(busy)" @click="runExport('png')">
        {{ busy === 'png' ? '处理中…' : '导出 PNG' }}
      </button>
      <button type="button" :disabled="Boolean(busy)" @click="runExport('jpeg')">
        {{ busy === 'jpeg' ? '处理中…' : '导出 JPEG' }}
      </button>
    </div>

    <p v-if="error" class="export-error">{{ error }}</p>
  </section>
</template>
