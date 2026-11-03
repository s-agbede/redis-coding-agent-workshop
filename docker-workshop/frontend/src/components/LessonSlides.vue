<template>
  <section ref="frame" class="lesson-slides" :class="{ 'is-focused': focused }" :role="focused ? 'dialog' : 'region'" :aria-modal="focused ? 'true' : undefined" aria-label="Lesson introduction" tabindex="-1" @keydown="handleKeys">
    <div class="slide-toolbar">
      <div class="slide-modes" aria-label="Introduction view">
        <button type="button" :aria-pressed="!readMode" @click="readMode = false">Guided slides</button>
        <button type="button" :aria-pressed="readMode" @click="readMode = true">Read text</button>
      </div>
      <div class="slide-modes">
        <a class="download" :href="deckUrl" :download="deckFile">Download slides (PDF)</a>
        <button ref="focusButton" type="button" :aria-pressed="focused" @click="toggleFocus">{{ focused ? 'Exit focus' : 'Focus mode' }}</button>
      </div>
    </div>
    <p v-if="loading" role="status">Loading introduction…</p>
    <div v-else-if="error" role="alert">
      <p>Could not load slides. Exercises below remain available.</p>
      <button type="button" @click="load">Retry slides</button>
    </div>
    <template v-else>
      <div v-if="readMode" class="slide-text">
        <article v-for="(slide, number) in slides" :key="number" class="slide-body" v-html="render(slide)"></article>
      </div>
      <article v-else class="slide-body slide-card" :aria-label="`Slide ${index + 1} of ${slides.length}`" v-html="render(slides[index] || '')"></article>
      <nav v-if="!readMode" class="slide-navigation" aria-label="Slide navigation">
        <button type="button" :disabled="index === 0" @click="move(-1)">Previous</button>
        <span role="status" aria-live="polite">{{ index + 1 }} / {{ slides.length }}</span>
        <button type="button" :disabled="index === slides.length - 1" @click="move(1)">Next</button>
      </nav>
      <p v-if="focused" class="focus-hint">Press Escape to return to the exercise.</p>
    </template>
  </section>
</template>

<script>
import { splitSlides } from '../utils/slides'
import { markdownToHtml } from '../utils/markdown'
import { getBasePath } from '../utils/basePath'

const DECK_FILE = 'agent-memory-workshop-slides.pdf'

export default {
  props: { src: { type: String, required: true } },
  computed: {
    // The whole deck, rendered by scripts/render_slides.py; anyone with the guide's link can download it.
    deckFile: () => DECK_FILE,
    deckUrl: () => `${getBasePath()}/slides/${DECK_FILE}`
  },
  data() { return { slides: [], index: 0, readMode: false, focused: false, loading: true, error: false, controller: null, blockedElements: [] } },
  methods: {
    render: markdownToHtml,
    async load() {
      this.controller?.abort()
      const controller = new AbortController()
      this.controller = controller
      this.loading = true
      this.error = false
      try {
        const response = await fetch(`${getBasePath()}${this.src}`, { signal: controller.signal })
        if (!response.ok) throw new Error('Slide request failed')
        const slides = splitSlides(await response.text())
        if (!slides.length) throw new Error('Empty introduction')
        if (controller.signal.aborted) return
        this.slides = slides
        this.index = 0
      } catch {
        if (!controller.signal.aborted) this.error = true
      } finally {
        if (!controller.signal.aborted) this.loading = false
      }
    },
    move(delta) { this.index = Math.max(0, Math.min(this.slides.length - 1, this.index + delta)) },
    restoreBackground() {
      for (const element of this.blockedElements) element.inert = false
      this.blockedElements = []
    },
    isolateIntroduction() {
      // Inert siblings at every ancestor level, never the ancestor containing this deck.
      let element = this.$refs.frame
      while (element?.parentElement) {
        for (const sibling of element.parentElement.children) {
          if (sibling !== element && !sibling.inert) {
            sibling.inert = true
            this.blockedElements.push(sibling)
          }
        }
        element = element.parentElement
      }
    },
    async toggleFocus() {
      this.focused = !this.focused
      await this.$nextTick()
      if (this.focused) {
        this.isolateIntroduction()
        this.$refs.frame?.focus()
      } else {
        this.restoreBackground()
        this.$refs.focusButton?.focus()
      }
    },
    handleKeys(event) {
      if (event.key === 'Escape' && this.focused) { event.preventDefault(); void this.toggleFocus() }
      if (!this.readMode && ['ArrowLeft', 'ArrowRight'].includes(event.key)) {
        event.preventDefault(); this.move(event.key === 'ArrowLeft' ? -1 : 1)
      }
      // Keep keyboard focus inside the expanded introduction until Escape or Exit.
      if (this.focused && event.key === 'Tab') {
        const controls = [...this.$refs.frame.querySelectorAll('button:not([disabled]), a[href]')]
        const current = controls.indexOf(document.activeElement)
        if (current < 0 || (!event.shiftKey && current === controls.length - 1) || (event.shiftKey && current === 0)) {
          event.preventDefault(); controls[event.shiftKey ? controls.length - 1 : 0]?.focus()
        }
      }
    }
  },
  mounted() { void this.load() },
  beforeUnmount() { this.controller?.abort(); this.restoreBackground() }
}
</script>

<style scoped>
.lesson-slides { margin: 1.4rem 0 2rem; border: 1px solid #526079; border-radius: 12px; padding: 1rem; color: #f1f5f9; background: #0c202b; }
.slide-toolbar, .slide-modes, .slide-navigation { display: flex; align-items: center; gap: .5rem; flex-wrap: wrap; }
.slide-toolbar, .slide-navigation { justify-content: space-between; }
button { background: #1f3545; color: #f1f5f9; border: 1px solid #698094; border-radius: 6px; padding: .5rem .7rem; cursor: pointer; font: inherit; }
button[aria-pressed="true"] { background: #b92a23; border-color: #ff766e; }
button:disabled { opacity: .45; cursor: default; }
a.download { color: #b7d5ff; padding: .5rem .2rem; }
button:focus-visible, a.download:focus-visible, .lesson-slides:focus-visible { outline: 3px solid #a9c7ff; outline-offset: 3px; }
.slide-body { overflow-wrap: anywhere; line-height: 1.6; }
.slide-card { min-height: 18rem; padding: 1rem 0; }
.slide-body :deep(h1) { font-size: clamp(1.5rem, 3vw, 2.7rem); line-height: 1.2; margin: .75rem 0 1.25rem; }
.slide-body :deep(img) { display: block; width: 100%; max-height: 45vh; object-fit: contain; margin: 1rem auto; }
.slide-body :deep(pre) { overflow-x: auto; padding: 1rem; background: #08151e; }
.slide-body :deep(a) { color: #b7d5ff; }
.slide-text article + article { border-top: 1px solid #526079; margin-top: 1.5rem; padding-top: 1rem; }
.is-focused { position: fixed; inset: 0; z-index: 1000; margin: 0; border-radius: 0; overflow-y: auto; padding: clamp(1rem, 4vw, 3rem); }
.is-focused .slide-body { max-width: 1000px; margin-left: auto; margin-right: auto; font-size: 1.2rem; }
.is-focused .slide-card { min-height: 65vh; }
.is-focused .slide-body:has(img) { max-width: min(1600px, 96vw); }
.is-focused .slide-body :deep(img) { max-height: 80vh; }
.focus-hint { color: #a9bac8; font-size: .85rem; }
</style>
