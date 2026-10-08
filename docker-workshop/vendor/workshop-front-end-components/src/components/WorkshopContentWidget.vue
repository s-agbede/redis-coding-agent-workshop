<template>
  <component
    :is="widget"
    v-if="widget"
    v-bind="resolvedProps"
  />
  <div v-else class="content-widget content-widget--missing">
    Widget unavailable: <code>{{ widgetId }}</code>
  </div>
</template>

<script>
export default {
  name: 'WorkshopContentWidget',
  props: {
    widget: { type: [Object, Function], default: null },
    widgetId: { type: String, required: true },
    widgetProps: { type: Object, default: () => ({}) },
    contextProps: { type: Object, default: () => ({}) }
  },
  computed: {
    resolvedProps() {
      return {
        ...this.contextProps,
        ...this.widgetProps
      };
    }
  }
};
</script>
