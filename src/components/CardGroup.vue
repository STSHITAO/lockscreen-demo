<script setup>
import { onBeforeUnmount } from 'vue'

import { createGestureRecognizer } from '../core/gestureRecognizer.js'

const props = defineProps({
  group: {
    type: Object,
    required: true,
  },
  activeIndex: {
    type: Number,
    default: 0,
  },
  overlayStyle: {
    type: Object,
    default: () => ({}),
  },
})
const emit = defineEmits(['trigger'])

const recognizer = createGestureRecognizer({
  emit: (event) => {
    if (event.type === 'swipeLeft' || event.type === 'swipeRight') {
      emit('trigger', event)
    }
  },
})

function pointerdown(event) {
  event.currentTarget?.setPointerCapture?.(event.pointerId)
  recognizer.pointerDown(
    props.group.id,
    event.clientX,
    event.clientY,
    event.timeStamp,
  )
}

function pointermove(event) {
  recognizer.pointerMove(
    props.group.id,
    event.clientX,
    event.clientY,
  )
}

function pointerup(event) {
  recognizer.pointerUp(
    props.group.id,
    event.clientX,
    event.clientY,
    event.timeStamp,
  )
}

onBeforeUnmount(recognizer.destroy)
</script>

<template>
  <div
    class="card-group-gesture"
    :style="overlayStyle"
    :data-card-group="group.id"
    @pointerdown="pointerdown"
    @pointermove="pointermove"
    @pointerup="pointerup"
    @pointercancel="recognizer.cancel"
  >
    <div class="card-group-dots" aria-hidden="true">
      <span
        v-for="(_, index) in group.cardIds || []"
        :key="index"
        :class="{ active: index === activeIndex }"
      ></span>
    </div>
  </div>
</template>

<style scoped>
.card-group-gesture {
  position: absolute;
  z-index: 55;
  cursor: grab;
  touch-action: pan-y;
}

.card-group-gesture:active {
  cursor: grabbing;
}

.card-group-dots {
  position: absolute;
  bottom: -16px;
  left: 50%;
  display: flex;
  gap: 5px;
  transform: translateX(-50%);
}

.card-group-dots span {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.38);
  transition: width 180ms ease, background 180ms ease;
}

.card-group-dots span.active {
  width: 12px;
  border-radius: 99px;
  background: rgba(255, 255, 255, 0.9);
}
</style>
