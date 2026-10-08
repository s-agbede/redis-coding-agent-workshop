<template>
  <div id="app">
    <p v-if="directGuide" class="workbench-link">These are the workshop instructions. <a href="/">Open the workbench</a> to use the editor, terminal and app beside them.</p>
    <router-view />
  </div>
</template>

<script>
import { getBasePath } from './utils/basePath'

export default {
  name: 'App',
  data() {
    return { directGuide: getBasePath() === '/guide' && window.parent === window }
  }
}
</script>

<style>
/* Global styles */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
  background: #1a1a2e;
  color: #e2e8f0;
  line-height: 1.5;
}

#app {
  min-height: 100vh;
}
.workbench-link { padding: .75rem 1rem; background: #24334c; }
.workbench-link a { color: #a9c7ff; }

/* Scrollbar styling */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: #2d3748;
}

::-webkit-scrollbar-thumb {
  background: #4a5568;
  border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
  background: #718096;
}
</style>
