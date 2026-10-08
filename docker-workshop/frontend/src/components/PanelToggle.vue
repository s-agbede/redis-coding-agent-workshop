<template>
  <button type="button" class="panel-toggle" :aria-label="`${expanded ? 'Restore' : 'Expand'} ${label}`"
    :aria-pressed="expanded" :title="expanded ? 'Restore split view' : `Expand ${label}`" @click="$emit('toggle')">
    <svg viewBox="0 0 20 20" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.5" aria-hidden="true">
      <path v-if="expanded" d="M2 7h5V2m6 0v5h5M2 13h5v5m6 0v-5h5" />
      <path v-else d="M7 2H2v5m11-5h5v5M2 13v5h5m6 0h5v-5" />
    </svg>
    {{ expanded ? 'Restore' : 'Expand' }}
  </button>
</template>

<script setup lang="ts">
defineProps<{ label: string; expanded: boolean }>()
defineEmits<{ (event: 'toggle'): void }>()
</script>

<style scoped>
.panel-toggle { display: inline-flex; align-items: center; justify-content: center; gap: .4rem; flex-shrink: 0; padding: .35rem .6rem; border: 1px solid #718096; border-radius: 4px; background: #2d3748; color: #e2e8f0; font: inherit; font-size: .75rem; cursor: pointer; }
.panel-toggle:hover { background: #3d4758; border-color: #7aa2f7; }
.panel-toggle:focus-visible { outline: 2px solid #7aa2f7; outline-offset: 2px; }
</style>
