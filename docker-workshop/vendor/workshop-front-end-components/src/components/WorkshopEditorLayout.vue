<template>
  <div class="workshop-editor">
    <div class="main-container">
      <div
        class="workshop-panel"
        :class="{ 'workshop-panel--resizing': isResizing }"
        :style="workshopPanelStyle"
      >
        <div class="workshop-header">
          <h2>
            <div class="logo-small">
              <img src="@/assets/logo/small.png" alt="Redis Logo" width="24" height="24" />
            </div>
            {{ title }}
          </h2>
        </div>
        <div class="workshop-content">
          <slot name="instructions"></slot>
        </div>
      </div>
      <button
        type="button"
        class="workshop-panel-resize-handle"
        :class="{ 'workshop-panel-resize-handle--active': isResizing }"
        aria-label="Resize instructions panel"
        title="Drag to resize instructions panel"
        @pointerdown="startResize"
      ></button>

      <CodeEditor
        ref="editor"
        :files="files"
        :diagnostics="diagnostics"
        @file-loaded="onFileLoaded"
        @file-saved="onFileSaved"
        @content-changed="onContentChanged"
      />
    </div>
  </div>
</template>

<script>
import CodeEditor from './CodeEditor.vue';
import { getWorkshopHubUrl } from '../utils/basePath.js';

export default {
  name: 'WorkshopEditorLayout',
  components: { CodeEditor },
  data() {
    return {
      panelWidth: 400,
      isResizing: false
    };
  },
  props: {
    title: { type: String, required: true },
    files: { type: Array, required: true },
    diagnostics: { type: Array, default: () => [] }
  },
  emits: ['file-loaded', 'file-saved', 'content-changed'],
  computed: {
    workshopPanelStyle() {
      return {
        width: `${this.panelWidth}px`
      };
    },
    workshopHubUrl() {
      return getWorkshopHubUrl();
    }
  },
  mounted() {
    this.restorePanelWidth();
  },
  beforeUnmount() {
    this.stopResize();
  },
  methods: {
    clampPanelWidth(nextWidth) {
      const minWidth = 320;
      const maxWidth = Math.max(minWidth, window.innerWidth - 320);
      return Math.min(Math.max(nextWidth, minWidth), maxWidth);
    },
    persistPanelWidth() {
      localStorage.setItem('workshopEditorPanelWidth', String(this.panelWidth));
    },
    onFileLoaded(data) {
      this.$emit('file-loaded', data);
    },
    onFileSaved(data) {
      this.$emit('file-saved', data);
    },
    onContentChanged(data) {
      this.$emit('content-changed', data);
    },
    onResize(event) {
      if (!this.isResizing) {
        return;
      }

      this.panelWidth = this.clampPanelWidth(event.clientX);
    },
    restorePanelWidth() {
      const savedWidth = Number.parseInt(localStorage.getItem('workshopEditorPanelWidth') || '', 10);
      if (!Number.isNaN(savedWidth)) {
        this.panelWidth = this.clampPanelWidth(savedWidth);
      }
    },
    startResize(event) {
      event.preventDefault();
      this.isResizing = true;
      window.addEventListener('pointermove', this.onResize);
      window.addEventListener('pointerup', this.stopResize);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
    },
    stopResize() {
      if (!this.isResizing) {
        return;
      }

      this.isResizing = false;
      window.removeEventListener('pointermove', this.onResize);
      window.removeEventListener('pointerup', this.stopResize);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      this.persistPanelWidth();
    },
    // Proxy methods to CodeEditor
    loadFile(fileName) { return this.$refs.editor.loadFile(fileName); },
    save() { return this.$refs.editor.save(); },
    reload() { return this.$refs.editor.reload(); },
    showStatus(msg, type) { return this.$refs.editor.showStatus(msg, type); },
    updateContent(content) { return this.$refs.editor.updateContent(content); },
    getCurrentContent() { return this.$refs.editor.getCurrentContent(); },
    getCurrentFile() { return this.$refs.editor.getCurrentFile(); }
  }
};
</script>

<style scoped>
.workshop-editor { margin: 0; padding: 0; background: #1a1a1a; overflow: hidden; }
.main-container { display: flex; height: 100vh; width: 100vw; }
.workshop-panel { width: 400px; min-width: 320px; background: #1e1e1e; border-right: 1px solid var(--color-border); display: flex; flex-direction: column; overflow: hidden; flex-shrink: 0; }
.workshop-panel--resizing { pointer-events: none; }
.workshop-header { background: #252526; padding: var(--spacing-4); border-bottom: 1px solid var(--color-border); }
.workshop-header h2 { margin: 0; color: #DC382C; font-size: var(--font-size-lg); display: flex; align-items: center; gap: var(--spacing-2); }
.logo-small { display: inline-block; }
.workshop-panel-resize-handle { width: 10px; min-width: 10px; padding: 0; border: 0; background: linear-gradient(180deg, rgba(59, 130, 246, 0) 0%, rgba(59, 130, 246, 0.2) 50%, rgba(59, 130, 246, 0) 100%); cursor: col-resize; position: relative; flex-shrink: 0; }
.workshop-panel-resize-handle::before { content: ''; position: absolute; inset: 0 3px; background: rgba(59, 130, 246, 0.18); transition: background 150ms ease; }
.workshop-panel-resize-handle:hover::before,
.workshop-panel-resize-handle--active::before { background: rgba(96, 165, 250, 0.5); }
.workshop-content { flex: 1; overflow-y: auto; padding: var(--spacing-6); color: #cccccc; font-size: var(--font-size-sm); line-height: 1.6; }
.workshop-content :deep(h3) { color: #fff; font-size: var(--font-size-base); margin-top: 0; }
.workshop-content :deep(h4) { color: #4fc3f7; font-size: var(--font-size-sm); margin-top: var(--spacing-6); margin-bottom: var(--spacing-3); font-weight: var(--font-weight-semibold); }
.workshop-content :deep(ol) { padding-left: var(--spacing-6); }
.workshop-content :deep(li) { margin-bottom: var(--spacing-3); }
.workshop-content :deep(.step-with-button) { display: flex; align-items: flex-start; gap: var(--spacing-2); margin-bottom: var(--spacing-3); }
.workshop-content :deep(.step-content) { flex: 1; min-width: 0; word-break: break-word; }
.workshop-content :deep(.step-content code) { word-break: break-all; }
.workshop-content :deep(.step-content ul) { margin-top: var(--spacing-2); padding-left: var(--spacing-5); }
.workshop-content :deep(.button-group) { display: flex; align-items: center; gap: var(--spacing-2); flex-shrink: 0; }
.workshop-content :deep(.tooltip-wrapper) { position: relative; display: flex; align-items: center; cursor: help; }
.workshop-content :deep(.tooltip-wrapper::after) { content: attr(data-tooltip); position: absolute; bottom: 100%; right: 0; background: #1e1e1e; color: #d4d4d4; padding: 8px 12px; border-radius: 4px; font-size: 0.8rem; white-space: normal; width: 250px; max-width: 250px; text-align: left; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3); border: 1px solid #3c3c3c; opacity: 0; visibility: hidden; transition: opacity 0.2s, visibility 0.2s; z-index: 1000; margin-bottom: 8px; line-height: 1.4; pointer-events: none; word-wrap: break-word; overflow-wrap: break-word; }
.workshop-content :deep(.tooltip-wrapper:hover::after) { opacity: 1; visibility: visible; }
.workshop-content :deep(.info-icon) { display: flex; align-items: center; justify-content: center; width: 18px; height: 18px; min-width: 18px; background: transparent; border: 1.5px solid #569cd6; border-radius: 50%; color: #569cd6; font-size: 0.7rem; font-weight: bold; font-style: italic; font-family: serif; opacity: 0.7; transition: opacity 0.2s; }
.workshop-content :deep(.tooltip-wrapper:hover .info-icon) { opacity: 1; }
.workshop-content :deep(.info-icon-inline) { display: inline-flex; align-items: center; justify-content: center; width: 16px; height: 16px; background: transparent; border: 1.5px solid #569cd6; border-radius: 50%; color: #569cd6; font-size: 0.65rem; font-weight: bold; font-style: italic; font-family: serif; margin: 0 2px; vertical-align: middle; }
.workshop-content :deep(.play-btn) { width: 28px; height: 28px; min-width: 28px; background: #1e7e34; color: white; border: none; border-radius: 50%; cursor: pointer; font-size: 0.7rem; transition: all 0.2s; display: flex; align-items: center; justify-content: center; flex-shrink: 0; padding: 0; margin-top: 2px; }
.workshop-content :deep(.play-btn:hover) { background: #28a745; transform: scale(1.1); }
.workshop-content :deep(.play-btn:active) { transform: scale(0.95); }
.workshop-content :deep(.play-btn.hint-btn) { background: #b45309; }
.workshop-content :deep(.play-btn.hint-btn:hover) { background: #d97706; }
.workshop-content :deep(code) { background: #2d2d2d; padding: 0.2rem 0.4rem; border-radius: var(--radius-sm); color: #ce9178; font-size: 0.85rem; white-space: normal; overflow-wrap: anywhere; word-break: break-word; }
.workshop-content :deep(.alert) { padding: var(--spacing-4); border-radius: var(--radius-md); margin-bottom: var(--spacing-4); background: #094771; border-left: 3px solid #569cd6; }
.workshop-content :deep(.note) { margin-bottom: var(--spacing-4); color: #999; font-size: 0.85rem; }
.workshop-content :deep(.link) { color: #569cd6; text-decoration: none; }
.workshop-content :deep(.link:hover) { text-decoration: underline; }
.workshop-content :deep(.concept-box) { background: #1e3a5f; border-left: 3px solid #4fc3f7; border-radius: var(--radius-md); padding: var(--spacing-4); margin: var(--spacing-3) 0; }
.workshop-content :deep(.concept-box p) { margin: 0; font-size: 0.85rem; color: #b3d9f2; }
.workshop-content :deep(.concept-box pre) { background: #0d1f30; padding: var(--spacing-3); border-radius: var(--radius-sm); margin-top: var(--spacing-2); overflow-x: auto; font-size: 0.8rem; }
.workshop-content :deep(.concept-box pre code) { background: transparent; padding: 0; color: #9cdcfe; }
.workshop-content :deep(.concept-box.warning) { background: #3d2814; border-left-color: #f59e0b; }
.workshop-content :deep(.concept-box.warning p) { color: #fcd9a8; }
.workshop-content :deep(.concept-box.review) { background: rgba(59, 130, 246, 0.1); border-left-color: #3b82f6; }
.workshop-content :deep(.completion-banner) { margin-top: var(--spacing-6); padding: var(--spacing-4); background: #1e7e34; color: white; border-radius: var(--radius-md); text-align: center; font-weight: var(--font-weight-semibold); }
@media (max-width: 1024px) { .workshop-panel { min-width: 280px; } }
@media (max-width: 768px) { .main-container { flex-direction: column; } .workshop-panel { width: 100% !important; max-height: 40vh; } .workshop-panel-resize-handle { display: none; } }
</style>
