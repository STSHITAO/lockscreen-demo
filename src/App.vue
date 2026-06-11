<script setup>
import { computed, ref } from 'vue'

import ExportPanel from './components/ExportPanel.vue'
import LockScreenPreview from './components/LockScreenPreview.vue'
import fallbackDSL from './core/fallbackDSL.js'

const DEFAULT_PROMPT =
  '生成一个夜晚星空风格锁屏，有月亮和星星，整体深色高级一点，底部显示天气卡片。'

const prompt = ref(DEFAULT_PROMPT)
const dsl = ref(structuredClone(fallbackDSL))
const loading = ref(false)
const error = ref('')
const previewRef = ref(null)

const formattedDsl = computed(() => JSON.stringify(dsl.value, null, 2))

async function generateLockScreen() {
  if (!prompt.value.trim() || loading.value) return

  loading.value = true
  error.value = ''
  try {
    const response = await fetch('http://localhost:8000/api/generate-lockscreen', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: prompt.value.trim() }),
    })
    if (!response.ok) {
      throw new Error(`后端请求失败（HTTP ${response.status}）`)
    }
    const result = await response.json()
    if (!result || !Array.isArray(result.layers)) {
      throw new Error('后端返回的 DSL 格式无效')
    }
    dsl.value = result
  } catch (reason) {
    dsl.value = structuredClone(fallbackDSL)
    error.value = `${reason instanceof Error ? reason.message : '生成失败'}，已切换到本地 fallback DSL。`
  } finally {
    loading.value = false
  }
}

function getPreviewElement() {
  return previewRef.value?.screenElement || null
}
</script>

<template>
  <main class="studio">
    <header class="topbar">
      <div class="brand-mark">LS</div>
      <div>
        <p class="product-kicker">LOCKSCREEN LAB / LOCAL DEMO</p>
        <h1>自然语言生成锁屏 DSL</h1>
      </div>
      <div class="pipeline-status">
        <span class="status-dot"></span>
        JSON-driven
      </div>
    </header>

    <div class="workspace">
      <section class="control-column">
        <div class="panel prompt-panel">
          <div class="section-heading">
            <div>
              <span class="eyebrow">01 / PROMPT</span>
              <h2>描述你想要的锁屏</h2>
            </div>
            <span class="model-tag">TEXT → DSL</span>
          </div>

          <textarea
            v-model="prompt"
            aria-label="锁屏生成提示词"
            :disabled="loading"
            @keydown.ctrl.enter="generateLockScreen"
          ></textarea>

          <div class="prompt-footer">
            <span>Ctrl + Enter 快速生成</span>
            <button
              class="generate-button"
              type="button"
              :disabled="loading || !prompt.trim()"
              @click="generateLockScreen"
            >
              <span v-if="loading" class="spinner"></span>
              {{ loading ? '模型生成中…' : '生成锁屏' }}
            </button>
          </div>

          <p v-if="error" class="error-message">{{ error }}</p>
        </div>

        <div class="panel dsl-panel">
          <div class="section-heading">
            <div>
              <span class="eyebrow">02 / LOCKSCREEN DSL</span>
              <h2>实时 JSON</h2>
            </div>
            <span class="valid-tag">JSON</span>
          </div>
          <pre><code>{{ formattedDsl }}</code></pre>
        </div>
      </section>

      <section class="preview-column">
        <div class="preview-heading">
          <div>
            <span class="eyebrow">03 / PREVIEW</span>
            <h2>手机锁屏预览</h2>
          </div>
          <span class="theme-chip">{{ dsl.theme || 'custom' }}</span>
        </div>

        <div class="preview-stage">
          <div class="stage-grid"></div>
          <LockScreenPreview ref="previewRef" :dsl="dsl" />
        </div>

        <ExportPanel :dsl="dsl" :get-target="getPreviewElement" />
      </section>
    </div>
  </main>
</template>
