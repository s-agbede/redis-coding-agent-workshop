<template>
  <div class="workshop-welcome">
    <div class="intro-container">
      <div class="intro-header">
        <img src="@/assets/logo/small.png" alt="Redis Logo" class="intro-logo" />
        <h1 class="intro-title">{{ content?.title || 'Build a Coding Agent' }}</h1>
        <p class="intro-subtitle">{{ content?.subtitle || 'From first principles' }}</p>
      </div>

      <div class="intro-description">
        <p>{{ content?.description }}</p>
      </div>

      <div class="intro-meta">
        <div class="meta-item">
          <span class="meta-label">Time to allow</span>
          <span class="meta-value">{{ content?.estimatedMinutes || 30 }} minutes</span>
        </div>
      </div>

      <div class="intro-actions">
        <button class="btn-primary" @click="startWorkshop">
          Start Workshop
        </button>
      </div>
      <LessonContent v-if="content?.htmlContent" class="welcome-content" :html="content.htmlContent" :terminal-available="terminalAvailable" @show-terminal="showTerminal" />
    </div>
  </div>
</template>

<script>
import { loadWelcomeContent } from '../utils/pageContent'
import { loadWorkshopConfig, getNextPhase } from '../utils/workshopConfig'
import LessonContent from '../components/LessonContent.vue'

export default {
  name: 'WorkshopWelcome',
  components: { LessonContent },
  data() {
    return {
      content: null,
      config: null,
      loading: true,
      error: null
    }
  },
  computed: {
    terminalAvailable() {
      return !!window.parent && window.parent !== window
    }
  },
  async mounted() {
    // Load workshop config
    try {
      this.config = await loadWorkshopConfig()
    } catch (err) {
      console.warn('Failed to load workshop config:', err)
    }

    // Load content from welcome.md
    try {
      this.content = await loadWelcomeContent()
      if (!this.content) {
        // Use fallback content if file doesn't exist
        this.content = {
          title: this.config?.title || 'Build a Coding Agent',
          subtitle: this.config?.subtitle || 'From first principles',
          description: 'Unable to load workshop content. Refresh to try again.',
          estimatedMinutes: 90,
          difficulty: 'Beginner',
          topics: ['Python', 'Agent loops']
        }
      }
    } catch (err) {
      this.error = err.message
      // Use fallback content
      this.content = {
        title: 'Build a Coding Agent',
        subtitle: 'From first principles',
        description: 'Unable to load workshop content. Refresh to try again.',
        estimatedMinutes: 90,
        difficulty: 'Beginner',
        topics: ['Python', 'Agent loops']
      }
    } finally {
      this.loading = false
    }
  },
  methods: {
    showTerminal() {
      if (this.terminalAvailable) window.parent.postMessage({ type: 'show-workshop-terminal' }, window.location.origin)
    },
    startWorkshop() {
      // Navigate to the next enabled phase after welcome
      const nextPhase = getNextPhase(this.config, 'welcome')
      this.$router.push(nextPhase?.route || '/build')
    }
  }
}
</script>

<style scoped>
.workshop-welcome {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  padding: 2rem;
}

.intro-container {
  max-width: 800px;
  width: 100%;
  min-width: 0;
  text-align: center;
}

.intro-header {
  margin-bottom: 2rem;
}

.intro-logo {
  width: 80px;
  height: auto;
  margin-bottom: 1.5rem;
}

.intro-title {
  font-size: 2.5rem;
  color: #ffffff;
  margin-bottom: 0.5rem;
  font-weight: 700;
}

.intro-subtitle {
  font-size: 1.25rem;
  color: #a0aec0;
  margin: 0;
}

.intro-description {
  margin: 2rem 0;
  color: #e2e8f0;
  font-size: 1.1rem;
  line-height: 1.6;
}

.intro-meta {
  display: flex;
  justify-content: center;
  gap: 3rem;
  margin: 2rem 0;
}

.meta-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.meta-label {
  font-size: 0.875rem;
  color: #718096;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.meta-value {
  font-size: 1.1rem;
  color: #e2e8f0;
  font-weight: 500;
}

.intro-actions {
  margin: 2rem 0;
}
.welcome-content { text-align: left; color: #e2e8f0; line-height: 1.7; padding: 1.5rem; background: #222b40; border-radius: 8px; }
.welcome-content :deep(h1), .welcome-content :deep(h2), .welcome-content :deep(h3) { color: #fff; margin: 1.5rem 0 .7rem; line-height: 1.3; }
.welcome-content :deep(p) { margin: .75rem 0; }
.welcome-content :deep(ul), .welcome-content :deep(ol) { padding-left: 1.5rem; }
.welcome-content :deep(li) { margin: .5rem 0; }
.welcome-content :deep(a) { color: #a9c7ff; text-decoration: underline; }
.welcome-content :deep(pre) { padding: 1rem; overflow-x: auto; background: #1a1a2e; border-radius: 6px; }
.welcome-content :deep(code) { font: .9em/1.6 ui-monospace, SFMono-Regular, Consolas, monospace; color: #c0caf5; }
.welcome-content :deep(table) { border-collapse: collapse; width: 100%; }
.welcome-content :deep(th), .welcome-content :deep(td) { border: 1px solid #4a5568; padding: .6rem; vertical-align: top; }

.btn-primary {
  background: #dc382c;
  color: white;
  border: none;
  padding: 1rem 2.5rem;
  font-size: 1.1rem;
  font-weight: 600;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-primary:hover {
  background: #c42f24;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(220, 56, 44, 0.4);
}
</style>
