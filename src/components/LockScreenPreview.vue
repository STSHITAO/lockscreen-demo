<script setup>
import { computed, onBeforeUnmount, ref, watch } from 'vue'

import CardGroup from './CardGroup.vue'
import InteractionParticle from './InteractionParticle.vue'
import { animationClassName } from '../core/animationPresets.js'
import { frameIndexAtElapsed } from '../core/frameSequence.js'
import { createGestureRecognizer } from '../core/gestureRecognizer.js'
import { createInteractionRuntime } from '../core/interactionRuntime.js'

const props = defineProps({
  dsl: {
    type: Object,
    required: true,
  },
})

const screenElement = ref(null)
const frameIndexes = ref({})
const frameTimers = new Map()
const interactionState = ref({
  effects: {},
  hiddenLayerIds: [],
  activeCards: {},
  transitioningGroups: [],
  particles: [],
})
let interactionRuntime = null
let unsubscribeRuntime = null

const gestureRecognizer = createGestureRecognizer({
  emit: (event) => interactionRuntime?.trigger(event),
})

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
  const override = interactionState.value.effects[layer.id]
  return animationClassName(override?.animation || layer.animation)
}

function runtimeStyle(layer) {
  const effect = interactionState.value.effects[layer.id]
  if (!effect) return {}
  const durations = {
    float: 5000,
    pulse: 900,
    rotate: 2400,
    twinkle: 700,
    'drift-left': 2600,
    'drift-right': 2600,
    sway: 1800,
    bounce: 1200,
    fade: 1600,
    breathe: 1800,
  }
  return {
    animationDuration: `${(durations[effect.animation] || 1000) / (effect.speed || 1)}ms`,
    '--interaction-peak-scale': String(
      1 + 0.1 * (effect.intensity || 1),
    ),
  }
}

function withRuntimeStyle(style, layer) {
  return { ...style, ...runtimeStyle(layer) }
}

function isInteractiveTarget(targetId) {
  return (props.dsl?.interactions || []).some(
    (interaction) => interaction?.targetId === targetId,
  )
}

function layerRuntimeClass(layer) {
  return {
    'interactive-layer': isInteractiveTarget(layer.id),
    'card-transitioning': cardGroupForLayer(layer.id)?.id &&
      interactionState.value.transitioningGroups.includes(
        cardGroupForLayer(layer.id).id,
      ),
  }
}

function cardGroupForLayer(layerId) {
  return (props.dsl?.cardGroups || []).find((group) =>
    (group.cardIds || []).includes(layerId),
  )
}

function isLayerVisible(layerId) {
  if (interactionState.value.hiddenLayerIds.includes(layerId)) return false
  const group = cardGroupForLayer(layerId)
  if (!group) return true
  const activeIndex =
    interactionState.value.activeCards[group.id] ??
    Number(group.activeIndex) ??
    0
  return group.cardIds?.[activeIndex] === layerId
}

function handlePointerDown(event, targetId) {
  if (!isInteractiveTarget(targetId)) return
  event.currentTarget?.setPointerCapture?.(event.pointerId)
  gestureRecognizer.pointerDown(
    targetId,
    event.clientX,
    event.clientY,
    event.timeStamp,
  )
}

function handlePointerMove(event, targetId) {
  if (!isInteractiveTarget(targetId)) return
  gestureRecognizer.pointerMove(targetId, event.clientX, event.clientY)
}

function handlePointerUp(event, targetId) {
  if (!isInteractiveTarget(targetId)) return
  gestureRecognizer.pointerUp(
    targetId,
    event.clientX,
    event.clientY,
    event.timeStamp,
  )
}

function handleRuntimeTrigger(event) {
  interactionRuntime?.trigger(event)
}

function cardGroupStyle(group) {
  const firstLayer = (props.dsl?.layers || []).find(
    (layer) => layer.id === group.cardIds?.[0],
  )
  return {
    left: `${numeric(firstLayer?.x, 32)}px`,
    top: `${numeric(firstLayer?.y, 690)}px`,
    width: `${numeric(firstLayer?.width, 326)}px`,
    height: `${numeric(firstLayer?.height, 96)}px`,
  }
}

function setupInteractionRuntime() {
  unsubscribeRuntime?.()
  interactionRuntime?.destroy()
  interactionRuntime = createInteractionRuntime(props.dsl || {})
  unsubscribeRuntime = interactionRuntime.subscribe((state) => {
    interactionState.value = state
  })
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

function assetStyle(layer) {
  return {
    left: `${numeric(layer.x)}px`,
    top: `${numeric(layer.y)}px`,
    width: `${numeric(layer.width, 120)}px`,
    height: `${numeric(layer.height, layer.width || 120)}px`,
    opacity: numeric(layer.opacity, 1),
    transform: `rotate(${numeric(layer.rotation)}deg)`,
    zIndex: numeric(layer.zIndex, 8),
  }
}

function assetImageStyle(layer) {
  return {
    objectFit: ['cover', 'contain'].includes(layer.fit) ? layer.fit : 'contain',
  }
}

function assetEffectClass(layer) {
  const effects = layer.effects && typeof layer.effects === 'object' ? layer.effects : {}
  return {
    'effect-shadow': Boolean(effects.shadow),
    'effect-glow': Boolean(effects.glow),
  }
}

function compoundPart(part = {}) {
  const x = numeric(part.x) * 100
  const y = numeric(part.y) * 100
  const width = numeric(part.width) * 100
  const height = numeric(part.height) * 100
  return {
    x,
    y,
    width,
    height,
    cx: x + width / 2,
    cy: y + height / 2,
    rx: width / 2,
    ry: height / 2,
    r: Math.min(width, height) / 2,
    x2: x + width,
    y2: y + height,
    fill: part.fill || 'transparent',
    stroke: part.stroke || 'transparent',
    strokeWidth: Math.max(0, numeric(part.strokeWidth) * 100),
    opacity: numeric(part.opacity, 1),
    radius: numeric(part.radius, 0.12) * 100,
    transform: numeric(part.rotation)
      ? `rotate(${numeric(part.rotation)} ${x + width / 2} ${y + height / 2})`
      : undefined,
  }
}

function compoundPoints(part = {}) {
  return (part.points || [])
    .map((point) => `${numeric(point?.[0]) * 100},${numeric(point?.[1]) * 100}`)
    .join(' ')
}

function clearFrameTimers() {
  for (const timer of frameTimers.values()) {
    window.clearInterval(timer)
  }
  frameTimers.clear()
}

function setupFrameAnimations() {
  clearFrameTimers()
  frameIndexes.value = {}

  for (const layer of props.dsl?.layers || []) {
    if (
      layer?.type !== 'frameAnimation' ||
      !Array.isArray(layer.frames) ||
      !layer.frames.length
    ) {
      continue
    }

    const startedAt = Date.now()
    const updateFrame = () => {
      const speed =
        interactionState.value.effects[layer.id]?.speed || 1
      frameIndexes.value[layer.id] = frameIndexAtElapsed(
        (Date.now() - startedAt) * speed,
        layer.frames.length,
        layer.fps,
        layer.loop !== false,
      )
    }
    updateFrame()
    const fps = Math.min(24, Math.max(1, numeric(layer.fps, 6)))
    frameTimers.set(
      layer.id,
      window.setInterval(updateFrame, Math.max(32, 1000 / fps)),
    )
  }
}

function currentFrame(layer) {
  if (!Array.isArray(layer.frames) || !layer.frames.length) {
    return layer.poster || ''
  }
  const index = frameIndexes.value[layer.id] || 0
  return layer.frames[index] || layer.poster || layer.frames[0]
}

watch(() => props.dsl?.layers, setupFrameAnimations, {
  deep: true,
  immediate: true,
})
watch(() => props.dsl, setupInteractionRuntime, {
  deep: true,
  immediate: true,
})
onBeforeUnmount(() => {
  clearFrameTimers()
  gestureRecognizer.destroy()
  unsubscribeRuntime?.()
  interactionRuntime?.destroy()
})

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
          v-show="isLayerVisible(layer.id)"
          class="layer text-layer"
          :class="[animationClass(layer), `role-${layer.role || 'text'}`, layerRuntimeClass(layer)]"
          :style="withRuntimeStyle(textStyle(layer), layer)"
          :data-interactive-id="isInteractiveTarget(layer.id) ? layer.id : undefined"
          @pointerdown="handlePointerDown($event, layer.id)"
          @pointermove="handlePointerMove($event, layer.id)"
          @pointerup="handlePointerUp($event, layer.id)"
          @pointercancel="gestureRecognizer.cancel"
        >
          {{ layer.content }}
        </div>

        <div
          v-else-if="layer.type === 'shape' && layer.shape === 'line'"
          v-show="isLayerVisible(layer.id)"
          class="layer shape-line"
          :class="[animationClass(layer), layerRuntimeClass(layer)]"
          :style="withRuntimeStyle(lineStyle(layer), layer)"
          :data-interactive-id="isInteractiveTarget(layer.id) ? layer.id : undefined"
          @pointerdown="handlePointerDown($event, layer.id)"
          @pointermove="handlePointerMove($event, layer.id)"
          @pointerup="handlePointerUp($event, layer.id)"
          @pointercancel="gestureRecognizer.cancel"
        ></div>

        <div
          v-else-if="layer.type === 'shape'"
          v-show="isLayerVisible(layer.id)"
          class="layer shape-layer"
          :class="[`shape-${layer.shape || 'roundedRect'}`, animationClass(layer), layerRuntimeClass(layer)]"
          :style="withRuntimeStyle(boxStyle(layer), layer)"
          :data-interactive-id="isInteractiveTarget(layer.id) ? layer.id : undefined"
          @pointerdown="handlePointerDown($event, layer.id)"
          @pointermove="handlePointerMove($event, layer.id)"
          @pointerup="handlePointerUp($event, layer.id)"
          @pointercancel="gestureRecognizer.cancel"
        ></div>

        <svg
          v-else-if="layer.type === 'compoundShape'"
          v-show="isLayerVisible(layer.id)"
          class="layer compound-shape-svg"
          :class="[animationClass(layer), layerRuntimeClass(layer)]"
          :style="withRuntimeStyle(assetStyle(layer), layer)"
          viewBox="0 0 100 100"
          preserveAspectRatio="xMidYMid meet"
          :data-compound-target="layer.target"
          :data-interactive-id="isInteractiveTarget(layer.id) ? layer.id : undefined"
          @pointerdown="handlePointerDown($event, layer.id)"
          @pointermove="handlePointerMove($event, layer.id)"
          @pointerup="handlePointerUp($event, layer.id)"
          @pointercancel="gestureRecognizer.cancel"
        >
          <template
            v-for="(part, partIndex) in layer.parts || []"
            :key="`${layer.id}-part-${partIndex}`"
          >
            <circle
              v-if="part.shape === 'circle'"
              v-bind="compoundPart(part)"
            />
            <ellipse
              v-else-if="part.shape === 'ellipse'"
              v-bind="compoundPart(part)"
            />
            <rect
              v-else-if="part.shape === 'rect' || part.shape === 'roundedRect'"
              v-bind="compoundPart(part)"
              :rx="part.shape === 'roundedRect' ? compoundPart(part).radius : 0"
              :ry="part.shape === 'roundedRect' ? compoundPart(part).radius : 0"
            />
            <polygon
              v-else-if="part.shape === 'triangle' || part.shape === 'polygon'"
              :points="compoundPoints(part)"
              :fill="part.fill || 'transparent'"
              :stroke="part.stroke || 'transparent'"
              :stroke-width="numeric(part.strokeWidth) * 100"
              :opacity="numeric(part.opacity, 1)"
            />
            <line
              v-else-if="part.shape === 'line'"
              :x1="compoundPart(part).x"
              :y1="compoundPart(part).y"
              :x2="compoundPart(part).x2"
              :y2="compoundPart(part).y2"
              :stroke="part.stroke || part.fill || '#ffffff'"
              :stroke-width="Math.max(0.5, numeric(part.strokeWidth, 0.01) * 100)"
              :opacity="numeric(part.opacity, 1)"
              stroke-linecap="round"
            />
          </template>
        </svg>

        <div
          v-else-if="layer.type === 'frameAnimation' && currentFrame(layer)"
          v-show="isLayerVisible(layer.id)"
          class="layer asset-layer frame-animation-layer"
          :class="[animationClass(layer), layerRuntimeClass(layer)]"
          :style="withRuntimeStyle(assetStyle(layer), layer)"
          :data-asset-id="layer.assetId"
          :data-interactive-id="isInteractiveTarget(layer.id) ? layer.id : undefined"
          @pointerdown="handlePointerDown($event, layer.id)"
          @pointermove="handlePointerMove($event, layer.id)"
          @pointerup="handlePointerUp($event, layer.id)"
          @pointercancel="gestureRecognizer.cancel"
        >
          <img
            class="asset-image frame-animation-image"
            :src="currentFrame(layer)"
            :alt="layer.alt || layer.assetId || 'animated lockscreen material'"
            :style="assetImageStyle(layer)"
            crossorigin="anonymous"
            draggable="false"
          />
        </div>

        <div
          v-else-if="layer.type === 'asset' && layer.src"
          v-show="isLayerVisible(layer.id)"
          class="layer asset-layer"
          :class="layerRuntimeClass(layer)"
          :style="withRuntimeStyle(assetStyle(layer), layer)"
          :data-asset-id="layer.assetId"
          :data-interactive-id="isInteractiveTarget(layer.id) ? layer.id : undefined"
          @pointerdown="handlePointerDown($event, layer.id)"
          @pointermove="handlePointerMove($event, layer.id)"
          @pointerup="handlePointerUp($event, layer.id)"
          @pointercancel="gestureRecognizer.cancel"
        >
          <img
            class="asset-image"
            :class="[animationClass(layer), assetEffectClass(layer)]"
            :src="layer.src"
            :alt="layer.alt || layer.assetId || 'lockscreen material'"
            :style="assetImageStyle(layer)"
            crossorigin="anonymous"
            draggable="false"
          />
        </div>

        <div
          v-else-if="layer.type === 'widget' || layer.type === 'glassCard'"
          v-show="isLayerVisible(layer.id)"
          class="layer glass-card"
          :class="[
            animationClass(layer),
            layerRuntimeClass(layer),
            layer.type === 'widget' ? `widget-${layer.role || 'generic'}` : 'dsl-glass-card',
          ]"
          :style="withRuntimeStyle(boxStyle(layer), layer)"
          :data-interactive-id="isInteractiveTarget(layer.id) ? layer.id : undefined"
          @pointerdown="handlePointerDown($event, layer.id)"
          @pointermove="handlePointerMove($event, layer.id)"
          @pointerup="handlePointerUp($event, layer.id)"
          @pointercancel="gestureRecognizer.cancel"
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

      <InteractionParticle
        v-for="particle in interactionState.particles"
        :key="particle.id"
        :particle="particle"
      />

      <CardGroup
        v-for="group in dsl.cardGroups || []"
        :key="group.id"
        :group="group"
        :active-index="interactionState.activeCards[group.id] ?? group.activeIndex ?? 0"
        :overlay-style="cardGroupStyle(group)"
        @trigger="handleRuntimeTrigger"
      />

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
  z-index: 20;
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
  z-index: 4;
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

.shape-crescent {
  border-radius: 50%;
  background: currentColor !important;
  filter: drop-shadow(0 0 18px color-mix(in srgb, currentColor 55%, transparent));
  -webkit-mask: radial-gradient(circle at 68% 36%, transparent 0 41%, #000 43%);
  mask: radial-gradient(circle at 68% 36%, transparent 0 41%, #000 43%);
}

.shape-heart {
  background: currentColor !important;
  clip-path: polygon(
    50% 100%,
    10% 61%,
    0 36%,
    4% 17%,
    18% 4%,
    35% 3%,
    50% 20%,
    65% 3%,
    82% 4%,
    96% 17%,
    100% 36%,
    90% 61%
  );
  filter: drop-shadow(0 0 10px color-mix(in srgb, currentColor 45%, transparent));
}

.shape-cloud {
  border-radius: 999px;
  background: currentColor !important;
  transform-origin: center;
}

.shape-cloud::before,
.shape-cloud::after {
  position: absolute;
  content: "";
  border-radius: 50%;
  background: currentColor;
}

.shape-cloud::before {
  left: 16%;
  bottom: 28%;
  width: 42%;
  height: 72%;
}

.shape-cloud::after {
  right: 15%;
  bottom: 25%;
  width: 48%;
  height: 82%;
}

.shape-sparkle {
  background: currentColor !important;
  clip-path: polygon(
    50% 0,
    59% 39%,
    100% 50%,
    59% 61%,
    50% 100%,
    41% 61%,
    0 50%,
    41% 39%
  );
  filter: drop-shadow(0 0 8px currentColor);
}

.shape-planet {
  overflow: visible;
  border-radius: 50%;
  background: currentColor !important;
  transform-origin: center;
  box-shadow: inset -10px -8px 18px rgba(15, 23, 42, 0.26);
}

.shape-planet::after {
  position: absolute;
  top: 39%;
  left: -12%;
  width: 124%;
  height: 22%;
  content: "";
  border: max(2px, 0.06em) solid currentColor;
  border-radius: 50%;
  transform: rotate(-18deg);
  box-shadow: 0 0 8px color-mix(in srgb, currentColor 42%, transparent);
}

.shape-line {
  border-radius: 999px;
  transform-origin: left center;
}

.compound-shape-svg {
  z-index: 8;
  overflow: visible;
  transform-origin: center;
}

.asset-layer {
  display: grid;
  place-items: center;
  transform-origin: center;
  pointer-events: none;
}

.interactive-layer {
  pointer-events: auto;
  cursor: pointer;
  touch-action: none;
  user-select: none;
}

.card-transitioning {
  transition: opacity 180ms ease, translate 180ms ease;
}

.asset-image {
  display: block;
  width: 100%;
  height: 100%;
  user-select: none;
}

.frame-animation-image {
  will-change: contents;
}

.asset-image.effect-shadow {
  filter: drop-shadow(0 16px 22px rgba(0, 0, 0, 0.3));
}

.asset-image.effect-glow {
  filter: drop-shadow(0 0 18px rgba(125, 211, 252, 0.48));
}

.asset-image.effect-shadow.effect-glow {
  filter:
    drop-shadow(0 16px 22px rgba(0, 0, 0, 0.28))
    drop-shadow(0 0 18px rgba(125, 211, 252, 0.45));
}

.glass-card {
  z-index: 24;
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

.animation-twinkle {
  animation: twinkle 1.6s ease-in-out infinite;
}

.animation-drift-left {
  animation: driftLeft 5.5s ease-in-out infinite;
}

.animation-drift-right {
  animation: driftRight 5.5s ease-in-out infinite;
}

.animation-sway {
  animation: sway 3.8s ease-in-out infinite;
}

.animation-bounce {
  animation: bounce 2.4s ease-in-out infinite;
}

.animation-fade {
  animation: fade 3.6s ease-in-out infinite;
}

.animation-breathe {
  animation: breathe 4.2s ease-in-out infinite;
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
    scale: var(--interaction-peak-scale, 1.08);
  }
}

@keyframes rotate {
  to {
    rotate: 360deg;
  }
}

@keyframes twinkle {
  0%,
  100% {
    opacity: 0.42;
    scale: 0.82;
  }
  50% {
    opacity: 1;
    scale: var(--interaction-peak-scale, 1.16);
  }
}

@keyframes driftLeft {
  0%,
  100% {
    translate: 12px 0;
  }
  50% {
    translate: -18px -4px;
  }
}

@keyframes driftRight {
  0%,
  100% {
    translate: -12px 0;
  }
  50% {
    translate: 18px -4px;
  }
}

@keyframes sway {
  0%,
  100% {
    rotate: -5deg;
  }
  50% {
    rotate: 5deg;
  }
}

@keyframes bounce {
  0%,
  100% {
    translate: 0 0;
  }
  45% {
    translate: 0 -14px;
  }
  65% {
    translate: 0 -5px;
  }
}

@keyframes fade {
  0%,
  100% {
    opacity: 0.3;
  }
  50% {
    opacity: 1;
  }
}

@keyframes breathe {
  0%,
  100% {
    scale: 0.94;
    filter: brightness(0.9);
  }
  50% {
    scale: 1.06;
    filter: brightness(1.16);
  }
}
</style>
