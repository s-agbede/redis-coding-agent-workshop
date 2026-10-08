<template>
  <div class="progress-indicator" :class="[variantClass]">
    <!-- Step-based progress -->
    <template v-if="variant === 'steps'">
      <div class="steps-container">
        <div 
          v-for="(step, index) in steps" 
          :key="index"
          class="step"
          :class="{
            'completed': index < currentStep,
            'active': index === currentStep,
            'clickable': clickable && index <= currentStep
          }"
          @click="handleStepClick(index)"
        >
          <div class="step-marker">
            <span v-if="index < currentStep" class="check">✓</span>
            <span v-else>{{ index + 1 }}</span>
          </div>
          <span v-if="showLabels" class="step-label">{{ step }}</span>
        </div>
        <div class="step-connector" :style="connectorStyle"></div>
      </div>
    </template>

    <!-- Counter-based progress -->
    <template v-else-if="variant === 'counter'">
      <div class="counter-container">
        <span class="counter-value">{{ current }}/{{ total }}</span>
        <span v-if="label" class="counter-label">{{ label }}</span>
      </div>
    </template>

    <!-- Bar-based progress -->
    <template v-else-if="variant === 'bar'">
      <div class="bar-container">
        <div class="bar-label" v-if="showPercentage || label">
          <span v-if="label">{{ label }}</span>
          <span v-if="showPercentage">{{ percentage }}%</span>
        </div>
        <div class="bar-track">
          <div class="bar-fill" :style="{ width: percentage + '%' }"></div>
        </div>
      </div>
    </template>
  </div>
</template>

<script>
/**
 * WorkshopProgressIndicator - Visual progress component for workshops
 * 
 * Three variants:
 * 
 * 1. Steps (default) - Shows numbered steps with optional labels
 *    <WorkshopProgressIndicator
 *      :steps="['Intro', 'Concept', 'Editor', 'Test']"
 *      :current-step="1"
 *      show-labels
 *    />
 * 
 * 2. Counter - Simple X/Y display
 *    <WorkshopProgressIndicator
 *      variant="counter"
 *      :current="3"
 *      :total="5"
 *      label="Completed"
 *    />
 * 
 * 3. Bar - Progress bar with percentage
 *    <WorkshopProgressIndicator
 *      variant="bar"
 *      :current="3"
 *      :total="5"
 *      show-percentage
 *    />
 */
export default {
  name: 'WorkshopProgressIndicator',
  props: {
    variant: {
      type: String,
      default: 'steps',
      validator: v => ['steps', 'counter', 'bar'].includes(v)
    },
    // For steps variant
    steps: { type: Array, default: () => [] },
    currentStep: { type: Number, default: 0 },
    showLabels: { type: Boolean, default: false },
    clickable: { type: Boolean, default: false },
    // For counter/bar variants
    current: { type: Number, default: 0 },
    total: { type: Number, default: 1 },
    label: { type: String, default: '' },
    showPercentage: { type: Boolean, default: false }
  },
  emits: ['step-click'],
  computed: {
    variantClass() {
      return `variant-${this.variant}`;
    },
    percentage() {
      if (this.total === 0) return 0;
      return Math.round((this.current / this.total) * 100);
    },
    connectorStyle() {
      const totalSteps = this.steps.length;
      if (totalSteps <= 1) return { width: '0%' };
      const progress = (this.currentStep / (totalSteps - 1)) * 100;
      return { width: `${Math.min(progress, 100)}%` };
    }
  },
  methods: {
    handleStepClick(index) {
      if (this.clickable && index <= this.currentStep) {
        this.$emit('step-click', index);
      }
    }
  }
};
</script>

<style scoped>
.progress-indicator {
  width: 100%;
}

/* Steps Variant */
.steps-container {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  position: relative;
  padding: 0 var(--spacing-2, 0.5rem);
}

.step {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-2, 0.5rem);
  position: relative;
  z-index: 1;
}

.step.clickable { cursor: pointer; }

.step-marker {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-sm, 0.875rem);
  font-weight: var(--font-weight-semibold, 600);
  background: var(--color-dark-700, #101A21);
  border: 2px solid var(--color-border, rgba(71, 85, 105, 0.5));
  color: var(--color-text-secondary, #94a3b8);
  transition: all var(--transition-base, 200ms);
}

.step.completed .step-marker {
  background: #10b981;
  border-color: #10b981;
  color: white;
}

.step.active .step-marker {
  background: #DC382C;
  border-color: #DC382C;
  color: white;
}

.step-label {
  font-size: var(--font-size-xs, 0.75rem);
  color: var(--color-text-secondary, #94a3b8);
  text-align: center;
  max-width: 80px;
}

.step.active .step-label { color: var(--color-text, #e2e8f0); }
.step.completed .step-label { color: #10b981; }

.step-connector {
  position: absolute;
  top: 16px;
  left: calc(16px + var(--spacing-2, 0.5rem));
  right: calc(16px + var(--spacing-2, 0.5rem));
  height: 2px;
  background: linear-gradient(to right, #10b981 var(--progress, 0%), var(--color-border, rgba(71, 85, 105, 0.5)) var(--progress, 0%));
  z-index: 0;
}

/* Counter Variant */
.counter-container {
  text-align: right;
}

.counter-value {
  display: block;
  font-size: var(--font-size-2xl, 1.5rem);
  font-weight: var(--font-weight-bold, 700);
  color: #10b981;
}

.counter-label {
  font-size: var(--font-size-sm, 0.875rem);
  color: var(--color-text-secondary, #94a3b8);
}

/* Bar Variant */
.bar-container { width: 100%; }

.bar-label {
  display: flex;
  justify-content: space-between;
  margin-bottom: var(--spacing-2, 0.5rem);
  font-size: var(--font-size-sm, 0.875rem);
  color: var(--color-text-secondary, #94a3b8);
}

.bar-track {
  height: 8px;
  background: var(--color-dark-700, #101A21);
  border-radius: var(--radius-full, 50%);
  overflow: hidden;
}

.bar-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #34d399);
  border-radius: var(--radius-full, 50%);
  transition: width var(--transition-base, 200ms);
}
</style>

