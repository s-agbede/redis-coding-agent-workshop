<template>
  <div class="workshop-scrollable-demo">
    <slot name="header"></slot>

    <main class="demo-layout">
      <!-- Left panel: Scrollable instructions -->
      <div class="demo-instructions" ref="instructionsPanel">
        <div
          v-for="(section, index) in sections"
          :key="section.sectionId || index"
          :ref="el => setSectionRef(section.sectionId || index, el)"
          class="scroll-section"
          :class="{ 'scroll-section--active': activeSection === (section.sectionId || index) }"
        >
          <h2 v-if="section.title" class="section-title">{{ section.title }}</h2>
          
          <div v-if="section.body" class="section-body">
            <WorkshopMarkdownContent :body="section.body" />
          </div>

          <!-- Code snippet with language toggle -->
          <div v-if="section.codeSnippet" class="section-code">
            <div class="code-header">
              <span class="code-title">{{ getCodeTitle(section) }}</span>
              <div v-if="hasMultipleLanguages(section)" class="language-toggle">
                <button
                  v-for="lang in availableLanguages"
                  :key="lang"
                  :class="{ active: selectedLanguage === lang }"
                  @click="selectedLanguage = lang"
                >
                  {{ languageLabels[lang] || lang }}
                </button>
              </div>
            </div>
            <pre class="code-block"><code :class="`language-${getCodeLanguage(section)}`">{{ getCodeContent(section) }}</code></pre>
          </div>

          <!-- Custom content slot -->
          <slot :name="`section-${section.sectionId}`" :section="section"></slot>

          <!-- Actions -->
          <div v-if="section.actions?.length" class="section-actions">
            <button
              v-for="action in section.actions"
              :key="action.id"
              :class="['btn', `btn--${action.variant || 'secondary'}`]"
              @click="handleAction(action)"
            >
              {{ action.label }}
            </button>
          </div>
        </div>
      </div>

      <!-- Right panel: Sticky demo app -->
      <div class="demo-app-container">
        <div class="demo-app-header">
          <span class="app-title">{{ appTitle }}</span>
          <div class="app-status" :class="{ connected: appReady }">
            {{ appReady ? 'Connected' : 'Loading...' }}
          </div>
        </div>
        <div class="demo-app-frame">
          <iframe
            v-if="appUrl"
            ref="demoFrame"
            :src="appUrl"
            @load="onFrameLoad"
            :title="appTitle"
          ></iframe>
          <slot v-else name="app"></slot>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
import WorkshopMarkdownContent from './WorkshopMarkdownContent.vue'

export default {
  name: 'WorkshopScrollableDemo',
  components: {
    WorkshopMarkdownContent
  },
  props: {
    sections: {
      type: Array,
      required: true
    },
    appUrl: {
      type: String,
      default: ''
    },
    appTitle: {
      type: String,
      default: 'Demo App'
    },
    availableLanguages: {
      type: Array,
      default: () => ['java', 'python']
    },
    defaultLanguage: {
      type: String,
      default: 'java'
    },
    languageLabels: {
      type: Object,
      default: () => ({
        java: 'Java',
        python: 'Python',
        javascript: 'JavaScript',
        go: 'Go'
      })
    }
  },
  emits: ['action', 'section-change', 'language-change'],
  data() {
    return {
      activeSection: null,
      selectedLanguage: this.defaultLanguage,
      appReady: false,
      sectionRefs: {},
      scrollObserver: null
    }
  },
  watch: {
    selectedLanguage(newLang) {
      this.$emit('language-change', newLang)
    }
  },
  mounted() {
    if (this.sections.length) {
      this.activeSection = this.sections[0].sectionId || 0
    }
    this.$nextTick(() => this.setupScrollObserver())
  },
  beforeUnmount() {
    if (this.scrollObserver) {
      this.scrollObserver.disconnect()
    }
  },
  methods: {
    setSectionRef(sectionId, el) {
      if (el) {
        this.sectionRefs[sectionId] = el
      }
    },
    setupScrollObserver() {
      const options = {
        root: this.$refs.instructionsPanel,
        rootMargin: '-20% 0px -60% 0px',
        threshold: 0
      }

      this.scrollObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const sectionId = Object.keys(this.sectionRefs).find(
              id => this.sectionRefs[id] === entry.target
            )
            if (sectionId !== undefined && sectionId !== this.activeSection) {
              this.activeSection = sectionId
              this.onSectionChange(sectionId)
            }
          }
        })
      }, options)

      Object.values(this.sectionRefs).forEach(el => {
        if (el) this.scrollObserver.observe(el)
      })
    },
    onSectionChange(sectionId) {
      const section = this.sections.find(s => (s.sectionId || this.sections.indexOf(s)) == sectionId)
      this.$emit('section-change', { sectionId, section })
      
      // Send action to iframe if applicable
      if (section?.appAction && this.$refs.demoFrame?.contentWindow) {
        this.$refs.demoFrame.contentWindow.postMessage({
          type: 'workshop-action',
          ...section.appAction
        }, '*')
      }
    },
    onFrameLoad() {
      this.appReady = true
    },
    hasMultipleLanguages(section) {
      return section.codeSnippet && (
        section.codeSnippetPython ||
        section.codeSnippetJavascript ||
        section.codeSnippetGo
      )
    },
    getCodeTitle(section) {
      const snippet = this.getActiveCodeSnippet(section)
      return snippet?.title || 'Code'
    },
    getCodeLanguage(section) {
      const snippet = this.getActiveCodeSnippet(section)
      return snippet?.language || 'text'
    },
    getCodeContent(section) {
      const snippet = this.getActiveCodeSnippet(section)
      return snippet?.code || ''
    },
    getActiveCodeSnippet(section) {
      const langKey = `codeSnippet${this.capitalize(this.selectedLanguage)}`
      return section[langKey] || section.codeSnippet
    },
    capitalize(str) {
      if (!str) return ''
      return str.charAt(0).toUpperCase() + str.slice(1)
    },
    handleAction(action) {
      this.$emit('action', action)
    }
  }
}
</script>

<style scoped>
.workshop-scrollable-demo {
  min-height: 100vh;
  background: var(--color-bg-primary);
  display: flex;
  flex-direction: column;
}

.demo-layout {
  flex: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0;
  height: calc(100vh - 60px);
}

.demo-instructions {
  overflow-y: auto;
  padding: 2rem;
  border-right: 1px solid var(--color-border);
}

.scroll-section {
  padding: 2rem 0;
  border-bottom: 1px solid var(--color-border);
  opacity: 0.6;
  transition: opacity 0.3s ease;
}

.scroll-section--active {
  opacity: 1;
}

.scroll-section:last-child {
  border-bottom: none;
}

.section-title {
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--color-text-primary);
  margin-bottom: 1rem;
}

.section-body {
  color: var(--color-text-secondary);
  line-height: 1.7;
  margin-bottom: 1.5rem;
}

.section-code {
  margin: 1.5rem 0;
  border-radius: 0.5rem;
  overflow: hidden;
  background: var(--color-bg-secondary);
}

.code-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: var(--color-bg-tertiary);
  border-bottom: 1px solid var(--color-border);
}

.code-title {
  font-size: 0.875rem;
  color: var(--color-text-secondary);
}

.language-toggle {
  display: flex;
  gap: 0.25rem;
}

.language-toggle button {
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  background: transparent;
  border: 1px solid var(--color-border);
  border-radius: 0.25rem;
  color: var(--color-text-tertiary);
  cursor: pointer;
  transition: all 0.2s;
}

.language-toggle button.active {
  background: var(--color-primary);
  border-color: var(--color-primary);
  color: white;
}

.code-block {
  padding: 1rem;
  margin: 0;
  overflow-x: auto;
  font-family: 'JetBrains Mono', 'Fira Code', monospace;
  font-size: 0.875rem;
  line-height: 1.5;
  color: var(--color-text-primary);
}

.section-actions {
  margin-top: 1.5rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  font-size: 1rem;
  font-weight: 500;
  border: none;
  border-radius: 0.375rem;
  cursor: pointer;
  transition: all 0.2s;
}

.btn--primary {
  background: var(--color-primary);
  color: white;
}

.btn--primary:hover {
  background: var(--color-primary-hover);
}

.btn--secondary {
  background: var(--color-bg-tertiary);
  color: var(--color-text-primary);
}

.demo-app-container {
  display: flex;
  flex-direction: column;
  background: var(--color-bg-secondary);
  position: sticky;
  top: 0;
  height: calc(100vh - 60px);
}

.demo-app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  background: var(--color-bg-tertiary);
  border-bottom: 1px solid var(--color-border);
}

.app-title {
  font-weight: 600;
  color: var(--color-text-primary);
}

.app-status {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 1rem;
  background: var(--color-bg-primary);
  color: var(--color-text-tertiary);
}

.app-status.connected {
  background: var(--color-success-bg, rgba(34, 197, 94, 0.1));
  color: var(--color-success, #22c55e);
}

.demo-app-frame {
  flex: 1;
  overflow: hidden;
}

.demo-app-frame iframe {
  width: 100%;
  height: 100%;
  border: none;
  background: white;
}
</style>
