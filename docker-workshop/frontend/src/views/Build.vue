<template>
  <div class="workshop-build" :class="{ 'workshop-build--expanded': expandedPanel, 'workshop-build--guide': guideMode }">
    <WorkshopHeader
      :hub-url="guideMode ? '/guide/' : '/'"
      :hidden="!!expandedPanel"
      title="Build a coding agent"
      :steps="phaseSteps"
      :current-step="currentPhaseIndex"
      :clickable="true"
      @step-click="navigateToPhase"
    />

    <main class="build-layout">
      <!-- Left panel: Instructions with Steps -->
      <div ref="instructions" class="build-instructions" :hidden="!!expandedPanel && expandedPanel !== 'instructions'" :style="guideMode ? {} : { flexBasis: `${instructionsPercent}%` }">
        <div v-if="!guideMode" class="instructions-toolbar">
          <span>Instructions</span>
          <PanelToggle label="instructions" :expanded="expandedPanel === 'instructions'" @toggle="expandedPanel = expandedPanel === 'instructions' ? null : 'instructions'" />
        </div>
        
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

      <!-- Resize Handle -->
      <PanelDivider v-if="!guideMode" v-model:value="instructionsPercent" class="workspace-divider" :hidden="!!expandedPanel" orientation="vertical" label="Resize instructions and workspace" />

      <!-- Right panel: Code Editor + App Preview -->
      <div v-if="!guideMode" class="build-interactive-panel" :hidden="expandedPanel === 'instructions'">
        <BuildPanel
          ref="workspace"
          :expanded-panel="expandedPanel"
          @expand="expandedPanel = $event"
          :language="selectedLanguage"
          :selected-file="selectedFile"
          @file-change="selectedFile = $event"
          @files-loaded="filePaths = $event"
          :app-url="appUrl"
          :app-title="appTitle"
          :default-editor-percent="editorPercent"
        />
      </div>
    </main>
  </div>
</template>

<script>
import WorkshopHeader from '@redis-workshop/components/components/WorkshopHeader.vue'
import { loadAllBuildSteps, markdownToHtml } from '../utils/buildSteps'
import { loadWorkshopConfig, getPhaseStepTitles, getEnabledPhases, isPhaseEnabled } from '../utils/workshopConfig'
import BuildPanel from '../components/BuildPanel.vue'
import PanelToggle from '../components/PanelToggle.vue'
import PanelDivider from '../components/PanelDivider.vue'
import LessonContent from '../components/LessonContent.vue'
import { getBasePath } from '../utils/basePath'

export default {
  name: 'WorkshopBuild',
  components: {
    WorkshopHeader,
    BuildPanel,
    PanelToggle,
    PanelDivider,
    LessonContent
  },
  data() {
    return {
      config: null,
      phaseSteps: ['Welcome', 'Workshop'],
      enabledPhases: [],
      currentPhaseIndex: 2,
      // Build steps from markdown files
      buildSteps: [],
      currentBuildStep: 0,
      visitedSteps: [],
      navigationError: '',
      guideMode: getBasePath() === '/guide' || /^\/guide(?:\/|$)/.test(window.location?.pathname || ''),
      fileListError: '',
      loadingSteps: true,
      stepsError: null,
      // Resize state
      instructionsPercent: 50,
      expandedPanel: null,
      // Panel configuration
      selectedLanguage: 'python',
      selectedFile: 'first_call.py',
      filePaths: [],
      appUrl: '/app/',
      appTitle: 'Task-list app',
      editorPercent: 70
    }
  },
  computed: {
    terminalAvailable() {
      return !this.guideMode || window.parent !== window
    },
    currentStep() {
      return this.buildSteps[this.currentBuildStep] || { title: '', content: '' }
    },
    renderedContent() {
      return markdownToHtml(this.currentStep.content)
    }
  },
  methods: {
    async showTerminal() {
      if (this.guideMode) {
        if (window.parent !== window) window.parent.postMessage({ type: 'show-workshop-terminal' }, window.location.origin)
        return
      }
      this.expandedPanel = null
      await this.$nextTick()
      this.$refs.workspace?.showTerminal()
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
    async openFile(path) {
      if (this.guideMode) {
        if (window.parent === window) {
          this.navigationError = 'Open the workbench using the link above to view and edit files.'
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
      }
      if (this.expandedPanel !== 'editor') this.expandedPanel = null
      await this.$nextTick()
      return this.$refs.workspace?.openFile(path)
    },
    navigateToPhase(step) {
      const phase = this.enabledPhases[step - 1]
      if (phase) {
        this.$router.push(phase.route)
      }
    },
    async goToStep(index) {
      if (index < 0 || index >= this.buildSteps.length) return
      this.currentBuildStep = index
      if (!this.visitedSteps.includes(index)) this.visitedSteps.push(index)
      try { sessionStorage.setItem('coding-agent-workshop-lesson-v3', this.currentStep.file) }
      catch { this.navigationError = 'Your current lesson cannot be saved in this browser. Navigation still works.' }
      this.selectedFile = this.currentStep.editorFile || this.selectedFile
      await this.focusLesson()
    },
    async focusLesson() {
      await this.$nextTick()
      this.$refs.stepHeading?.focus({ preventScroll: true })
      if (this.$refs.instructions) this.$refs.instructions.scrollTop = 0
      // The embedded guide and responsive layout both scroll the document.
      if (this.guideMode || window.matchMedia?.('(max-width: 900px)').matches) {
        this.$refs.stepHeading?.scrollIntoView({ block: 'start' })
      }
    },
    nextStep() {
      if (this.currentBuildStep < this.buildSteps.length - 1) {
        this.goToStep(this.currentBuildStep + 1)
      }
    },
    prevStep() {
      if (this.currentBuildStep > 0) {
        this.goToStep(this.currentBuildStep - 1)
      }
    },
    restorePanel(event) {
      if (event.key === 'Escape') this.expandedPanel = null
    }
  },
  beforeUnmount() { document.removeEventListener('keydown', this.restorePanel) },
  async mounted() {
    document.addEventListener('keydown', this.restorePanel)
    if (this.guideMode) void this.loadGuideFiles()
    // Load workshop config
    try {
      this.config = await loadWorkshopConfig()
      
      // Redirect if build phase is disabled
      if (!isPhaseEnabled(this.config, 'build')) {
        this.$router.replace('/')
        return
      }
      
      this.phaseSteps = getPhaseStepTitles(this.config)
      this.enabledPhases = getEnabledPhases(this.config)
      this.currentPhaseIndex = this.enabledPhases.findIndex(p => p.id === 'build') + 1
      
      // Set panel width from config
      if (this.config.buildPanel?.defaultWidth) {
        this.instructionsPercent = Math.max(20, Math.min(80, 100 * (1 - this.config.buildPanel.defaultWidth / window.innerWidth)))
      }

      // Load App URL and title from config
      if (this.config.buildPanel?.appUrl) {
        this.appUrl = this.config.buildPanel.appUrl
      }
      if (this.config.buildPanel?.appTitle) {
        this.appTitle = this.config.buildPanel.appTitle
      }
      if (this.config.buildPanel?.editorPercent) {
        this.editorPercent = this.config.buildPanel.editorPercent
      }
    } catch (err) {
      console.warn('Failed to load workshop config:', err)
    }

    // Load build steps
    try {
      this.buildSteps = await loadAllBuildSteps()
      let storedStep = 0
      try { storedStep = this.buildSteps.findIndex(step => step.file === sessionStorage.getItem('coding-agent-workshop-lesson-v3')) }
      catch { this.navigationError = 'Your current lesson cannot be saved in this browser. Navigation still works.' }
      this.loadingSteps = false
      await this.goToStep(Number.isInteger(storedStep) && storedStep >= 0 && storedStep < this.buildSteps.length ? storedStep : 0)
    } catch (err) {
      this.stepsError = err.message
      // Fallback steps if loading fails
      this.buildSteps = [
        {
          id: 'fallback',
          title: 'Build Step',
          content: 'Failed to load build steps. Please check that the build-steps folder contains a manifest.yaml file.',
          action: null
        }
      ]
    } finally {
      this.loadingSteps = false
    }
  }
}
</script>

<style scoped>
.workshop-build {
  height: 100vh;
  min-height: 600px;
  background: #1a1a2e;
  display: flex;
  flex-direction: column;
}

.build-layout {
  min-height: 0;
  display: flex;
  flex: 1;
  overflow: hidden;
  position: relative;
}

.build-instructions {
  min-width: 0;
  padding: 1.5rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}
.workshop-build [hidden] { display: none !important; }
.workshop-build--guide { height: auto; min-height: 100vh; }
.workshop-build--guide .build-layout { display: block; overflow: visible; }
.workshop-build--guide .build-instructions { width: 100%; overflow: visible; padding: 1rem; }
.instructions-toolbar { display: flex; align-items: center; justify-content: space-between; gap: 1rem; margin-bottom: 1rem; font-size: .85rem; color: #cbd5e0; }

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

/* Right Panel */
.build-interactive-panel {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}
.open-file { margin-bottom: 1rem; padding: .5rem .75rem; border: 1px solid #7aa2f7; border-radius: 4px; background: #1e2030; color: #c0caf5; cursor: pointer; }
@media (max-width: 900px) {
  .workshop-build { height: auto; }
  .build-layout { flex-direction: column; }
  .build-instructions { width: 100%; flex-basis: auto !important; }
  .build-interactive-panel { width: 100%; flex: none; height: 750px; }
  .workspace-divider { display: none; }
}
.workshop-build--expanded { position: fixed; inset: 0; z-index: 100; height: 100vh; height: 100dvh; min-height: 0; }
.workshop-build--expanded .build-instructions,
.workshop-build--expanded .build-interactive-panel { flex: 1; width: 100%; height: 100%; min-height: 0; }
.workshop-build--expanded .instructions-toolbar { position: sticky; top: -1.5rem; margin-top: -1.5rem; padding: .75rem 0; background: #1a1a2e; z-index: 1; }
</style>
