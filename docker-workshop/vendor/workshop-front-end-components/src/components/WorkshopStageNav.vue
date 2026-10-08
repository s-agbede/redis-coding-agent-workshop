<template>
  <div class="stage-nav" :class="[alignmentClass]">
    <button 
      v-if="showPrev" 
      @click="$emit('prev')" 
      class="btn btn-secondary"
      :disabled="disablePrev"
    >
      <span class="nav-icon">←</span>
      <span class="nav-text">{{ prevText }}</span>
    </button>
    
    <slot></slot>
    
    <button 
      v-if="showNext" 
      @click="$emit('next')" 
      class="btn btn-primary"
      :disabled="disableNext"
    >
      <span class="nav-text">{{ nextText }}</span>
      <span class="nav-icon">→</span>
    </button>
  </div>
</template>

<script>
/**
 * WorkshopStageNav - Stage navigation component for workshops
 * 
 * Usage:
 *   <WorkshopStageNav
 *     :show-prev="currentStage > 1"
 *     :show-next="currentStage < totalStages"
 *     prev-text="Back"
 *     next-text="Continue"
 *     @prev="currentStage--"
 *     @next="currentStage++"
 *   />
 * 
 * With router-link for next:
 *   <WorkshopStageNav :show-next="false" @prev="prevStage">
 *     <router-link to="/editor" class="btn btn-primary">Open Editor →</router-link>
 *   </WorkshopStageNav>
 * 
 * Props:
 *   - showPrev (Boolean): Show previous button (default: true)
 *   - showNext (Boolean): Show next button (default: true)
 *   - prevText (String): Text for prev button (default: 'Back')
 *   - nextText (String): Text for next button (default: 'Continue')
 *   - disablePrev (Boolean): Disable prev button
 *   - disableNext (Boolean): Disable next button
 *   - align (String): 'left', 'center', 'right', 'space-between' (default: 'space-between')
 * 
 * Events:
 *   - prev: Emitted when prev button clicked
 *   - next: Emitted when next button clicked
 * 
 * Slots:
 *   - default: Additional buttons/links between prev and next
 */
export default {
  name: 'WorkshopStageNav',
  props: {
    showPrev: { type: Boolean, default: true },
    showNext: { type: Boolean, default: true },
    prevText: { type: String, default: 'Back' },
    nextText: { type: String, default: 'Continue' },
    disablePrev: { type: Boolean, default: false },
    disableNext: { type: Boolean, default: false },
    align: { 
      type: String, 
      default: 'space-between',
      validator: v => ['left', 'center', 'right', 'space-between'].includes(v)
    }
  },
  emits: ['prev', 'next'],
  computed: {
    alignmentClass() {
      return `align-${this.align}`;
    }
  }
};
</script>

<style scoped>
.stage-nav {
  display: flex;
  gap: var(--spacing-3, 0.75rem);
  margin-top: var(--spacing-6, 1.5rem);
  flex-wrap: wrap;
}

.align-left { justify-content: flex-start; }
.align-center { justify-content: center; }
.align-right { justify-content: flex-end; }
.align-space-between { justify-content: space-between; }

.btn {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2, 0.5rem);
  padding: var(--spacing-3, 0.75rem) var(--spacing-5, 1.25rem);
  border: none;
  border-radius: var(--radius-md, 6px);
  font-size: var(--font-size-sm, 0.875rem);
  font-weight: var(--font-weight-semibold, 600);
  cursor: pointer;
  transition: all var(--transition-base, 200ms);
  text-decoration: none;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: #DC382C;
  color: white;
}
.btn-primary:hover:not(:disabled) { background: #c42f24; }

.btn-secondary {
  background: var(--color-dark-800, #0D1A22);
  color: var(--color-text, #e2e8f0);
  border: 1px solid var(--color-border, rgba(71, 85, 105, 0.5));
}
.btn-secondary:hover:not(:disabled) { background: var(--color-border, rgba(71, 85, 105, 0.5)); }

.nav-icon {
  font-size: 1em;
}

/* Deep style for slotted router-links */
:deep(.btn) {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2, 0.5rem);
  padding: var(--spacing-3, 0.75rem) var(--spacing-5, 1.25rem);
  border: none;
  border-radius: var(--radius-md, 6px);
  font-size: var(--font-size-sm, 0.875rem);
  font-weight: var(--font-weight-semibold, 600);
  cursor: pointer;
  transition: all var(--transition-base, 200ms);
  text-decoration: none;
}

:deep(.btn-primary) {
  background: #DC382C;
  color: white;
}
:deep(.btn-primary:hover) { background: #c42f24; }
</style>

