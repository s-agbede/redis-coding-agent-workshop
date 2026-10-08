<template>
  <section class="build-panel" :class="{ 'build-panel--expanded': expandedPanel }" aria-label="Student workspace">
    <div class="editor-section" :hidden="!!expandedPanel && expandedPanel !== 'editor'" :style="{ flexBasis: `${editorPercent}%` }">
      <CodeEditor ref="editor" :selected-file="selectedFile" :language="language" @file-change="emit('file-change', $event)" @files-loaded="emit('files-loaded', $event)">
        <template #panel-actions>
          <PanelToggle label="code editor" :expanded="expandedPanel === 'editor'" @toggle="emit('expand', expandedPanel === 'editor' ? null : 'editor')" />
        </template>
      </CodeEditor>
    </div>
    <PanelDivider v-model:value="editorPercent" :hidden="!!expandedPanel" orientation="horizontal" label="Resize editor and runtime" />
    <div class="runtime-tabs" :hidden="expandedPanel === 'editor'">
      <div role="tablist" aria-label="Runtime panels">
        <button id="terminal-tab" role="tab" :aria-selected="activeTab === 'terminal'" aria-controls="terminal-panel" @click="selectTab('terminal')">Terminal</button>
        <button id="preview-tab" role="tab" :aria-selected="activeTab === 'preview'" aria-controls="preview-panel" @click="selectTab('preview')">App Preview</button>
      </div>
      <PanelToggle :label="activeTab === 'terminal' ? 'terminal' : 'app preview'" :expanded="expandedPanel === activeTab" @toggle="emit('expand', expandedPanel === activeTab ? null : activeTab)" />
    </div>
    <div id="terminal-panel" :hidden="activeTab !== 'terminal' || expandedPanel === 'editor'" class="runtime-section" role="tabpanel" aria-labelledby="terminal-tab">
      <iframe :src="terminalUrl" title="Python workshop terminal" allow="clipboard-read; clipboard-write" />
    </div>
    <div id="preview-panel" :hidden="activeTab !== 'preview' || expandedPanel === 'editor'" class="runtime-section" role="tabpanel" aria-labelledby="preview-tab">
      <AppEmbed v-if="previewOpened" :url="appUrl" :title="appTitle" />
    </div>
  </section>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import CodeEditor from './CodeEditor.vue'
import AppEmbed from './AppEmbed.vue'
import PanelToggle from './PanelToggle.vue'
import PanelDivider from './PanelDivider.vue'
import { getApiUrl } from '../utils/basePath'

type RuntimeTab = 'terminal' | 'preview'
type ExpandedPanel = 'instructions' | 'editor' | RuntimeTab | null
const props = withDefaults(defineProps<{ selectedFile?: string; language?: string; appUrl?: string; appTitle?: string; defaultEditorPercent?: number; expandedPanel?: ExpandedPanel }>(), {
  selectedFile: 'first_call.py', language: 'python', appUrl: '/app/', appTitle: 'Task-list app', defaultEditorPercent: 55, expandedPanel: null
})
const activeTab = ref<RuntimeTab>('terminal')
const emit = defineEmits<{
  (event: 'file-change', path: string): void
  (event: 'expand', panel: ExpandedPanel): void
  (event: 'files-loaded', paths: string[]): void
}>()
const editor = ref<{ openFile(path: string, focus: boolean): Promise<void> } | null>(null)
defineExpose({
  openFile: (path: string) => editor.value?.openFile(path, true),
  showTerminal: () => { activeTab.value = 'terminal' }
})
const previewOpened = ref(false)
const editorPercent = ref(Math.max(20, Math.min(80, props.defaultEditorPercent)))
watch(() => props.defaultEditorPercent, value => { editorPercent.value = Math.max(20, Math.min(80, value)) })
const terminalUrl = getApiUrl('/terminal/')

function selectTab(tab: RuntimeTab): void {
  activeTab.value = tab
  if (tab === 'preview') previewOpened.value = true
  if (props.expandedPanel) emit('expand', tab)
}
</script>

<style scoped>
.build-panel { display: flex; flex-direction: column; height: 100%; min-height: 0; background: #1a1a2e; }
.build-panel [hidden] { display: none !important; }
.editor-section { flex: 0 1 55%; min-height: 160px; overflow: hidden; }
.runtime-tabs { display: flex; align-items: center; justify-content: space-between; gap: .5rem; padding: .45rem .65rem; background: #161824; }
.runtime-tabs [role="tablist"] { display: flex; gap: .5rem; }
.runtime-tabs [role="tab"] { color: #a0aec0; background: transparent; border: 1px solid transparent; border-radius: 4px; padding: .4rem .8rem; cursor: pointer; }
.runtime-tabs button[aria-selected="true"] { color: #fff; border-color: #7aa2f7; background: #2d3748; }
.runtime-section { flex: 1; min-height: 100px; }
.build-panel--expanded .editor-section { flex: 1; min-height: 0; }
.build-panel--expanded .runtime-section { min-height: 0; }
iframe { display: block; width: 100%; height: 100%; border: 0; }
</style>
