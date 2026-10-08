<template>
  <div class="workshop-review">
    <WorkshopHeader
      :hub-url="workshopHomeUrl"
      :title="reviewTitle"
      :steps="phaseSteps"
      :current-step="currentPhaseIndex"
      :clickable="true"
      @step-click="navigateToPhase"
    />

    <main class="review-content">
      <!-- Markdown Content -->
      <div v-if="htmlContent" class="markdown-content" v-html="htmlContent"></div>

      <p v-else role="status">{{ loading ? 'Loading concepts…' : 'Unable to load the workshop concepts. Refresh to try again.' }}</p>

      <div class="navigation-buttons">
        <button class="nav-btn nav-btn--back" @click="goToPreviousPhase">
          Back to {{ previousPhase?.title || 'Welcome' }}
        </button>
        <button class="nav-btn nav-btn--continue" @click="goToNextPhase">
          Next: {{ nextPhase?.title || 'Try the app' }}
        </button>
      </div>
    </main>
  </div>
</template>

<script>
import WorkshopHeader from '@redis-workshop/components/components/WorkshopHeader.vue'
import { loadReviewContent } from '../utils/pageContent'
import { getBasePath } from '../utils/basePath'
import { loadWorkshopConfig, getPhaseStepTitles, getEnabledPhases, getNextPhase, getPreviousPhase } from '../utils/workshopConfig'

export default {
  name: 'WorkshopReview',
  components: {
    WorkshopHeader
  },
  data() {
    return {
      workshopHomeUrl: getBasePath() === '/guide' ? '/guide/' : '/',
      content: null,
      htmlContent: null,
      config: null,
      loading: true,
      error: null,
      phaseSteps: ['Welcome', 'How it works', 'Try the app', 'Build your agent'],
      enabledPhases: [],
      currentPhaseIndex: 2
    }
  },
  computed: {
    reviewTitle() {
      return this.content?.title || 'How it works'
    },
    previousPhase() {
      if (!this.config) return { route: '/', title: 'Welcome' }
      return getPreviousPhase(this.config, 'review')
    },
    nextPhase() {
      if (!this.config) return { route: '/demo', title: 'Try the app' }
      return getNextPhase(this.config, 'review')
    }
  },
  methods: {
    navigateToPhase(step) {
      const phase = this.enabledPhases[step - 1]
      if (phase) {
        this.$router.push(phase.route)
      }
    },
    goToPreviousPhase() {
      this.$router.push(this.previousPhase?.route || '/')
    },
    goToNextPhase() {
      this.$router.push(this.nextPhase?.route || '/demo')
    }
  },
  async mounted() {
    // Load workshop config
    try {
      this.config = await loadWorkshopConfig()
      this.phaseSteps = getPhaseStepTitles(this.config)
      this.enabledPhases = getEnabledPhases(this.config)
      this.currentPhaseIndex = this.enabledPhases.findIndex(p => p.id === 'review') + 1
    } catch (err) {
      console.warn('Failed to load workshop config:', err)
    }

    // Load review content from review.md
    try {
      this.content = await loadReviewContent()
      if (this.content) {
        this.htmlContent = this.content.htmlContent
      }
    } catch (err) {
      this.error = err.message
    } finally {
      this.loading = false
    }
  }
}
</script>

<style scoped>
.workshop-review {
  min-height: 100vh;
  background: #1a1a2e;
}

.review-content {
  max-width: 900px;
  margin: 0 auto;
  padding: 2rem;
}

.fallback-content h2 {
  color: #ffffff;
  font-size: 1.75rem;
  margin-bottom: 2rem;
}

.review-section {
  margin-bottom: 2.5rem;
}

.review-section h3 {
  color: #dc382c;
  font-size: 1.25rem;
  margin-bottom: 1rem;
}

.review-section p {
  color: #e2e8f0;
  line-height: 1.6;
  margin-bottom: 1rem;
}

.review-section ul {
  color: #e2e8f0;
  padding-left: 1.5rem;
}

.review-section li {
  margin-bottom: 0.5rem;
}

.concept-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.concept-card {
  background: #2d3748;
  border-radius: 8px;
  padding: 1.25rem;
  border: 1px solid #4a5568;
}

.concept-card h4 {
  color: #ffffff;
  font-size: 1rem;
  margin-bottom: 0.5rem;
}

.concept-card p {
  color: #a0aec0;
  font-size: 0.875rem;
  margin: 0;
}

.command-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.command-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: #2d3748;
  padding: 0.75rem 1rem;
  border-radius: 6px;
}

.command-item code {
  background: #1a1a2e;
  color: #f56565;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.875rem;
}

.command-item span {
  color: #a0aec0;
}

.navigation-buttons {
  display: flex;
  justify-content: space-between;
  margin-top: 3rem;
  padding-top: 2rem;
  border-top: 1px solid #4a5568;
}

.nav-btn {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-btn--back {
  background: transparent;
  border: 1px solid #4a5568;
  color: #a0aec0;
}

.nav-btn--back:hover {
  border-color: #718096;
  color: #e2e8f0;
}

.nav-btn--continue {
  background: #dc382c;
  border: none;
  color: white;
}

.nav-btn--continue:hover {
  background: #c42f24;
}

/* Markdown Content Styles */
.markdown-content {
  color: #e2e8f0;
  line-height: 1.7;
}

.markdown-content :deep(h1) {
  color: #ffffff;
  font-size: 1.75rem;
  margin-bottom: 1.5rem;
}

.markdown-content :deep(h2) {
  color: #dc382c;
  font-size: 1.25rem;
  margin-top: 2rem;
  margin-bottom: 1rem;
}

.markdown-content :deep(h3) {
  color: #ffffff;
  font-size: 1.1rem;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

.markdown-content :deep(p) {
  margin-bottom: 1rem;
}

.markdown-content :deep(ul),
.markdown-content :deep(ol) {
  padding-left: 1.5rem;
  margin-bottom: 1rem;
}

.markdown-content :deep(li) {
  margin-bottom: 0.5rem;
}

.markdown-content :deep(code) {
  background: #1a1a2e;
  color: #f56565;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-family: monospace;
}

.markdown-content :deep(pre) {
  background: #1a1a2e;
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
  margin: 1rem 0;
}

.markdown-content :deep(pre code) {
  background: none;
  padding: 0;
  color: #e2e8f0;
}

.markdown-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1rem 0;
}

.markdown-content :deep(th),
.markdown-content :deep(td) {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #4a5568;
}

.markdown-content :deep(th) {
  color: #ffffff;
  font-weight: 600;
}

.markdown-content :deep(td) {
  color: #a0aec0;
}
</style>
