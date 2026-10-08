<template>
  <section class="workshop-content-renderer">
    <div v-if="renderIssues.length" class="content-renderer-status content-renderer-status--error">
      <strong>Renderer warnings:</strong>
      <ul>
        <li v-for="issue in renderIssues" :key="issue">{{ issue }}</li>
      </ul>
    </div>

    <div v-if="showTitle || displaySummary || displayStageTitle" class="content-renderer-header">
      <h2 v-if="showTitle" class="content-renderer-header__title">{{ renderModel.title }}</h2>
      <div v-if="displayStageTitle" class="content-renderer-header__stage">{{ renderModel.stage.title }}</div>
      <WorkshopMarkdownContent v-if="displaySummary" :body="renderModel.summary" />
    </div>

    <section
      v-for="section in renderModel.sections"
      :key="section.sectionId"
      class="content-section"
    >
      <header v-if="section.title || section.body" class="content-section__header">
        <h3 v-if="section.title">{{ section.title }}</h3>
        <WorkshopMarkdownContent v-if="section.body" :body="section.body" />
      </header>

      <div class="content-section__blocks">
        <WorkshopContentBlockRenderer
          v-for="(block, blockIndex) in section.blocks"
          :key="`${section.sectionId}-block-${blockIndex}`"
          :block="block"
          :content="content"
          :section="section"
          :stage="renderModel.stage"
          :widgets="widgets"
          :widget-props="widgetProps"
          @action="handleAction"
        />
      </div>
    </section>
  </section>
</template>

<script>
import '../styles/content-renderer.css';

import {
  bindContentAction,
  createContentRenderModel
} from '../content-renderer/renderModel.js';
import WorkshopContentBlockRenderer from './WorkshopContentBlockRenderer.vue';
import WorkshopMarkdownContent from './WorkshopMarkdownContent.vue';

export default {
  name: 'WorkshopContentRenderer',
  components: {
    WorkshopContentBlockRenderer,
    WorkshopMarkdownContent
  },
  props: {
    content: { type: Object, required: true },
    tokens: { type: Object, default: () => ({}) },
    activeStageId: { type: String, default: '' },
    actionHandlers: { type: Object, default: () => ({}) },
    widgets: { type: Object, default: () => ({}) },
    widgetProps: { type: Object, default: () => ({}) },
    showTitle: { type: Boolean, default: false },
    showSummary: { type: Boolean, default: true },
    showStageTitle: { type: Boolean, default: true }
  },
  emits: ['action', 'render-error'],
  computed: {
    displayStageTitle() {
      return this.showStageTitle && Boolean(this.renderModel.stage?.title);
    },
    displaySummary() {
      return this.showSummary && Boolean(this.renderModel.summary);
    },
    renderIssues() {
      return [...this.renderModel.errors, ...this.renderModel.missingTokens.map(token => `Missing token: ${token}`)];
    },
    renderModel() {
      return createContentRenderModel(this.content, {
        tokens: this.tokens,
        activeStageId: this.activeStageId
      });
    }
  },
  watch: {
    renderIssues: {
      immediate: true,
      handler(issues) {
        if (issues.length) {
          this.$emit('render-error', issues);
        }
      }
    }
  },
  methods: {
    handleAction(payload) {
      const actionPayload = {
        ...payload,
        viewId: this.renderModel.viewId,
        pageType: this.renderModel.pageType
      };

      this.$emit('action', actionPayload);
      bindContentAction(this.actionHandlers, actionPayload);
    }
  }
};
</script>
