<script setup>
import { computed } from 'vue'

const props = defineProps({
  particle: {
    type: Object,
    required: true,
  },
})

const particleStyle = computed(() => ({
  left: `${props.particle.originX}px`,
  top: `${props.particle.originY}px`,
  width: `${props.particle.size}px`,
  height: `${props.particle.size}px`,
  '--particle-x': `${props.particle.dx}px`,
  '--particle-y': `${props.particle.dy}px`,
  '--particle-rotation': `${props.particle.rotation}deg`,
  animationDuration: `${props.particle.duration}ms`,
  animationDelay: `${props.particle.delay}ms`,
}))
</script>

<template>
  <div
    class="interaction-particle"
    :class="`particle-${particle.source?.shape || particle.source?.type || 'circle'}`"
    :style="particleStyle"
    aria-hidden="true"
  >
    <img
      v-if="particle.source?.type === 'asset' && particle.source?.src"
      :src="particle.source.src"
      alt=""
      draggable="false"
    />
  </div>
</template>

<style scoped>
.interaction-particle {
  position: absolute;
  z-index: 82;
  pointer-events: none;
  background: #fff;
  transform: translate(-50%, -50%);
  animation: particleBurst 800ms cubic-bezier(0.15, 0.7, 0.25, 1) forwards;
  filter: drop-shadow(0 0 6px currentColor);
}

.interaction-particle img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.particle-heart {
  color: #fb7185;
  background: currentColor;
  clip-path: polygon(50% 100%, 4% 42%, 7% 17%, 25% 3%, 50% 22%, 75% 3%, 93% 17%, 96% 42%);
}

.particle-star {
  color: #fef08a;
  background: currentColor;
  clip-path: polygon(50% 0, 61% 35%, 98% 35%, 68% 57%, 79% 94%, 50% 72%, 21% 94%, 32% 57%, 2% 35%, 39% 35%);
}

.particle-sparkle {
  color: #fff;
  background: currentColor;
  clip-path: polygon(50% 0, 60% 40%, 100% 50%, 60% 60%, 50% 100%, 40% 60%, 0 50%, 40% 40%);
}

.particle-circle {
  border-radius: 50%;
}

.particle-asset {
  background: transparent;
  filter: none;
}

@keyframes particleBurst {
  0% {
    opacity: 0;
    scale: 0.5;
  }
  18% {
    opacity: 1;
  }
  100% {
    opacity: 0;
    translate: var(--particle-x) var(--particle-y);
    rotate: var(--particle-rotation);
    scale: 1.15;
  }
}
</style>
