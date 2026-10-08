<template>
  <section class="code-editor" aria-label="Code editor">
    <div class="editor-header">
      <label for="workshop-file">File</label>
      <select id="workshop-file" :value="session.path" @change="selectFile">
        <option v-for="file in shownFiles" :key="file.path" :value="file.path">{{ file.path }}</option>
      </select>
      <label class="file-filter"><input v-model="allFiles" type="checkbox" /> All files</label>
      <span class="save-status" role="status">{{ session.loading ? 'Loading…' : session.saving ? 'Saving…' : session.dirty ? 'Unsaved changes' : 'Saved' }}</span>
      <button :disabled="!session.dirty || session.saving" @click="session.save()">Save</button>
      <button :disabled="!session.path || session.dirty || session.loading || session.saving" :title="session.dirty ? 'Save pending edits before reloading.' : 'Read changes made in the terminal or by your agent.'" @click="reloadFile">Reload file</button>
      <button :disabled="!session.path || session.loading" @click="jumpToExercise">Next exercise</button>
      <slot name="panel-actions" />
    </div>
    <p class="editor-help">Tab / Shift+Tab: indent · Ctrl/⌘+Z: undo · Esc then Tab: leave editor. Save pending edits before reloading. <span role="status">{{ editorMessage }}</span></p>
    <div v-if="error || session.error" class="editor-error" role="alert">
      {{ error || session.error }}
      <button v-if="error" @click="loadFiles">Retry</button>
    </div>
    <p v-if="loading" class="editor-message">Loading workspace…</p>
    <textarea v-else-if="session.path" ref="textarea" :value="session.content" :aria-label="`Contents of ${session.path}`"
      :disabled="session.loading" class="code-textarea" spellcheck="false" autocomplete="off"
      autocapitalize="off" @keydown="handleKey" @beforeinput="beforeInput" @input="inputText" />
    <p v-else class="editor-message">Select a file to edit.</p>
  </section>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave } from 'vue-router'
import { EditorSession, type FileDocument } from '../editorSession'
import { getApiUrl } from '../utils/basePath'
import { enterText, indentText, nextExercise, TextHistory, visibleFiles, type TextState } from '../editorText'

const props = withDefaults(defineProps<{ selectedFile?: string; language?: string }>(), {
  selectedFile: 'first_call.py', language: 'python'
})
const emit = defineEmits<{
  (event: 'file-change', path: string): void
  (event: 'files-loaded', paths: string[]): void
}>()
const files = ref<Array<{ name: string; path: string; language: string }>>([])
const error = ref('')
const loading = ref(true)
const allFiles = ref(false)
const textarea = ref<HTMLTextAreaElement | null>(null)
const editorMessage = ref('')
let filesReady = false
let leaveEditor = false
let history = new TextHistory({ content: '', start: 0, end: 0 })

async function request(url: string, init?: RequestInit): Promise<Response> {
  const response = await fetch(getApiUrl(url), init)
  if (!response.ok) {
    throw new Error(`Could not ${init?.method === 'POST' ? 'save' : 'read'} file (${response.status}). Your pending edits are kept here; retry when the workspace is available.`)
  }
  return response
}

const session = reactive(new EditorSession({
  async read(path: string): Promise<FileDocument> {
    const response = await request(`/api/editor/file?path=${encodeURIComponent(path)}`)
    return response.json()
  },
  async write(path: string, content: string): Promise<void> {
    await request('/api/editor/file', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ path, content })
    })
  }
}))
const shownFiles = computed(() => visibleFiles(files.value, allFiles.value, session.path))

async function loadFiles(): Promise<void> {
  loading.value = true
  error.value = ''
  try {
    files.value = await (await request('/api/editor/files')).json()
    emit('files-loaded', files.value.map(file => file.path))
    filesReady = true
    const path = props.selectedFile || files.value[0]?.path
    if (path) await openFile(path)
  } catch (cause) {
    error.value = cause instanceof Error ? cause.message : String(cause)
  } finally {
    loading.value = false
  }
}

async function selectFile(event: Event): Promise<void> {
  const select = event.target as HTMLSelectElement
  await openFile(select.value)
  select.value = session.path
}

async function openFile(path: string, focus = false): Promise<void> {
  const opened = await session.open(path)
  // Keep lesson buttons in sync with manual selection and failed switches.
  emit('file-change', session.path)
  if (opened && focus) {
    await nextTick()
    textarea.value?.focus({ preventScroll: true })
    textarea.value?.scrollIntoView({ block: 'nearest' })
  }
}

defineExpose({ openFile })

async function reloadFile(): Promise<void> {
  if (await session.reload()) {
    history = new TextHistory({ content: session.content, start: 0, end: 0 })
    editorMessage.value = 'File reloaded from the workspace.'
  }
}

function fieldState(field: HTMLTextAreaElement): TextState {
  return { content: field.value, start: field.selectionStart, end: field.selectionEnd }
}

function applyText(state: TextState): void {
  session.content = state.content
  void nextTick(() => {
    textarea.value?.focus()
    textarea.value?.setSelectionRange(state.start, state.end)
  })
}

function beforeInput(event: InputEvent): void {
  if (event.inputType === 'historyUndo' || event.inputType === 'historyRedo') {
    event.preventDefault()
    const state = event.inputType === 'historyUndo' ? history.undo() : history.redo()
    if (state) applyText(state)
  } else history.record(fieldState(event.target as HTMLTextAreaElement))
}

function inputText(event: Event): void {
  const state = fieldState(event.target as HTMLTextAreaElement)
  session.content = state.content
  history.record(state)
}

function jumpToExercise(): void {
  if (!textarea.value) return
  const state = nextExercise(fieldState(textarea.value))
  editorMessage.value = state ? '' : 'No exercise markers in this file.'
  if (state) {
    applyText(state)
    const line = state.content.slice(0, state.start).split('\n').length - 1
    const lineHeight = parseFloat(getComputedStyle(textarea.value).lineHeight)
    textarea.value.scrollTop = Math.max(0, line * lineHeight - textarea.value.clientHeight / 2)
  }
}

function handleKey(event: KeyboardEvent): void {
  if (event.isComposing) return
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
    event.preventDefault()
    void session.save()
    return
  }
  if ((event.ctrlKey || event.metaKey) && ['z', 'y'].includes(event.key.toLowerCase())) {
    event.preventDefault()
    const state = event.shiftKey || event.key.toLowerCase() === 'y' ? history.redo() : history.undo()
    if (state) applyText(state)
    return
  }
  if (event.key === 'Escape') { leaveEditor = true; return }
  if (event.key === 'Tab' && leaveEditor) { leaveEditor = false; return }
  leaveEditor = false
  if (event.key === 'Tab' || event.key === 'Enter') {
    event.preventDefault()
    const before = fieldState(event.target as HTMLTextAreaElement)
    const after = event.key === 'Tab' ? indentText(before, event.shiftKey) : enterText(before)
    history.record(before)
    history.record(after)
    applyText(after)
  }
}

function guardClose(event: BeforeUnloadEvent): void {
  if (session.dirty || session.saving) {
    event.preventDefault()
    event.returnValue = ''
  }
}

watch(() => props.selectedFile, path => { if (path && filesReady) void openFile(path) })
watch(() => session.path, () => {
  history = new TextHistory({ content: session.content, start: 0, end: 0 })
  editorMessage.value = ''
})
onBeforeRouteLeave(async () => (await session.save()) && !session.dirty)
onMounted(() => { void loadFiles(); window.addEventListener('beforeunload', guardClose) })
onBeforeUnmount(() => window.removeEventListener('beforeunload', guardClose))
</script>

<style scoped>
.code-editor { display: flex; flex-direction: column; height: 100%; background: #1e2030; min-height: 0; }
.editor-header { display: flex; align-items: center; gap: .65rem; padding: .65rem; background: #161824; flex-wrap: wrap; }
.editor-header label, .save-status { font-size: .75rem; color: #c0caf5; }
select { flex: 1; min-width: 120px; max-width: 100%; background: #2d3748; color: #e2e8f0; padding: .4rem; border: 1px solid #4a5568; border-radius: 4px; }
button { border: 1px solid #718096; border-radius: 4px; padding: .35rem .7rem; color: #fff; background: #2d3748; cursor: pointer; }
button:disabled { opacity: .45; cursor: default; }
.editor-error { padding: .6rem; background: #702b30; color: #fff; font-size: .85rem; }
.editor-message { padding: 1rem; }
.editor-help { margin: 0; padding: .35rem .65rem; font-size: .7rem; color: #a0aec0; }
.file-filter { display: flex; gap: .3rem; align-items: center; white-space: nowrap; }
.code-textarea { flex: 1; min-height: 0; width: 100%; padding: 1rem; background: #1e2030; color: #c0caf5; border: 0; resize: none; font: 13px/1.65 ui-monospace, SFMono-Regular, Consolas, monospace; tab-size: 4; white-space: pre; }
.code-textarea:focus { outline: 2px solid #7aa2f7; outline-offset: -2px; }
</style>
