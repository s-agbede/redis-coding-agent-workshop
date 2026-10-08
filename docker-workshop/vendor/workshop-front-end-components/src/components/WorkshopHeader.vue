<template>
  <header class="workshop-header">
    <a :href="hubUrl" class="back-link">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M19 12H5M12 19l-7-7 7-7"/>
      </svg>
      <span>Workshop Home</span>
    </a>

    <div v-if="steps && steps.length" class="progress-steps">
      <div 
        v-for="(step, index) in steps" 
        :key="index"
        class="step"
        :class="{ active: index === currentStep - 1, inactive: index !== currentStep - 1, clickable }"
        @click="clickable && $emit('step-click', index + 1)"
      >
        <div class="step-dot">
          {{ index + 1 }}
        </div>
        <span class="step-label">{{ step }}</span>
      </div>
    </div>

    <div v-if="$slots.right" class="header-right">
      <slot name="right"></slot>
    </div>
  </header>
</template>

<script>
export default {
  name: 'WorkshopHeader',
  props: {
    hubUrl: { type: String, default: '/' },
    steps: { type: Array, default: () => [] },
    currentStep: { type: Number, default: 1 },
    clickable: { type: Boolean, default: false }
  },
  emits: ['step-click']
};
</script>

<style scoped>
.workshop-header {
  display: flex;
  align-items: center;
  gap: var(--spacing-6, 1.5rem);
  padding: var(--spacing-3, 0.75rem) var(--spacing-4, 1rem);
  background: var(--color-dark-900, #0a1015);
  border-bottom: 1px solid var(--color-border, rgba(71, 85, 105, 0.3));
  margin-bottom: var(--spacing-4, 1rem);
}

.back-link {
  display: flex;
  align-items: center;
  gap: var(--spacing-2, 0.5rem);
  color: var(--color-text-secondary, #94a3b8);
  text-decoration: none;
  font-size: var(--font-size-sm, 0.875rem);
  font-weight: 500;
  white-space: nowrap;
  transition: color 0.2s;
}

.back-link:hover {
  color: var(--color-text, #e2e8f0);
}

.progress-steps {
  display: flex;
  align-items: center;
  gap: var(--spacing-1, 0.25rem);
  flex: 1;
  justify-content: center;
}

.step {
  display: flex;
  align-items: center;
  gap: var(--spacing-2, 0.5rem);
  padding: var(--spacing-1, 0.25rem) var(--spacing-2, 0.5rem);
  border-radius: var(--radius-full, 9999px);
  transition: all 0.2s;
}

.step.clickable { cursor: pointer; }
.step.clickable:hover { background: var(--color-dark-800, #0D1A22); }

.step-dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-dark-700, #101A21);
  border: 2px solid var(--color-border, rgba(71, 85, 105, 0.5));
  color: var(--color-text-muted, #64748b);
  font-size: 10px;
  font-weight: 600;
  transition: all 0.2s;
}

.step.inactive .step-dot {
  background: var(--color-dark-700, #101A21);
  border-color: rgba(71, 85, 105, 0.3);
  color: #475569;
}

.step.active .step-dot {
  background: var(--yellow, #DCFF1E);
  border-color: var(--yellow, #DCFF1E);
  color: var(--color-dark-900, #0a1015);
}

.step-label {
  font-size: var(--font-size-xs, 0.75rem);
  color: var(--color-text-muted, #64748b);
  font-weight: 500;
}

.step.active .step-label { color: var(--color-text, #e2e8f0); font-weight: 600; }
.step.inactive .step-label { color: #475569; }

.header-right {
  margin-left: auto;
}

/* Hide labels on small screens */
@media (max-width: 768px) {
  .step-label { display: none; }
  .progress-steps { gap: var(--spacing-2, 0.5rem); }
}
</style>
