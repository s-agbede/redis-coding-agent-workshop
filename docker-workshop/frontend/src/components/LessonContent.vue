<template>
  <div class="lesson-content">
    <div @click="handleClick" v-html="withCopyButtons(withFileButtons(html, filePaths))"></div>
    <span class="copy-status" role="status">{{ copyStatus }}</span>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { copyCode, runCode, withCopyButtons, withFileButtons } from '../lessonContent'
import { getApiUrl } from '../utils/basePath'

const props = withDefaults(defineProps<{ html: string; filePaths?: string[]; terminalAvailable?: boolean }>(), { filePaths: () => [], terminalAvailable: true })
const emit = defineEmits<{
  (event: 'open-file', path: string): void
  (event: 'show-terminal'): void
}>()
const copyStatus = ref('')
let contentVersion = 0
let dispatching = false
watch(() => props.html, () => { copyStatus.value = ''; contentVersion++ })

async function handleClick(event: MouseEvent): Promise<void> {
  const target = event.target as HTMLElement
  const path = target.closest<HTMLButtonElement>('button[data-open-file]')?.dataset.openFile
  if (path && props.filePaths.includes(path)) {
    emit('open-file', path)
    return
  }
  const runButton = target.closest<HTMLButtonElement>('button[data-run-code]')
  if (runButton) {
    if (dispatching) return
    const code = runButton.parentElement?.querySelector('pre code')
    if (!code) return
    const error = runButton.parentElement?.querySelector<HTMLElement>('[data-run-error]')
    const status = runButton.parentElement?.querySelector<HTMLElement>('[data-run-status]')
    if (!props.terminalAvailable) {
      if (error) {
        error.textContent = 'Open the workbench using the link above to run code in Terminal.'
        error.hidden = false
      }
      return
    }
    const version = contentVersion
    dispatching = true
    runButton.disabled = true
    runButton.textContent = 'Sending…'
    if (error) error.hidden = true
    if (status) status.hidden = true
    emit('show-terminal')
    const result = await runCode(code.textContent || '', getApiUrl('/api/terminal/run'))
    dispatching = false
    if (version !== contentVersion) return
    runButton.disabled = false
    runButton.textContent = 'Run code'
    if (error) {
      error.textContent = result.ok ? '' : result.message
      error.hidden = result.ok
    }
    if (status) {
      status.textContent = result.ok ? result.message : ''
      status.hidden = !result.ok
    }
    return
  }
  const button = target.closest<HTMLButtonElement>('button[data-copy-code]')
  const code = button?.parentElement?.querySelector('pre code')
  if (!button || !code) return
  const version = contentVersion
  const result = await copyCode(code.textContent || '', navigator.clipboard)
  if (version !== contentVersion) return
  const error = button.parentElement?.querySelector<HTMLElement>('[data-copy-error]')
  if (error) {
    error.textContent = result.ok ? '' : result.message
    error.hidden = result.ok
  }
  copyStatus.value = result.ok ? 'Code copied to clipboard.' : ''
  button.textContent = result.ok ? 'Copied' : 'Retry copy'
}
</script>

<style scoped>
.lesson-content { min-width: 0; overflow-wrap: anywhere; }
.lesson-content :deep(p) { margin: 1rem 0 1.3rem; line-height: 1.7; }
.lesson-content :deep(h2) { margin-top: 2.2rem; margin-bottom: 1rem; }
.lesson-content :deep(details) { margin: 1.25rem 0; }
.lesson-content :deep(img) { display: block; max-width: 100%; height: auto; margin: 1rem auto; }
.lesson-content :deep(.lesson-table) { max-width: 100%; overflow-x: auto; margin: 1rem 0; }
.lesson-content :deep(.lesson-table:focus-visible) { outline: 2px solid #7aa2f7; outline-offset: 2px; }
.lesson-content :deep(table) { width: 100%; border-collapse: collapse; text-align: left; }
.lesson-content :deep(th), .lesson-content :deep(td) { border: 1px solid #718096; padding: .6rem .75rem; vertical-align: top; min-width: 8rem; }
.lesson-content :deep(th) { background: #1a1a2e; color: #fff; }
.lesson-content :deep(td code) { white-space: pre-wrap; overflow-wrap: anywhere; }
.lesson-content :deep(pre) { max-width: 100%; overflow-x: auto; }
.lesson-content :deep(.lesson-file) { display: inline; padding: 0; border: 0; background: transparent; color: #90cdf4; font: inherit; text-align: inherit; text-decoration: underline; text-underline-offset: .2em; cursor: pointer; }
.lesson-content :deep(.lesson-file:hover) { color: #bee3f8; }
.lesson-content :deep(.lesson-file:focus-visible) { outline: 2px solid #7aa2f7; outline-offset: 3px; border-radius: 2px; }
.lesson-content :deep(.lesson-file code) { color: inherit; }

.lesson-content :deep(.lesson-code) { position: relative; margin: 1rem 0; padding-top: 2.3rem; background: #1a1a2e; border-radius: 6px; }
.lesson-content :deep(.lesson-code pre) { margin-top: 0; }
.lesson-content :deep(code.language-text) { display: block; white-space: pre-wrap; overflow-wrap: anywhere; }
.lesson-content :deep([data-copy-code]), .lesson-content :deep([data-run-code]) { position: absolute; right: .5rem; top: .4rem; border: 1px solid #718096; border-radius: 4px; padding: .25rem .6rem; color: #e2e8f0; background: #2d3748; cursor: pointer; font: inherit; font-size: .8rem; }
.lesson-content :deep([data-run-code]) { border-color: #81e6d9; color: #b2f5ea; }
.lesson-content :deep([data-run-code]:disabled) { opacity: .6; cursor: wait; }
.lesson-content :deep([data-copy-error]:not([hidden])), .lesson-content :deep([data-run-error]:not([hidden])) { display: block; margin: .4rem .75rem; padding: .5rem; border: 1px solid #fc8181; color: #fed7d7; border-radius: 4px; }
.lesson-content :deep([data-run-status]:not([hidden])) { display: block; margin: .4rem .75rem; color: #b2f5ea; font-size: .85rem; }
.copy-status { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); }
</style>
