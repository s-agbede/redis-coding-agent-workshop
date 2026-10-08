<template>
  <div class="app-embed">
    <div class="app-header">
      <div class="app-title">
        <span class="app-icon">A</span>
        {{ title }}
      </div>
      <div class="app-actions">
        <button class="action-btn" @click="reload" title="Reload">
          <span class="reload-icon">&#8635;</span>
        </button>
        <button class="action-btn" @click="openExternal" title="Open in new tab">
          <span class="external-icon">&#8599;</span>
        </button>
      </div>
    </div>

    <div class="app-container">
      <div v-if="loading" class="loading-overlay">
        <div class="spinner"></div>
        <p>Loading App...</p>
      </div>
      <div v-if="!url" class="no-url-message">
        <p>No app URL configured.</p>
        <p class="hint">Set <code>demoPanel.appUrl</code> in workshop.config.yaml</p>
      </div>
      <iframe
        v-else
        ref="appFrame"
        :title="title"
        :src="computedUrl"
        class="app-frame"
        @load="onFrameLoad"
        @error="onFrameError"
        allow="clipboard-read; clipboard-write"
      ></iframe>
    </div>
  </div>
</template>

<script>
import { getApiUrl } from '../utils/basePath'

export default {
  name: 'AppEmbed',
  props: {
    /**
     * App URL - can be absolute or relative to the workshop API
     */
    url: {
      type: String,
      default: ''
    },
    /**
     * Title shown in the header
     */
    title: {
      type: String,
      default: 'Application'
    }
  },
  data() {
    return {
      loading: true
    }
  },
  computed: {
    computedUrl() {
      if (!this.url) return ''
      // If it's an absolute URL, use as-is
      if (this.url.startsWith('http://') || this.url.startsWith('https://') || this.url.startsWith('//')) {
        return this.url
      }
      // Otherwise, treat as relative to the API base
      return getApiUrl(this.url)
    }
  },
  methods: {
    onFrameLoad() {
      this.loading = false
    },
    onFrameError() {
      this.loading = false
    },
    reload() {
      this.loading = true
      if (this.$refs.appFrame) {
        this.$refs.appFrame.src = this.computedUrl
      }
    },
    openExternal() {
      if (this.computedUrl) {
        window.open(this.computedUrl, '_blank', 'noopener,noreferrer')
      }
    }
  }
}
</script>

<style scoped>
.app-embed {
  display: flex;
  flex-direction: column;
  height: 100%;
  background: #1e2030;
}

.app-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem 1rem;
  background: #161824;
  border-bottom: 1px solid #2d3748;
}

.app-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #e2e8f0;
  font-weight: 500;
  font-size: 0.875rem;
}

.app-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 0.75rem;
  font-weight: 700;
  border-radius: 4px;
}

.app-actions {
  display: flex;
  gap: 0.25rem;
}

.action-btn {
  background: transparent;
  border: 1px solid #4a5568;
  color: #a0aec0;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
  transition: all 0.2s;
}

.action-btn:hover {
  background: #2d3748;
  color: #e2e8f0;
  border-color: #667eea;
}

.reload-icon,
.external-icon {
  font-size: 1rem;
}

.app-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.loading-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(30, 32, 48, 0.9);
  z-index: 10;
}

.loading-overlay p {
  color: #a0aec0;
  margin-top: 1rem;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #2d3748;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.no-url-message {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #a0aec0;
  text-align: center;
  padding: 2rem;
}

.no-url-message .hint {
  font-size: 0.875rem;
  color: #718096;
  margin-top: 0.5rem;
}

.no-url-message code {
  background: #2d3748;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-family: monospace;
}

.app-frame {
  width: 100%;
  height: 100%;
  border: none;
  background: #fff;
}
</style>
