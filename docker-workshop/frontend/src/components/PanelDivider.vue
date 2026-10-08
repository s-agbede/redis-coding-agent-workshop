<template>
  <div class="panel-divider" :class="`panel-divider--${orientation}`" role="separator" :tabindex="0"
    :aria-label="label" :aria-orientation="orientation" :aria-valuemin="20" :aria-valuemax="80"
    :aria-valuenow="Math.round(value)" :aria-valuetext="`${Math.round(value)} percent`"
    :title="`${label}: drag or use arrow keys`" @keydown="resizeWithKeyboard"
    @pointerdown="startResize" @pointermove="resize" @pointerup="stopResize"
    @pointercancel="stopResize" @lostpointercapture="stopResize">
    <div v-if="dragging" class="resize-shield" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'

const props = defineProps<{ orientation: 'horizontal' | 'vertical'; label: string; value: number }>()
const emit = defineEmits<{ (event: 'update:value', value: number): void }>()
const dragging = ref(false)
let bounds: DOMRect | undefined
let pointerId: number | undefined

function update(value: number): void {
  emit('update:value', Math.max(20, Math.min(80, value)))
}
function startResize(event: PointerEvent): void {
  if (event.button !== 0 || dragging.value) return
  const handle = event.currentTarget as HTMLElement
  bounds = handle.parentElement?.getBoundingClientRect()
  if (!bounds) return
  event.preventDefault()
  handle.setPointerCapture(event.pointerId)
  pointerId = event.pointerId
  dragging.value = true
}
function resize(event: PointerEvent): void {
  if (!dragging.value || !bounds || event.pointerId !== pointerId) return
  const horizontal = props.orientation === 'horizontal'
  const size = horizontal ? bounds.height : bounds.width
  if (size > 0) update(100 * ((horizontal ? event.clientY - bounds.top : event.clientX - bounds.left) / size))
}
function stopResize(event: PointerEvent): void {
  if (event.pointerId !== pointerId) return
  dragging.value = false
  pointerId = undefined
  const handle = event.currentTarget as HTMLElement
  if (handle.hasPointerCapture(event.pointerId)) handle.releasePointerCapture(event.pointerId)
}
function resizeWithKeyboard(event: KeyboardEvent): void {
  const decrease = props.orientation === 'horizontal' ? 'ArrowUp' : 'ArrowLeft'
  const increase = props.orientation === 'horizontal' ? 'ArrowDown' : 'ArrowRight'
  if (![decrease, increase, 'Home', 'End'].includes(event.key)) return
  event.preventDefault()
  update(event.key === 'Home' ? 20 : event.key === 'End' ? 80 : props.value + (event.key === decrease ? -5 : 5))
}
</script>

<style scoped>
.panel-divider { flex-shrink: 0; position: relative; background: #2d3748; touch-action: none; user-select: none; }
.panel-divider::after { content: ''; position: absolute; border-radius: 2px; background: #718096; }
.panel-divider--vertical { width: 10px; cursor: col-resize; }
.panel-divider--vertical::after { width: 2px; height: 36px; top: calc(50% - 18px); left: 4px; }
.panel-divider--horizontal { height: 10px; cursor: row-resize; }
.panel-divider--horizontal::after { height: 2px; width: 36px; left: calc(50% - 18px); top: 4px; }
.panel-divider:hover, .panel-divider:focus-visible { background: #4a5568; outline: 2px solid #7aa2f7; outline-offset: -2px; }
.resize-shield { position: fixed; inset: 0; z-index: 1000; cursor: inherit; }
</style>
