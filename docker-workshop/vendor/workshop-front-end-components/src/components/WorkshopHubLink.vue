<template>
  <a :href="hubUrl" class="hub-link" :class="[variantClass, sizeClass]">
    <span v-if="showIcon" class="hub-icon">
      <slot name="icon">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path>
          <polyline points="9 22 9 12 15 12 15 22"></polyline>
        </svg>
      </slot>
    </span>
    <span class="hub-text">
      <slot>{{ text }}</slot>
    </span>
    <span v-if="showArrow" class="hub-arrow">→</span>
  </a>
</template>

<script>
/**
 * WorkshopHubLink - Consistent link back to Workshop Hub
 * 
 * Usage:
 *   <WorkshopHubLink />
 *   <WorkshopHubLink variant="button" text="Back to Hub" />
 *   <WorkshopHubLink variant="minimal" :show-icon="false" />
 * 
 * Props:
 *   - hubUrl (String): URL to workshop hub (default: '/')
 *   - text (String): Link text (default: 'Workshop Hub')
 *   - variant (String): 'link', 'button', 'minimal' (default: 'link')
 *   - size (String): 'sm', 'md', 'lg' (default: 'md')
 *   - showIcon (Boolean): Show home icon (default: true)
 *   - showArrow (Boolean): Show arrow indicator (default: false)
 * 
 * Slots:
 *   - default: Custom link text
 *   - icon: Custom icon
 */
export default {
  name: 'WorkshopHubLink',
  props: {
    hubUrl: { type: String, default: '/' },
    text: { type: String, default: 'Workshop Hub' },
    variant: {
      type: String,
      default: 'link',
      validator: v => ['link', 'button', 'minimal'].includes(v)
    },
    size: {
      type: String,
      default: 'md',
      validator: v => ['sm', 'md', 'lg'].includes(v)
    },
    showIcon: { type: Boolean, default: true },
    showArrow: { type: Boolean, default: false }
  },
  computed: {
    variantClass() {
      return `variant-${this.variant}`;
    },
    sizeClass() {
      return `size-${this.size}`;
    }
  }
};
</script>

<style scoped>
.hub-link {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2, 0.5rem);
  text-decoration: none;
  transition: all var(--transition-base, 200ms);
  font-weight: var(--font-weight-medium, 500);
}

/* Size variants */
.size-sm { font-size: var(--font-size-xs, 0.75rem); }
.size-md { font-size: var(--font-size-sm, 0.875rem); }
.size-lg { font-size: var(--font-size-base, 1rem); }

.size-sm .hub-icon svg { width: 12px; height: 12px; }
.size-md .hub-icon svg { width: 16px; height: 16px; }
.size-lg .hub-icon svg { width: 20px; height: 20px; }

/* Link variant (default) */
.variant-link {
  color: var(--color-text-secondary, #94a3b8);
}

.variant-link:hover {
  color: var(--color-text, #e2e8f0);
}

/* Button variant */
.variant-button {
  padding: var(--spacing-2, 0.5rem) var(--spacing-4, 1rem);
  background: var(--color-dark-800, #0D1A22);
  border: 1px solid var(--color-border, rgba(71, 85, 105, 0.5));
  border-radius: var(--radius-md, 6px);
  color: var(--color-text, #e2e8f0);
}

.variant-button:hover {
  background: var(--color-border, rgba(71, 85, 105, 0.5));
  border-color: var(--color-text-secondary, #94a3b8);
}

.variant-button.size-sm { padding: var(--spacing-1, 0.25rem) var(--spacing-3, 0.75rem); }
.variant-button.size-lg { padding: var(--spacing-3, 0.75rem) var(--spacing-5, 1.25rem); }

/* Minimal variant */
.variant-minimal {
  color: var(--color-text-muted, #64748b);
}

.variant-minimal:hover {
  color: var(--color-text-secondary, #94a3b8);
  text-decoration: underline;
}

/* Icon styling */
.hub-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Arrow styling */
.hub-arrow {
  opacity: 0;
  transform: translateX(-4px);
  transition: all var(--transition-base, 200ms);
}

.hub-link:hover .hub-arrow {
  opacity: 1;
  transform: translateX(0);
}
</style>

