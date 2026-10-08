<template>
  <component
    :is="displayTag"
    v-bind="componentAttrs"
    class="content-action"
    :class="[
      `content-action--${appearance}`,
      `content-action--${display}`
    ]"
    @click.prevent="$emit('trigger', action)"
  >
    {{ action.label }}
  </component>
</template>

<script>
export default {
  name: 'WorkshopContentAction',
  props: {
    action: { type: Object, required: true },
    appearance: { type: String, default: 'secondary' },
    display: { type: String, default: 'button' }
  },
  emits: ['trigger'],
  computed: {
    componentAttrs() {
      if (this.display === 'link') {
        return { href: '#' };
      }

      return { type: 'button' };
    },
    displayTag() {
      return this.display === 'link' ? 'a' : 'button';
    }
  }
};
</script>
