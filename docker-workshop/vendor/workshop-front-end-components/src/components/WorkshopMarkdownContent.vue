<template>
  <div v-if="html" class="workshop-markdown" v-html="html"></div>
</template>

<script>
import { renderMarkdown } from '../content-renderer/markdown.js';

export default {
  name: 'WorkshopMarkdownContent',
  props: {
    body: { type: String, default: '' }
  },
  computed: {
    html() {
      return renderMarkdown(this.body);
    }
  }
};
</script>
