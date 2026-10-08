<template>
  <div class="workshop-intro-page">
    <div class="intro-container">
      <div class="intro-header">
        <slot name="logo">
          <div class="intro-logo-placeholder"></div>
        </slot>
        <h1 class="intro-title">{{ title }}</h1>
        <p v-if="subtitle" class="intro-subtitle">{{ subtitle }}</p>
      </div>

      <div v-if="description" class="intro-description">
        <p>{{ description }}</p>
      </div>

      <div v-if="estimatedMinutes || difficulty" class="intro-meta">
        <div v-if="estimatedMinutes" class="meta-item">
          <span class="meta-label">Duration</span>
          <span class="meta-value">{{ estimatedMinutes }} minutes</span>
        </div>
        <div v-if="difficulty" class="meta-item">
          <span class="meta-label">Difficulty</span>
          <span class="meta-value">{{ difficulty }}</span>
        </div>
      </div>

      <div v-if="topics && topics.length" class="intro-topics">
        <span v-for="topic in topics" :key="topic" class="topic-tag">
          {{ topic }}
        </span>
      </div>

      <div class="intro-actions">
        <slot name="actions">
          <button class="btn-primary" @click="$emit('start')">
            {{ startLabel }}
          </button>
        </slot>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'WorkshopIntroPage',
  props: {
    title: {
      type: String,
      required: true
    },
    subtitle: {
      type: String,
      default: ''
    },
    description: {
      type: String,
      default: ''
    },
    estimatedMinutes: {
      type: Number,
      default: null
    },
    difficulty: {
      type: String,
      default: ''
    },
    topics: {
      type: Array,
      default: () => []
    },
    startLabel: {
      type: String,
      default: 'Start Workshop'
    }
  },
  emits: ['start']
}
</script>

<style scoped>
.workshop-intro-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  background: linear-gradient(135deg, var(--color-bg-primary) 0%, var(--color-bg-secondary) 100%);
}

.intro-container {
  max-width: 600px;
  text-align: center;
}

.intro-logo-placeholder {
  width: 80px;
  height: 80px;
  margin: 0 auto 1.5rem;
  background: var(--color-bg-tertiary);
  border-radius: 1rem;
}

.intro-title {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 0.5rem;
}

.intro-subtitle {
  font-size: 1.25rem;
  color: var(--color-primary);
  margin-bottom: 2rem;
}

.intro-description {
  font-size: 1.1rem;
  color: var(--color-text-secondary);
  line-height: 1.6;
  margin-bottom: 2rem;
}

.intro-meta {
  display: flex;
  justify-content: center;
  gap: 3rem;
  margin-bottom: 1.5rem;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.meta-label {
  font-size: 0.75rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-tertiary);
}

.meta-value {
  font-size: 1rem;
  font-weight: 600;
  color: var(--color-text-primary);
}

.intro-topics {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 0.5rem;
  margin-bottom: 2.5rem;
}

.topic-tag {
  padding: 0.25rem 0.75rem;
  background: var(--color-bg-tertiary);
  border-radius: 1rem;
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.intro-actions {
  margin-top: 2rem;
}

.btn-primary {
  padding: 1rem 2.5rem;
  font-size: 1.1rem;
  font-weight: 600;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-primary:hover {
  background: var(--color-primary-hover);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}
</style>
