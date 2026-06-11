<script setup>
import { computed, ref } from 'vue'

const props = defineProps({
  dsl: {
    type: Object,
    required: true,
  },
})

const screenElement = ref(null)

defineExpose({ screenElement })

const canvasStyle = computed(() => ({
  width: `${props.dsl?.canvas?.width || 390}px`,
  height: `${props.dsl?.canvas?.height || 844}px`,
  background:
    props.dsl?.background?.value ||
    'linear-gradient(180deg, #0f172a 0%, #020617 100%)',
}))

function numeric(value, fallback = 0) {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : fallback
}

function animationClass(layer) {
  return ['float', 'pulse', 'rotate'].includes(layer.animation)
    ? `animation-${layer.animation}`
    : ''
}

function textStyle(layer) {
  const translate =
    layer.align === 'left' ? 'translateX(0)' : layer.align === 'right' ? 'translateX(-100%)' : 'translateX(-50%)'
  return {
    left: `${numeric(layer.x)}px`,
    top: `${numeric(layer.y)}px`,
    color: layer.color || '#ffffff',
    fontSize: `${numeric(layer.fontSize, 16)}px`,
    fontWeight: numeric(layer.fontWeight, 400),
    textAlign: layer.align || 'center',
    transform: translate,
    opacity: numeric(layer.opacity, 1),
  }
}

function boxStyle(layer) {
  return {
    left: `${numeric(layer.x)}px`,
    top: `${numeric(layer.y)}px`,
    width: `${numeric(layer.width, 20)}px`,
    height: `${numeric(layer.height, layer.width || 20)}px`,
    color: layer.color || '#ffffff',
    background: layer.color || undefined,
    opacity: numeric(layer.opacity, 1),
    borderRadius: layer.radius ? `${numeric(layer.radius)}px` : undefined,
  }
}

function lineStyle(layer) {
  const dx = numeric(layer.width, 40)
  const dy = numeric(layer.height, 0)
  return {
    left: `${numeric(layer.x)}px`,
    top: `${numeric(layer.y)}px`,
    width: `${Math.hypot(dx, dy)}px`,
    height: `${numeric(layer.strokeWidth, 2)}px`,
    background: layer.color || '#ffffff',
    opacity: numeric(layer.opacity, 1),
    transform: `rotate(${Math.atan2(dy, dx)}rad)`,
  }
}

function cardContent(layer) {
  if (typeof layer.content === 'string') {
    return { title: '', main: layer.content, subtitle: '', icon: '' }
  }
  return {
    title: layer.content?.title || '',
    main: layer.content?.main || '',
    subtitle: layer.content?.subtitle || '',
    icon: layer.content?.icon || '',
  }
}
</script>

<template>
  <div class="phone-shell">
    <div ref="screenElement" class="lockscreen" :style="canvasStyle">
      <div class="dynamic-island" aria-hidden="true"></div>
      <div class="lock-indicator" aria-hidden="true">
        <span class="lock-shackle"></span>
        <span class="lock-body"></span>
      </div>

      <template v-for="layer in dsl.layers || []" :key="layer.id">
        <div
          v-if="layer.type === 'text'"
          class="layer text-layer"
          :class="[animationClass(layer), `role-${layer.role || 'text'}`]"
          :style="textStyle(layer)"
        >
          {{ layer.content }}
        </div>

        <div
          v-else-if="layer.type === 'shape' && layer.shape === 'line'"
          class="layer shape-line"
          :class="animationClass(layer)"
          :style="lineStyle(layer)"
        ></div>

        <div
          v-else-if="layer.type === 'shape'"
          class="layer shape-layer"
          :class="[`shape-${layer.shape || 'roundedRect'}`, animationClass(layer)]"
          :style="boxStyle(layer)"
        ></div>

        <div
          v-else-if="layer.type === 'widget' || layer.type === 'glassCard'"
          class="layer glass-card"
          :class="[
            animationClass(layer),
            layer.type === 'widget' ? `widget-${layer.role || 'generic'}` : 'dsl-glass-card',
          ]"
          :style="boxStyle(layer)"
        >
          <div v-if="cardContent(layer).icon" class="card-icon">
            {{ cardContent(layer).icon }}
          </div>
          <div class="card-copy">
            <div v-if="cardContent(layer).title" class="card-title">
              {{ cardContent(layer).title }}
            </div>
            <div v-if="cardContent(layer).main" class="card-main">
              {{ cardContent(layer).main }}
            </div>
            <div v-if="cardContent(layer).subtitle" class="card-subtitle">
              {{ cardContent(layer).subtitle }}
            </div>
          </div>
        </div>
      </template>

      <div class="home-indicator" aria-hidden="true"></div>
    </div>
  </div>
</template>

<style scoped>
.phone-shell {
  width: 390px;
  height: 844px;
  padding: 10px;
  border-radius: 56px;
  background: linear-gradient(145deg, #2b2f37, #07090d 48%, #272b32);
  box-shadow:
    0 36px 80px rgba(0, 0, 0, 0.46),
    inset 0 0 0 1px rgba(255, 255, 255, 0.16);
}

.lockscreen {
  position: relative;
  overflow: hidden;
  border-radius: 47px;
  isolation: isolate;
  color: #ffffff;
  font-family:
    Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  box-shadow: inset 0 0 70px rgba(0, 0, 0, 0.22);
}

.lockscreen::after {
  position: absolute;
  inset: 0;
  z-index: 90;
  pointer-events: none;
  content: "";
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.04), transparent 22%),
    radial-gradient(circle at 50% 110%, rgba(255, 255, 255, 0.08), transparent 34%);
}

.dynamic-island {
  position: absolute;
  top: 13px;
  left: 50%;
  z-index: 100;
  width: 112px;
  height: 30px;
  border-radius: 20px;
  background: #030407;
  transform: translateX(-50%);
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.04);
}

.lock-indicator {
  position: absolute;
  top: 58px;
  left: 50%;
  z-index: 40;
  width: 18px;
  height: 22px;
  transform: translateX(-50%);
  opacity: 0.75;
}

.lock-shackle {
  position: absolute;
  top: 0;
  left: 4px;
  width: 10px;
  height: 10px;
  border: 1.8px solid currentColor;
  border-bottom: 0;
  border-radius: 7px 7px 0 0;
}

.lock-body {
  position: absolute;
  bottom: 0;
  left: 2px;
  width: 14px;
  height: 12px;
  border-radius: 4px;
  background: currentColor;
}

.layer {
  position: absolute;
  z-index: 10;
  box-sizing: border-box;
}

.text-layer {
  max-width: 350px;
  white-space: nowrap;
  line-height: 1;
  letter-spacing: -0.035em;
  text-shadow: 0 3px 16px rgba(0, 0, 0, 0.22);
}

.role-date {
  letter-spacing: 0.01em;
}

.shape-layer {
  transform-origin: center;
}

.shape-circle {
  border-radius: 50%;
  box-shadow: 0 0 34px color-mix(in srgb, currentColor 42%, transparent);
}

.shape-roundedRect {
  border-radius: 24px;
}

.shape-blob {
  border-radius: 42% 58% 64% 36% / 45% 40% 60% 55%;
  filter: blur(26px);
}

.shape-star {
  clip-path: polygon(
    50% 0%,
    61% 35%,
    98% 35%,
    68% 57%,
    79% 94%,
    50% 72%,
    21% 94%,
    32% 57%,
    2% 35%,
    39% 35%
  );
  filter: drop-shadow(0 0 6px currentColor);
}

.shape-line {
  border-radius: 999px;
  transform-origin: left center;
}

.glass-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 20px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.19);
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.105) !important;
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.16),
    0 16px 42px rgba(0, 0, 0, 0.16);
  opacity: 1 !important;
  backdrop-filter: blur(20px) saturate(145%);
}

.glass-card::before {
  position: absolute;
  inset: 0;
  z-index: -1;
  content: "";
  background: linear-gradient(120deg, rgba(255, 255, 255, 0.08), transparent 55%);
}

.card-icon {
  display: grid;
  flex: 0 0 50px;
  width: 50px;
  height: 50px;
  place-items: center;
  font-family: "Segoe UI Symbol", sans-serif;
  font-size: 31px;
  border-radius: 17px;
  background: rgba(255, 255, 255, 0.1);
}

.card-copy {
  min-width: 0;
  text-align: left;
}

.card-title {
  margin-bottom: 5px;
  overflow: hidden;
  color: rgba(255, 255, 255, 0.68);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-overflow: ellipsis;
  text-transform: uppercase;
  white-space: nowrap;
}

.card-main {
  overflow: hidden;
  font-size: 18px;
  font-weight: 650;
  letter-spacing: -0.02em;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.card-subtitle {
  margin-top: 5px;
  overflow: hidden;
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.home-indicator {
  position: absolute;
  bottom: 9px;
  left: 50%;
  z-index: 100;
  width: 132px;
  height: 5px;
  border-radius: 99px;
  background: rgba(255, 255, 255, 0.78);
  transform: translateX(-50%);
}

.animation-float {
  animation: float 5s ease-in-out infinite;
}

.animation-pulse {
  animation: pulse 3.2s ease-in-out infinite;
}

.animation-rotate {
  animation: rotate 14s linear infinite;
}

@keyframes float {
  0%,
  100% {
    translate: 0 0;
  }
  50% {
    translate: 0 -9px;
  }
}

@keyframes pulse {
  0%,
  100% {
    scale: 1;
  }
  50% {
    scale: 1.08;
  }
}

@keyframes rotate {
  to {
    rotate: 360deg;
  }
}
</style>
