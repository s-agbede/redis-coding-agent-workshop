// Shared styles and components for Redis workshops
// This package provides common design tokens, themes, and reusable components

// Styles are imported directly via path:
// import '@redis-workshop/components/styles/tokens.css'
// import '@redis-workshop/components/styles/dark-theme.css'

// Utilities
export {
  getBasePath,
  getApiUrl,
  getWorkshopHubUrl,
  getRedisInsightUrl
} from './utils/basePath.js';

export {
  bindContentAction,
  createContentRenderModel,
  getStageNavItems
} from './content-renderer/renderModel.js';

export { renderMarkdown } from './content-renderer/markdown.js';

// Components - Editor
export { default as CodeEditor } from './components/CodeEditor.vue';
export { default as WorkshopEditorLayout } from './components/WorkshopEditorLayout.vue';

// Components - UI (shared across workshop home/views)
export { default as WorkshopModal } from './components/WorkshopModal.vue';
export { default as WorkshopStageNav } from './components/WorkshopStageNav.vue';
export { default as WorkshopProgressIndicator } from './components/WorkshopProgressIndicator.vue';
export { default as WorkshopHubLink } from './components/WorkshopHubLink.vue';
export { default as WorkshopHeader } from './components/WorkshopHeader.vue';
export { default as WorkshopContentRenderer } from './components/WorkshopContentRenderer.vue';

// Components - New Workshop Flow (Intro, Review, Demo, Build)
export { default as WorkshopIntroPage } from './components/WorkshopIntroPage.vue';
export { default as WorkshopScrollableDemo } from './components/WorkshopScrollableDemo.vue';

export default {};
