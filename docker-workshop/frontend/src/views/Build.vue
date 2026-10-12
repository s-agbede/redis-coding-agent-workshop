<template>
  <div class="workshop-build">
    <WorkshopHeader
      :hub-url="homeUrl"
      title="Build a coding agent"
      :steps="['Welcome', 'Workshop']"
      :current-step="2"
      :clickable="true"
      @step-click="navigateToPhase"
    />

    <main class="build-layout">
      <!-- Left panel: Instructions with Steps -->
      <div ref="instructions" class="build-instructions">
        <!-- Loading State -->
        <div v-if="loadingSteps" class="loading-state">
          <p>Loading lessons...</p>
        </div>

        <!-- Error State -->
        <div v-else-if="stepsError" class="error-state">
          <p>Could not load the lessons: {{ stepsError }}</p>
        </div>

        <!-- Steps Content -->
        <template v-else>
          <!-- Step Progress Indicator -->
          <div class="step-progress">
            <button
              v-for="(step, index) in buildSteps" 
              :key="step.id"
              class="step-indicator"
              :class="{ 
                active: currentBuildStep === index,
                visited: visitedSteps.includes(index)
              }"
              :aria-current="currentBuildStep === index ? 'step' : undefined"
              @click="goToStep(index)"
            >
              <span class="step-number">
                <span>{{ index + 1 }}</span>
              </span>
              <span class="step-label">{{ step.title }}</span>
            </button>
          </div>

          <p v-if="navigationError" role="alert">{{ navigationError }}</p>
          <p v-if="fileListError" role="alert">{{ fileListError }} <button @click="loadGuideFiles">Retry file list</button></p>
          <!-- Current Step Content -->
          <div class="step-content">
            <button v-if="currentStep.editorFile" class="open-file" @click="openFile(currentStep.editorFile)">Open {{ currentStep.editorFile }}</button>
            <h2 ref="stepHeading" tabindex="-1" class="step-title">{{ currentStep.title }}</h2>
            <LessonContent class="step-description" :html="renderedContent" :file-paths="filePaths" :terminal-available="terminalAvailable" @open-file="openFile" @show-terminal="showTerminal" />
            
            <!-- Step Action (if defined) -->
            <div v-if="currentStep.action" class="step-action">
              <p class="action-prompt">{{ currentStep.action.prompt }}</p>
              <div v-if="currentStep.action.hint" class="action-hint">
                <strong>Hint:</strong> {{ currentStep.action.hint }}
              </div>
            </div>

          </div>

          <!-- Step Navigation -->
          <div class="step-navigation">
            <button 
              class="step-nav-btn step-nav-btn--prev" 
              :disabled="currentBuildStep === 0"
              @click="prevStep"
            >
              Previous Step
            </button>
            <span class="step-counter">Step {{ currentBuildStep + 1 }} of {{ buildSteps.length }}</span>
            <button 
              v-if="currentBuildStep < buildSteps.length - 1"
              class="step-nav-btn step-nav-btn--next" 
              @click="nextStep"
            >
              Next Step
            </button>
            <button 
              v-else
              class="step-nav-btn step-nav-btn--complete" 
              @click="$router.push('/')"
            >
              Back to welcome
            </button>
          </div>
        </template>
      </div>

    </main>
  </div>
</template>

<script>
import WorkshopHeader from '@redis-workshop/components/components/WorkshopHeader.vue'
import { loadAllBuildSteps, markdownToHtml } from '../utils/buildSteps'
import LessonContent from '../components/LessonContent.vue'
import { getBasePath } from '../utils/basePath'

export default {
  name: 'WorkshopBuild',
  components: { WorkshopHeader, LessonContent },
  data() {
    return {
      homeUrl: `${getBasePath()}/`,
      buildSteps: [],
      currentBuildStep: 0,
      visitedSteps: [],
      navigationError: '',
      fileListError: '',
      filePaths: [],
      loadingSteps: true,
      stepsError: null
    }
  },
  computed: {
    terminalAvailable() {
      return !!window.parent && window.parent !== window
    },
    currentStep() {
      return this.buildSteps[this.currentBuildStep] || { title: '', content: '' }
    },
    renderedContent() {
      return markdownToHtml(this.currentStep.content)
    }
  },
  methods: {
    showTerminal() {
      if (this.terminalAvailable) {
        window.parent.postMessage({ type: 'show-workshop-terminal' }, window.location.origin)
      }
    },
    async loadGuideFiles() {
      try {
        const response = await fetch('/api/editor/files')
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
        const files = await response.json()
        if (!Array.isArray(files) || !files.every(file => typeof file?.path === 'string')) throw new Error('Invalid file list')
        this.filePaths = files.map(file => file.path)
        this.fileListError = ''
      } catch {
        this.fileListError = 'Could not load workspace files. You can still read the lessons.'
      }
    },
    openFile(path) {
      if (!this.terminalAvailable) {
        this.navigationError = 'Open the workbench using the link above, then use its Code panel to edit files in VS Code.'
        return false
      }
      if (!this.filePaths.includes(path)) {
        this.navigationError = 'This file is not available in the workspace.'
        this.fileListError = 'Retry the file list if files have changed.'
        return false
      }
      this.navigationError = ''
      window.parent.postMessage({ type: 'open-workshop-file', path }, window.location.origin)
      return true
    },
    navigateToPhase(step) {
      this.$router.push(step === 1 ? '/' : '/build')
    },
    async goToStep(index) {
      if (index < 0 || index >= this.buildSteps.length) return
      this.currentBuildStep = index
      if (!this.visitedSteps.includes(index)) this.visitedSteps.push(index)
      try { sessionStorage.setItem('coding-agent-workshop-lesson-v3', this.currentStep.file) }
      catch { this.navigationError = 'Your current lesson cannot be saved in this browser. Navigation still works.' }
      await this.$nextTick()
      this.$refs.stepHeading?.focus({ preventScroll: true })
      if (this.$refs.instructions) this.$refs.instructions.scrollTop = 0
      this.$refs.stepHeading?.scrollIntoView({ block: 'start' })
    },
    nextStep() { this.goToStep(this.currentBuildStep + 1) },
    prevStep() { this.goToStep(this.currentBuildStep - 1) }
  },
  async mounted() {
    if (this.terminalAvailable) void this.loadGuideFiles()
    try {
      this.buildSteps = await loadAllBuildSteps()
      let storedStep = 0
      try { storedStep = this.buildSteps.findIndex(step => step.file === sessionStorage.getItem('coding-agent-workshop-lesson-v3')) }
      catch { this.navigationError = 'Your current lesson cannot be saved in this browser. Navigation still works.' }
      this.loadingSteps = false
      await this.goToStep(storedStep >= 0 ? storedStep : 0)
    } catch (err) {
      this.stepsError = err.message
    } finally {
      this.loadingSteps = false
    }
  }
}
</script>

<style scoped>
.workshop-build { min-height: 100vh; background: #1a1a2e; }
.build-instructions { padding: 1rem; }

.loading-state,
.error-state {
  color: #a0aec0;
  padding: 2rem;
  text-align: center;
}

.error-state {
  color: #f56565;
}

/* Step Progress Indicator */
.step-progress {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  flex-wrap: wrap;
}

.step-indicator {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: #2d3748;
  border-radius: 9999px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.step-indicator:hover {
  background: #3d4758;
}

.step-indicator.active {
  background: rgba(220, 56, 44, 0.2);
  border-color: #dc382c;
}

.step-indicator.visited {
  border-color: #718096;
}

.step-number {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: #4a5568;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  font-weight: 600;
  color: #e2e8f0;
}

.step-indicator.active .step-number {
  background: #dc382c;
  color: white;
}

.step-label {
  font-size: 0.875rem;
  color: #a0aec0;
}

.step-indicator.active .step-label {
  color: #ffffff;
  font-weight: 500;
}

/* Step Content */
.step-content {
  flex: 1;
  padding: 1.5rem;
  background: #2d3748;
  border-radius: 8px;
  margin-bottom: 1.5rem;
}

.step-title {
  color: #ffffff;
  font-size: 1.5rem;
  margin-bottom: 1rem;
}
.step-title:focus-visible { outline: 2px solid #7aa2f7; outline-offset: 4px; }
.step-description {
  color: #e2e8f0;
  line-height: 1.7;
}

.step-description :deep(h1),
.step-description :deep(h2),
.step-description :deep(h3) {
  color: #ffffff;
  margin-top: 1.5rem;
  margin-bottom: 0.75rem;
}

.step-description :deep(h1) {
  font-size: 1.5rem;
}

.step-description :deep(h2) {
  font-size: 1.25rem;
}

.step-description :deep(h3) {
  font-size: 1.1rem;
}

.step-description :deep(code) {
  background: #1a1a2e;
  color: #f56565;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-family: monospace;
}

.step-description :deep(pre) {
  background: #1a1a2e;
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
  margin: 1rem 0;
}

.step-description :deep(pre code) {
  background: none;
  padding: 0;
  color: #e2e8f0;
}

.step-description :deep(ul),
.step-description :deep(ol) {
  padding-left: 1.5rem;
  margin: 1rem 0;
}

.step-description :deep(li) {
  margin-bottom: 0.5rem;
}

.step-description :deep(details) {
  border: 1px solid #718096;
  border-radius: 6px;
  padding: 0.75rem 1rem;
  margin: 1rem 0;
}

.step-description :deep(summary) {
  cursor: pointer;
  color: #c0caf5;
  font-weight: 600;
}

.step-description :deep(summary:focus-visible) {
  outline: 2px solid #7aa2f7;
  outline-offset: 4px;
}

/* Step Action */
.step-action {
  margin-top: 1.5rem;
  padding: 1rem;
  background: rgba(220, 56, 44, 0.1);
  border-left: 3px solid #dc382c;
  border-radius: 0 6px 6px 0;
}

.action-prompt {
  color: #ffffff;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.action-hint {
  color: #a0aec0;
  font-size: 0.875rem;
}

/* Step Navigation */
.step-navigation {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 0;
  border-top: 1px solid #4a5568;
}

.step-nav-btn {
  padding: 0.625rem 1.25rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.step-nav-btn--prev {
  background: transparent;
  border: 1px solid #4a5568;
  color: #a0aec0;
}

.step-nav-btn--prev:hover:not(:disabled) {
  border-color: #718096;
  color: #e2e8f0;
}

.step-nav-btn--prev:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.step-nav-btn--next {
  background: #dc382c;
  border: none;
  color: white;
}

.step-nav-btn--next:hover {
  background: #c92d22;
}

.step-nav-btn--complete {
  background: #48bb78;
  border: none;
  color: white;
}

.step-nav-btn--complete:hover {
  background: #38a169;
}

.step-counter {
  color: #718096;
  font-size: 0.875rem;
}

.open-file { margin-bottom: 1rem; padding: .5rem .75rem; border: 1px solid #7aa2f7; border-radius: 4px; background: #1e2030; color: #c0caf5; cursor: pointer; }
</style>
