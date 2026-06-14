<script setup>
import { computed, ref } from 'vue'

import ExportPanel from './components/ExportPanel.vue'
import LockScreenPreview from './components/LockScreenPreview.vue'
import fallbackDSL from './core/fallbackDSL.js'
import { createSseParser } from './core/streamEvents.js'

const DEFAULT_PROMPT =
  '生成一个夜晚星空风格锁屏，有月亮和星星，整体深色高级一点，底部显示天气卡片。'

const prompt = ref(DEFAULT_PROMPT)
const dsl = ref(structuredClone(fallbackDSL))
const loading = ref(false)
const error = ref('')
const previewRef = ref(null)
const agentSteps = ref([])
const thinkingText = ref('')
const streamMessage = ref('等待开始')

const formattedDsl = computed(() => JSON.stringify(dsl.value, null, 2))

function updateStep(key, label, status, detail = '') {
  const existing = agentSteps.value.find((step) => step.key === key)
  if (existing) {
    Object.assign(existing, { label, status, detail })
    return
  }
  agentSteps.value.push({ key, label, status, detail })
}

function handleStreamEvent(event) {
  if (event.type === 'thinking') {
    thinkingText.value = `${thinkingText.value}${event.delta || ''}`.slice(-16000)
    streamMessage.value = event.phase === 'intent' ? '模型正在理解需求' : '模型正在设计布局'
    return
  }
  if (event.type === 'phase') {
    updateStep(event.phase, event.label || event.phase, event.status)
    streamMessage.value = event.label || streamMessage.value
    return
  }
  if (event.type === 'progress') {
    streamMessage.value = event.message || '正在生成结构化结果'
    return
  }
  if (event.type === 'validation') {
    const count = event.errors?.length || 0
    updateStep(
      `validation-${event.round}`,
      event.ok ? 'DSL 校验通过' : `发现 ${count} 个问题`,
      event.ok ? 'done' : 'warning',
      event.ok ? '' : '准备进入受控修复',
    )
    return
  }
  if (event.type === 'fallback_draw') {
    const targets = Array.isArray(event.targets) ? event.targets.join(' / ') : 'visual'
    const label = `素材缺失，已绘制 ${targets}`
    updateStep('fallback-draw', label, 'done', '使用受控 DSL shape')
    streamMessage.value = label
    return
  }
  if (event.type === 'animation_fallback') {
    const descriptions = (event.animations || [])
      .map((item) => `${item.target}: ${item.motion}`)
      .join(' / ')
    const label = `已使用简单动画托底${descriptions ? `：${descriptions}` : ''}`
    updateStep('animation-fallback', label, 'done', '使用受控 CSS 动画')
    streamMessage.value = label
    return
  }
  if (event.type === 'animation_unavailable') {
    for (const notice of event.notices || []) {
      updateStep(
        `animation-unavailable-${notice.target}`,
        `动画暂不可用：${notice.target}`,
        'warning',
        notice.message,
      )
    }
    streamMessage.value =
      event.notices?.[0]?.message || '部分复杂动画暂时无法自主生成'
    return
  }
  if (event.type === 'interaction_ready') {
    const descriptions = (event.interactions || [])
      .map((item) => `${item.target}: ${item.trigger}`)
      .join(' / ')
    const label = `交互动作已就绪${descriptions ? `：${descriptions}` : ''}`
    updateStep('interaction-ready', label, 'done', '使用受控 Trigger + Action DSL')
    streamMessage.value = label
    return
  }
  if (event.type === 'interaction_unavailable') {
    for (const notice of event.notices || []) {
      updateStep(
        `interaction-unavailable-${notice.target}`,
        `交互暂不可用：${notice.target}`,
        'warning',
        notice.message,
      )
    }
    streamMessage.value =
      event.notices?.[0]?.message || '部分复杂交互暂时无法自主生成'
    return
  }
  if (event.type === 'repair') {
    updateStep(`repair-${event.round}`, event.label, event.status)
    streamMessage.value = event.label
    return
  }
  if (event.type === 'error') {
    updateStep(`error-${agentSteps.value.length}`, event.message, 'error')
    streamMessage.value = event.message
    return
  }
  if (event.type === 'final') {
    if (!event.dsl || !Array.isArray(event.dsl.layers)) {
      throw new Error('后端返回的最终 DSL 格式无效')
    }
    dsl.value = event.dsl
    for (const notice of event.dsl._debug?.animationNotices || []) {
      updateStep(
        `animation-unavailable-${notice.target}`,
        `动画暂不可用：${notice.target}`,
        'warning',
        notice.message,
      )
    }
    for (const notice of event.dsl._debug?.interactionNotices || []) {
      updateStep(
        `interaction-unavailable-${notice.target}`,
        `交互暂不可用：${notice.target}`,
        'warning',
        notice.message,
      )
    }
    updateStep(
      'final',
      event.dsl._debug?.usedFallback ? '已返回安全 fallback' : '锁屏生成完成',
      event.dsl._debug?.usedFallback ? 'warning' : 'done',
    )
    streamMessage.value = event.dsl._debug?.usedFallback ? '生成结束，已使用 fallback' : '生成完成'
  }
}

async function generateLockScreen() {
  if (!prompt.value.trim() || loading.value) return

  loading.value = true
  error.value = ''
  agentSteps.value = []
  thinkingText.value = ''
  streamMessage.value = '正在连接模型'
  let receivedFinal = false
  try {
    const response = await fetch('http://localhost:8000/api/generate-lockscreen/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: prompt.value.trim() }),
    })
    if (!response.ok) {
      throw new Error(`后端请求失败（HTTP ${response.status}）`)
    }
    if (!response.body) {
      throw new Error('浏览器不支持流式响应')
    }

    const parser = createSseParser((event) => {
      handleStreamEvent(event)
      if (event.type === 'final') receivedFinal = true
    })
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      parser.push(decoder.decode(value, { stream: true }))
    }
    parser.push(decoder.decode())
    parser.finish()
    if (!receivedFinal) throw new Error('模型流已结束，但没有收到最终锁屏')
  } catch (reason) {
    dsl.value = structuredClone(fallbackDSL)
    const message = reason instanceof Error ? reason.message : '生成失败'
    error.value = `${message}，已切换到本地 fallback DSL。`
    updateStep('local-fallback', '前端使用本地 fallback', 'error', message)
    streamMessage.value = '生成中断'
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

        <div class="panel agent-panel">
          <div class="section-heading">
            <div>
              <span class="eyebrow">02 / AGENT RUN</span>
              <h2>生成过程</h2>
            </div>
            <span class="valid-tag">{{ loading ? 'STREAMING' : 'READY' }}</span>
          </div>

          <div class="agent-status">
            <span :class="['status-dot', { active: loading }]"></span>
            {{ streamMessage }}
          </div>

          <div v-if="agentSteps.length" class="agent-timeline">
            <div
              v-for="step in agentSteps"
              :key="step.key"
              :class="['agent-step', `step-${step.status}`]"
            >
              <span class="step-marker"></span>
              <div>
                <strong>{{ step.label }}</strong>
                <p v-if="step.detail">{{ step.detail }}</p>
              </div>
            </div>
          </div>
          <p v-else class="agent-empty">输入需求后，这里会实时显示模型思考、素材检索、校验与修复过程。</p>

          <section v-if="thinkingText" class="thinking-panel">
            <div class="thinking-heading">
              <span>MODEL THINKING</span>
              <span class="thinking-live">{{ loading ? 'LIVE' : 'DONE' }}</span>
            </div>
            <pre>{{ thinkingText }}</pre>
          </section>

          <details class="debug-details">
            <summary>查看最终 DSL / Debug</summary>
            <pre><code>{{ formattedDsl }}</code></pre>
          </details>
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
