import { createBurstParticles } from './particleEngine.js'


function cloneState(state) {
  return {
    effects: structuredClone(state.effects),
    hiddenLayerIds: [...state.hiddenLayerIds],
    activeCards: { ...state.activeCards },
    transitioningGroups: [...state.transitioningGroups],
    particles: state.particles.map((particle) => ({ ...particle })),
  }
}

export function createInteractionRuntime(
  dsl,
  {
    schedule = (callback, delay) => window.setTimeout(callback, delay),
    cancel = (timer) => window.clearTimeout(timer),
  } = {},
) {
  const layers = new Map(
    (dsl?.layers || []).map((layer) => [String(layer.id), layer]),
  )
  const groups = new Map(
    (dsl?.cardGroups || []).map((group) => [String(group.id), group]),
  )
  const interactions = Array.isArray(dsl?.interactions)
    ? dsl.interactions
    : []
  const state = {
    effects: {},
    hiddenLayerIds: new Set(),
    activeCards: Object.fromEntries(
      [...groups.values()].map((group) => [
        String(group.id),
        Number(group.activeIndex) || 0,
      ]),
    ),
    transitioningGroups: new Set(),
    particles: [],
  }
  const listeners = new Set()
  const targetTimers = new Map()
  const tapHistory = new Map()

  function notify() {
    const current = cloneState(state)
    for (const listener of listeners) listener(current)
  }

  function clearTargetTimers(targetId) {
    for (const timer of targetTimers.get(targetId) || []) cancel(timer)
    targetTimers.delete(targetId)
  }

  function addTimer(targetId, callback, delay) {
    const timer = schedule(callback, delay)
    const timers = targetTimers.get(targetId) || []
    timers.push(timer)
    targetTimers.set(targetId, timers)
    return timer
  }

  function runActions(targetId, actions, index = 0) {
    if (index >= actions.length) return
    const action = actions[index]
    const next = () => runActions(targetId, actions, index + 1)

    if (action.type === 'animate') {
      state.effects[targetId] = {
        animation: action.animation,
        speed: Number(action.speed) || 1,
        intensity: Number(action.intensity) || 1,
      }
      notify()
      if (action.until === 'release') return
      addTimer(targetId, () => {
        delete state.effects[targetId]
        notify()
        next()
      }, Number(action.duration) || 600)
      return
    }
    if (action.type === 'stopAnimation') {
      delete state.effects[targetId]
      notify()
      next()
      return
    }
    if (action.type === 'setAnimationSpeed') {
      const layer = layers.get(targetId)
      const baseAnimation =
        layer?.animation ||
        (layer?.type === 'frameAnimation' ? 'frame-sequence' : '')
      if (state.effects[targetId] || baseAnimation) {
        state.effects[targetId] = {
          animation:
            state.effects[targetId]?.animation || baseAnimation,
          speed: Number(action.speed) || 1,
          intensity: state.effects[targetId]?.intensity || 1,
        }
        notify()
      }
      next()
      return
    }
    if (action.type === 'burst') {
      const layer = layers.get(targetId) || { id: targetId }
      const particles = createBurstParticles(action, layer)
      state.particles.push(...particles)
      notify()
      addTimer(targetId, () => {
        const particleIds = new Set(particles.map((particle) => particle.id))
        state.particles = state.particles.filter(
          (particle) => !particleIds.has(particle.id),
        )
        if (action.afterEffect === 'hide') {
          state.hiddenLayerIds.add(targetId)
        } else {
          state.hiddenLayerIds.delete(targetId)
        }
        notify()
        if (
          action.afterEffect === 'restore' &&
          Number(action.restoreDelay) > 0
        ) {
          addTimer(targetId, () => {
            state.hiddenLayerIds.delete(targetId)
            notify()
            next()
          }, Number(action.restoreDelay))
        } else {
          next()
        }
      }, Number(action.duration) || 800)
      return
    }
    if (action.type === 'switchCard') {
      const group = groups.get(targetId)
      if (!group || state.transitioningGroups.has(targetId)) return
      const cardCount = group.cardIds?.length || 0
      if (!cardCount) return
      const current = state.activeCards[targetId] || 0
      const offset = action.direction === 'previous' ? -1 : 1
      let nextIndex = current + offset
      if (group.loop !== false) {
        nextIndex = (nextIndex + cardCount) % cardCount
      } else {
        nextIndex = Math.max(0, Math.min(nextIndex, cardCount - 1))
      }
      state.activeCards[targetId] = nextIndex
      state.transitioningGroups.add(targetId)
      notify()
      addTimer(targetId, () => {
        state.transitioningGroups.delete(targetId)
        notify()
        next()
      }, 360)
      return
    }
    if (action.type === 'setVisibility') {
      if (action.visible === false) state.hiddenLayerIds.add(targetId)
      else state.hiddenLayerIds.delete(targetId)
      notify()
      next()
      return
    }
    if (action.type === 'reset') {
      delete state.effects[targetId]
      state.hiddenLayerIds.delete(targetId)
      notify()
      next()
      return
    }
    next()
  }

  function execute(interaction) {
    const targetId = String(interaction.targetId)
    if (interaction.restart !== 'ignore') clearTargetTimers(targetId)
    runActions(targetId, interaction.actions || [])
  }

  function trigger(event) {
    const targetId = String(event?.targetId || '')
    const type = String(event?.type || '')
    if (!targetId || !type) return false
    let handled = false

    if (type === 'tap') {
      const timestamp = Number(event.timestamp) || 0
      const history = tapHistory.get(targetId) || []
      history.push(timestamp)
      tapHistory.set(targetId, history.slice(-10))
    }

    for (const interaction of interactions) {
      if (String(interaction.targetId) !== targetId) continue
      const triggerSpec = interaction.trigger || {}
      if (triggerSpec.type === type) {
        execute(interaction)
        handled = true
        continue
      }
      if (type === 'tap' && triggerSpec.type === 'multiTap') {
        const count = Number(triggerSpec.count) || 3
        const withinMs = Number(triggerSpec.withinMs) || 1200
        const history = tapHistory.get(targetId) || []
        const recent = history.slice(-count)
        if (
          recent.length === count &&
          recent[recent.length - 1] - recent[0] <= withinMs
        ) {
          tapHistory.set(targetId, [])
          execute(interaction)
          handled = true
        }
      }
    }
    return handled
  }

  function subscribe(listener) {
    listeners.add(listener)
    listener(cloneState(state))
    return () => listeners.delete(listener)
  }

  function destroy() {
    for (const targetId of targetTimers.keys()) clearTargetTimers(targetId)
    listeners.clear()
  }

  return {
    trigger,
    subscribe,
    snapshot: () => cloneState(state),
    destroy,
  }
}
