<template>
  <div class="editor-container">
    <div class="file-tabs">
      <button
        v-for="file in files"
        :key="file"
        :class="['file-tab', { active: currentFile === file }]"
        @click="selectFile(file)"
      >
        {{ file }}
      </button>
    </div>

    <div class="editor-panel">
      <div class="editor-header">
        <h3>{{ currentFile || 'Select a file to edit' }}</h3>
        <div v-if="isCheckingDiagnostics" class="editor-diagnostics-summary editor-diagnostics-summary--checking">
          Checking code...
        </div>
        <div v-else-if="activeDiagnostics.length" class="editor-diagnostics-summary">
          {{ activeDiagnostics.length }} issue{{ activeDiagnostics.length === 1 ? '' : 's' }}
        </div>
        <div class="editor-actions">
          <button @click="checkDiagnostics" class="btn btn-secondary" :disabled="!currentFile || isCheckingDiagnostics">
            {{ isCheckingDiagnostics ? 'Checking...' : 'Check Code' }}
          </button>
          <button @click="save" class="btn btn-primary" :disabled="!currentFile">Save Changes</button>
          <button @click="reload" class="btn btn-secondary" :disabled="!currentFile">Reload</button>
        </div>
      </div>
      <div class="code-editor-wrapper">
        <div class="editor-container-inner" :style="editorMetricsStyle">
          <div class="code-line-numbers" aria-hidden="true">
            <div class="code-line-numbers__content" :style="lineHighlightsContentStyle">
              <div
                v-for="lineNumber in lineNumbers"
                :key="`line-number-${lineNumber}`"
                class="code-line-number"
                :class="lineNumberClass(lineNumber)"
                :style="lineNumberStyle(lineNumber)"
              >
                <span
                  class="code-line-number__marker"
                  :class="lineMarkerClass(lineNumber)"
                >
                  {{ lineMarkerSymbol(lineNumber) }}
                </span>
                <span class="code-line-number__value">{{ lineNumber }}</span>
              </div>
            </div>
          </div>
          <div class="code-line-highlights">
            <div class="code-line-highlights__content" :style="lineHighlightsContentStyle">
              <div
                v-for="diagnostic in activeDiagnostics"
                :key="diagnostic.id"
                class="code-line-highlight"
                :class="`code-line-highlight--${diagnostic.severity}`"
                :style="lineHighlightStyle(diagnostic.line)"
              ></div>
            </div>
          </div>
          <pre class="code-highlight"><code :class="languageClass" v-html="highlightedCode"></code></pre>
          <textarea
            ref="codeTextarea"
            v-model="content"
            class="code-editor"
            :disabled="!currentFile"
            wrap="off"
            spellcheck="false"
            @scroll="syncScroll"
          ></textarea>
        </div>
      </div>
      <div v-if="activeDiagnostics.length" class="editor-diagnostics-panel">
        <button
          v-for="diagnostic in activeDiagnostics"
          :key="`${diagnostic.id}-panel`"
          type="button"
          class="editor-diagnostic-item"
          :class="`editor-diagnostic-item--${diagnostic.severity}`"
          @click="focusDiagnostic(diagnostic)"
        >
          <span class="editor-diagnostic-item__line">Line {{ diagnostic.line }}</span>
          <span class="editor-diagnostic-item__message">{{ diagnostic.message }}</span>
        </button>
      </div>
      <div v-if="statusMessage" :class="['status-message', statusType]">
        {{ statusMessage }}
      </div>
    </div>
  </div>
</template>

<script>
import { getBasePath } from '../utils/basePath.js';
import hljs from 'highlight.js/lib/core';
import java from 'highlight.js/lib/languages/java';
import kotlin from 'highlight.js/lib/languages/kotlin';
import properties from 'highlight.js/lib/languages/properties';

// Register languages
hljs.registerLanguage('java', java);
hljs.registerLanguage('kotlin', kotlin);
hljs.registerLanguage('properties', properties);

export default {
  name: 'CodeEditor',
  data() {
    return {
      currentFile: null,
      content: '',
      fileLanguage: '',
      statusMessage: '',
      statusType: '',
      scrollTop: 0,
      serverDiagnostics: [],
      isCheckingDiagnostics: false,
      editorLineHeight: 21,
      editorPaddingTop: 16
    };
  },
  props: {
    files: {
      type: Array,
      required: true
    },
    diagnostics: {
      type: Array,
      default: () => []
    },
    initialFile: {
      type: String,
      default: null
    }
  },
  emits: ['file-loaded', 'file-saved', 'status', 'content-changed'],
  computed: {
    basePath() {
      return getBasePath();
    },
    editorMetricsStyle() {
      return {
        '--editor-line-height': `${this.editorLineHeight}px`,
        '--editor-padding-top': `${this.editorPaddingTop}px`
      };
    },
    lineHighlightsContentStyle() {
      return {
        transform: `translateY(${-this.scrollTop}px)`
      };
    },
    lineNumbers() {
      const lineCount = Math.max(1, this.content.split('\n').length);
      return Array.from({ length: lineCount }, (_, index) => index + 1);
    },
    allDiagnostics() {
      return [...(this.diagnostics || []), ...this.serverDiagnostics];
    },
    activeDiagnostics() {
      return this.allDiagnostics
        .filter(diagnostic => diagnostic.file === this.currentFile)
        .slice()
        .sort((left, right) => left.line - right.line);
    },
    activeDiagnosticsByLine() {
      return this.activeDiagnostics.reduce((accumulator, diagnostic) => {
        const current = accumulator[diagnostic.line];
        if (!current || (current.severity === 'warning' && diagnostic.severity === 'error')) {
          accumulator[diagnostic.line] = diagnostic;
        }
        return accumulator;
      }, {});
    },
    languageClass() {
      const langMap = {
        java: 'language-java',
        kotlin: 'language-kotlin',
        properties: 'language-properties'
      };
      return langMap[this.fileLanguage] || '';
    },
    highlightedCode() {
      if (!this.content) return '';
      try {
        if (this.fileLanguage && hljs.getLanguage(this.fileLanguage)) {
          return hljs.highlight(this.content, { language: this.fileLanguage }).value;
        }
        return this.escapeHtml(this.content);
      } catch {
        return this.escapeHtml(this.content);
      }
    }
  },
  mounted() {
    if (this.initialFile && this.files.includes(this.initialFile)) {
      this.loadFile(this.initialFile);
    }
    this.$nextTick(() => {
      this.measureEditorMetrics();
      window.addEventListener('resize', this.measureEditorMetrics);
    });
  },
  beforeUnmount() {
    window.removeEventListener('resize', this.measureEditorMetrics);
  },
  watch: {
    content() {
      this.$emit('content-changed', {
        fileName: this.currentFile,
        content: this.content
      });
      this.$nextTick(() => {
        this.measureEditorMetrics();
      });
    }
  },
  methods: {
    escapeHtml(text) {
      const div = document.createElement('div');
      div.textContent = text;
      return div.innerHTML;
    },
    syncScroll() {
      const textarea = this.$refs.codeTextarea;
      const pre = textarea?.parentElement?.querySelector('.code-highlight');
      this.scrollTop = textarea?.scrollTop || 0;
      if (pre) {
        pre.scrollTop = textarea.scrollTop;
        pre.scrollLeft = textarea.scrollLeft;
      }
    },
    getLanguageFromFile(fileName) {
      if (fileName.endsWith('.java')) return 'java';
      if (fileName.endsWith('.kts') || fileName.endsWith('.kt')) return 'kotlin';
      if (fileName.endsWith('.properties')) return 'properties';
      return '';
    },
    async selectFile(fileName) {
      await this.loadFile(fileName);
    },
    async loadFile(fileName) {
      try {
        const url = `${this.basePath}/api/editor/file/${fileName}`;
        const response = await fetch(url, { credentials: 'include' });
        const responseText = await response.text();

        let data;
        try {
          data = JSON.parse(responseText);
        } catch {
          this.showStatus('Server returned invalid response (not JSON)', 'error');
          return;
        }

        if (data.error) {
          this.showStatus(data.error, 'error');
          return;
        }

        this.currentFile = fileName;
        this.content = data.content;
        this.fileLanguage = data.language || this.getLanguageFromFile(fileName);
        this.showStatus('File loaded successfully', 'success');
        this.$emit('file-loaded', { fileName, content: this.content });
        this.$nextTick(() => {
          this.measureEditorMetrics();
        });
      } catch (error) {
        this.showStatus(`Failed to load file: ${error.message}`, 'error');
      }
    },
    measureEditorMetrics() {
      const textarea = this.$refs.codeTextarea;
      const highlightLayer = this.$el?.querySelector('.code-highlight');
      const referenceElement = highlightLayer || textarea;

      if (!referenceElement) {
        return;
      }

      const computedStyle = window.getComputedStyle(referenceElement);
      const lineHeight = Number.parseFloat(computedStyle.lineHeight);
      const paddingTop = Number.parseFloat(computedStyle.paddingTop);
      const paddingBottom = Number.parseFloat(computedStyle.paddingBottom);
      const lineCount = Math.max(1, this.content.split('\n').length);
      const renderedContentHeight = highlightLayer
        ? highlightLayer.scrollHeight - paddingTop - (Number.isNaN(paddingBottom) ? 0 : paddingBottom)
        : Number.NaN;
      const renderedLineHeight = renderedContentHeight > 0
        ? (renderedContentHeight / lineCount) + 0.235
        : Number.NaN;

      if (!Number.isNaN(renderedLineHeight) && renderedLineHeight > 0) {
        this.editorLineHeight = renderedLineHeight;
      } else if (!Number.isNaN(lineHeight) && lineHeight > 0) {
        this.editorLineHeight = lineHeight;
      }

      if (!Number.isNaN(paddingTop) && paddingTop >= 0) {
        this.editorPaddingTop = paddingTop;
      }
    },
    async save() {
      if (!this.currentFile) return;

      try {
        const response = await fetch(`${this.basePath}/api/editor/file/${this.currentFile}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content: this.content }),
          credentials: 'include'
        });

        const data = await response.json();

        if (data.error) {
          this.showStatus(data.error, 'error');
        } else {
          this.showStatus('File saved! Checking for compiler errors...', 'success');
          this.$emit('file-saved', { fileName: this.currentFile, content: this.content });
          await this.checkDiagnostics(false, true);
        }
      } catch (error) {
        this.showStatus(`Failed to save file: ${error.message}`, 'error');
      }
    },
    async checkDiagnostics(showStatus = true, skipOverride = false) {
      if (!this.currentFile || this.isCheckingDiagnostics) {
        return;
      }

      this.isCheckingDiagnostics = true;

      try {
        const response = await fetch(`${this.basePath}/api/editor/diagnostics`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            overrides: skipOverride
              ? []
              : [
                {
                  fileName: this.currentFile,
                  content: this.content
                }
              ]
          }),
          credentials: 'include'
        });

        const data = await response.json();
        if (data.error) {
          this.serverDiagnostics = [];
          this.showStatus(data.error, 'error');
          return;
        }

        this.serverDiagnostics = Array.isArray(data.diagnostics) ? data.diagnostics : [];

        if (showStatus) {
          if (this.serverDiagnostics.length) {
            this.showStatus(
              `${this.serverDiagnostics.length} compiler issue${this.serverDiagnostics.length === 1 ? '' : 's'} found.`,
              'error'
            );
          } else {
            this.showStatus('No compiler errors found.', 'success');
          }
        }
      } catch (error) {
        this.serverDiagnostics = [];
        this.showStatus(`Failed to check code: ${error.message}`, 'error');
      } finally {
        this.isCheckingDiagnostics = false;
      }
    },
    reload() {
      if (this.currentFile) {
        this.loadFile(this.currentFile);
      }
    },
    showStatus(message, type) {
      this.statusMessage = message;
      this.statusType = type;
      this.$emit('status', { message, type });
      setTimeout(() => {
        this.statusMessage = '';
        this.statusType = '';
      }, 3000);
    },
    updateContent(newContent) {
      this.content = newContent;
    },
    focusDiagnostic(diagnostic) {
      const textarea = this.$refs.codeTextarea;
      if (!textarea) {
        return;
      }

      const lineNumber = Math.max(1, diagnostic.line || 1);
      const offset = this.lineStartOffset(lineNumber);
      const lineHeight = this.editorLineHeight;
      const paddingTop = this.editorPaddingTop;

      textarea.focus();
      textarea.setSelectionRange(offset, offset);
      textarea.scrollTop = Math.max(0, paddingTop + ((lineNumber - 1) * lineHeight) - (textarea.clientHeight / 3));
      this.syncScroll();
    },
    getCurrentContent() {
      return this.content;
    },
    getCurrentFile() {
      return this.currentFile;
    },
    lineMarkerClass(lineNumber) {
      const diagnostic = this.activeDiagnosticsByLine[lineNumber];
      return diagnostic ? `code-line-number__marker--${diagnostic.severity}` : '';
    },
    lineMarkerSymbol(lineNumber) {
      const diagnostic = this.activeDiagnosticsByLine[lineNumber];
      if (!diagnostic) {
        return '';
      }
      return diagnostic.severity === 'error' ? 'X' : '!';
    },
    lineNumberClass(lineNumber) {
      const diagnostic = this.activeDiagnosticsByLine[lineNumber];
      return diagnostic ? `code-line-number--${diagnostic.severity}` : '';
    },
    lineNumberStyle(lineNumber) {
      return this.lineHighlightStyle(lineNumber);
    },
    lineHighlightStyle(lineNumber) {
      const normalizedLine = Math.max(1, lineNumber || 1);
      const lineHeight = this.editorLineHeight;
      const paddingTop = this.editorPaddingTop;

      return {
        top: `${paddingTop + ((normalizedLine - 1) * lineHeight)}px`,
        height: `${lineHeight}px`
      };
    },
    lineStartOffset(lineNumber) {
      if (lineNumber <= 1) {
        return 0;
      }

      const lines = this.content.split('\n');
      let offset = 0;
      for (let index = 0; index < lineNumber - 1 && index < lines.length; index += 1) {
        offset += lines[index].length + 1;
      }
      return offset;
    }
  }
};
</script>

<style scoped>
.editor-container { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.file-tabs { display: flex; background: #252526; border-bottom: 1px solid var(--color-border); overflow-x: auto; }
.file-tab { padding: var(--spacing-3) var(--spacing-6); background: transparent; border: none; color: #969696; cursor: pointer; transition: all var(--transition-base); border-right: 1px solid var(--color-border); white-space: nowrap; font-size: var(--font-size-sm); }
.file-tab:hover { background: #2a2d2e; color: #cccccc; }
.file-tab.active { background: #1e1e1e; color: #ffffff; border-bottom: 2px solid #DC382C; }
.editor-panel { flex: 1; min-width: 0; display: flex; flex-direction: column; }
.editor-header { background: #252526; padding: var(--spacing-3) var(--spacing-4); display: flex; justify-content: space-between; align-items: center; gap: var(--spacing-3); border-bottom: 1px solid var(--color-border); }
.editor-header h3 { color: #cccccc; margin: 0; font-size: var(--font-size-sm); min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.editor-diagnostics-summary { color: #fbbf24; font-size: var(--font-size-xs); font-weight: var(--font-weight-semibold); letter-spacing: 0.02em; text-transform: uppercase; }
.editor-diagnostics-summary--checking { color: #93c5fd; }
.editor-actions { display: flex; gap: var(--spacing-2); }
.editor-actions button { padding: var(--spacing-2) var(--spacing-4); font-size: var(--font-size-sm); }
.code-editor-wrapper { flex: 1; width: 100%; min-width: 0; height: 100%; overflow: hidden; }
.editor-container-inner { position: relative; width: 100%; min-width: 0; height: 100%; overflow: hidden; }
.code-line-numbers { position: absolute; inset: 0 auto 0 0; width: 3.5rem; background: #181818; border-right: 1px solid rgba(255, 255, 255, 0.06); pointer-events: none; z-index: 2; overflow: hidden; }
.code-line-numbers__content { position: relative; width: 100%; height: 100%; }
.code-line-number { position: absolute; left: 0; right: 0; height: var(--editor-line-height, 21px); padding: 0.1rem 0.75rem 0 1.3rem; color: #6b7280; font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 13px; line-height: var(--editor-line-height, 15px); text-align: right; user-select: none; }
.code-line-number--warning .code-line-number__value { color: #fbbf24; }
.code-line-number--error .code-line-number__value { color: #fca5a5; }
.code-line-number__marker { position: absolute; left: 0.35rem; top: 50%; display: inline-flex; align-items: center; justify-content: center; width: 0.95rem; min-width: 0.95rem; height: 0.95rem; border-radius: 999px; font-size: 0.62rem; font-weight: 700; line-height: 1; opacity: 0; transform: translateY(-50%); }
.code-line-number__marker--warning { opacity: 1; background: rgba(245, 158, 11, 0.18); color: #fbbf24; }
.code-line-number__marker--error { opacity: 1; background: rgba(239, 68, 68, 0.18); color: #fca5a5; }
.code-line-number__value { display: block; min-width: 1.6rem; }
.code-line-highlights { position: absolute; inset: 0 0 0 3.5rem; pointer-events: none; z-index: 0; }
.code-line-highlights__content { position: relative; width: 100%; height: 100%; }
.code-line-highlight { position: absolute; left: 0; right: 0; }
.code-line-highlight::after { content: ''; position: absolute; left: 0; right: 0; bottom: 2px; height: 2px; opacity: 0.95; background-repeat: repeat-x; background-size: 10px 2px; }
.code-line-highlight--warning { background: rgba(245, 158, 11, 0.14); box-shadow: inset 3px 0 0 rgba(245, 158, 11, 0.7); }
.code-line-highlight--warning::after { background-image: repeating-linear-gradient(90deg, rgba(245, 158, 11, 0.95) 0 6px, rgba(245, 158, 11, 0) 6px 10px); }
.code-line-highlight--error { background: rgba(239, 68, 68, 0.12); box-shadow: inset 3px 0 0 rgba(239, 68, 68, 0.7); }
.code-line-highlight--error::after { background-image: repeating-linear-gradient(90deg, rgba(239, 68, 68, 0.95) 0 6px, rgba(239, 68, 68, 0) 6px 10px); }
.code-highlight { position: absolute; inset: 0; margin: 0; padding: var(--spacing-4) var(--spacing-4) var(--spacing-4) calc(3.5rem + var(--spacing-4)); background: #1e1e1e; font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 14px; line-height: 1.5; overflow: auto; pointer-events: none; white-space: pre; color: #d4d4d4; }
.code-highlight code { display: block; min-width: max-content; font-family: inherit; font-size: inherit; line-height: inherit; white-space: inherit; word-break: normal; overflow-wrap: normal; background: transparent; padding: 0; }
.code-editor { position: absolute; inset: 0; width: 100%; height: 100%; background: transparent; color: transparent; caret-color: #fff; border: none; padding: var(--spacing-4) var(--spacing-4) var(--spacing-4) calc(3.5rem + var(--spacing-4)); font-family: 'Consolas', 'Monaco', 'Courier New', monospace; font-size: 14px; line-height: 1.5; white-space: pre; overflow: auto; resize: none; z-index: 1; }
.code-editor:focus { outline: none; }
.code-editor:disabled { opacity: 0.5; cursor: not-allowed; }
.editor-diagnostics-panel { display: flex; flex-direction: column; gap: 0.5rem; padding: 0.75rem 1rem; border-top: 1px solid var(--color-border); background: #15181b; max-height: 10rem; overflow-y: auto; }
.editor-diagnostic-item { display: flex; gap: 0.75rem; align-items: flex-start; width: 100%; padding: 0.55rem 0.7rem; border: 1px solid transparent; border-radius: 6px; background: #1b1f23; color: #d1d5db; text-align: left; cursor: pointer; }
.editor-diagnostic-item--warning { border-color: rgba(245, 158, 11, 0.35); }
.editor-diagnostic-item--error { border-color: rgba(239, 68, 68, 0.35); }
.editor-diagnostic-item__line { min-width: 4rem; color: #9ca3af; font-size: var(--font-size-xs); text-transform: uppercase; letter-spacing: 0.03em; }
.editor-diagnostic-item__message { font-size: var(--font-size-sm); line-height: 1.4; }
.status-message { position: fixed; bottom: 20px; right: 20px; padding: var(--spacing-4) var(--spacing-6); background: #252526; color: #fff; text-align: center; font-size: var(--font-size-sm); border-radius: var(--radius-md); box-shadow: var(--shadow-xl); z-index: 1000; transition: opacity var(--transition-base); }
.status-message.success { background: #1e7e34; }
.status-message.error { background: #bd2130; }
.btn { padding: var(--spacing-2) var(--spacing-4); border: none; border-radius: var(--radius-md); font-size: var(--font-size-sm); font-weight: var(--font-weight-semibold); cursor: pointer; transition: all var(--transition-base); }
.btn-primary { background: #DC382C; color: white; }
.btn-primary:hover:not(:disabled) { background: #c42f24; }
.btn-secondary { background: var(--color-dark-800); color: var(--color-text); border: 1px solid var(--color-border); }
.btn-secondary:hover:not(:disabled) { background: var(--color-border); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.code-highlight :deep(.hljs-keyword) { color: #569cd6; }
.code-highlight :deep(.hljs-built_in) { color: #4ec9b0; }
.code-highlight :deep(.hljs-type) { color: #4ec9b0; }
.code-highlight :deep(.hljs-literal) { color: #569cd6; }
.code-highlight :deep(.hljs-number) { color: #b5cea8; }
.code-highlight :deep(.hljs-string) { color: #ce9178; }
.code-highlight :deep(.hljs-comment) { color: #6a9955; }
.code-highlight :deep(.hljs-class) { color: #4ec9b0; }
.code-highlight :deep(.hljs-function) { color: #dcdcaa; }
.code-highlight :deep(.hljs-title) { color: #dcdcaa; }
.code-highlight :deep(.hljs-title.function_) { color: #dcdcaa; }
.code-highlight :deep(.hljs-title.class_) { color: #4ec9b0; }
.code-highlight :deep(.hljs-params) { color: #9cdcfe; }
.code-highlight :deep(.hljs-variable) { color: #9cdcfe; }
.code-highlight :deep(.hljs-attr) { color: #9cdcfe; }
.code-highlight :deep(.hljs-property) { color: #9cdcfe; }
.code-highlight :deep(.hljs-punctuation) { color: #d4d4d4; }
.code-highlight :deep(.hljs-operator) { color: #d4d4d4; }
.code-highlight :deep(.hljs-meta) { color: #c586c0; }
.code-highlight :deep(.hljs-decorator) { color: #c586c0; }
.code-highlight :deep(.hljs-annotation) { color: #c586c0; }
</style>
