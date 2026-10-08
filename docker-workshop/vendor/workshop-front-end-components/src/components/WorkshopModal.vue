<template>
  <Teleport to="body">
    <div v-if="modelValue" class="modal-overlay" @click.self="handleOverlayClick">
      <div class="modal-container" :class="[sizeClass]">
        <div class="modal-header">
          <h3>{{ title }}</h3>
          <button v-if="showCloseButton" class="modal-close" @click="close">×</button>
        </div>
        <div class="modal-body">
          <slot>
            <p v-for="(line, index) in messageLines" :key="index">{{ line }}</p>
          </slot>
        </div>
        <div class="modal-footer">
          <slot name="footer">
            <button v-if="type === 'confirm'" @click="close" class="btn btn-outline">
              {{ cancelText }}
            </button>
            <button @click="confirm" class="btn btn-primary">
              {{ computedConfirmText }}
            </button>
          </slot>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script>
/**
 * WorkshopModal - Reusable modal component for workshops
 * 
 * Usage:
 *   <WorkshopModal
 *     v-model="showModal"
 *     title="Restart Lab"
 *     message="Are you sure?"
 *     type="confirm"
 *     @confirm="handleConfirm"
 *   />
 * 
 * Props:
 *   - modelValue (Boolean): Controls visibility (v-model)
 *   - title (String): Modal header title
 *   - message (String): Message text (supports \n for line breaks)
 *   - type (String): 'alert' or 'confirm' - determines button layout
 *   - confirmText (String): Text for confirm button (default: 'OK' or 'Confirm')
 *   - cancelText (String): Text for cancel button (default: 'Cancel')
 *   - size (String): 'sm', 'md', 'lg' (default: 'md')
 *   - closeOnOverlay (Boolean): Close when clicking overlay (default: true)
 *   - showCloseButton (Boolean): Show X button in header (default: false)
 * 
 * Events:
 *   - update:modelValue: Emitted to close modal
 *   - confirm: Emitted when confirm button clicked
 *   - cancel: Emitted when cancel button clicked or modal closed
 */
export default {
  name: 'WorkshopModal',
  props: {
    modelValue: { type: Boolean, default: false },
    title: { type: String, default: 'Notice' },
    message: { type: String, default: '' },
    type: { type: String, default: 'alert', validator: v => ['alert', 'confirm'].includes(v) },
    confirmText: { type: String, default: '' },
    cancelText: { type: String, default: 'Cancel' },
    size: { type: String, default: 'md', validator: v => ['sm', 'md', 'lg'].includes(v) },
    closeOnOverlay: { type: Boolean, default: true },
    showCloseButton: { type: Boolean, default: false }
  },
  emits: ['update:modelValue', 'confirm', 'cancel'],
  computed: {
    messageLines() {
      return this.message ? this.message.split('\n') : [];
    },
    sizeClass() {
      return `modal-${this.size}`;
    },
    computedConfirmText() {
      if (this.confirmText) return this.confirmText;
      return this.type === 'confirm' ? 'Confirm' : 'OK';
    }
  },
  methods: {
    close() {
      this.$emit('update:modelValue', false);
      this.$emit('cancel');
    },
    confirm() {
      this.$emit('confirm');
      this.$emit('update:modelValue', false);
    },
    handleOverlayClick() {
      if (this.closeOnOverlay) {
        this.close();
      }
    }
  }
};
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal, 1050);
  backdrop-filter: blur(4px);
}

.modal-container {
  background: var(--color-surface, #101A21);
  border-radius: var(--radius-lg, 8px);
  border: 1px solid var(--color-border, rgba(71, 85, 105, 0.5));
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  max-height: 90vh;
  overflow-y: auto;
}

.modal-sm { width: min(350px, 90vw); }
.modal-md { width: min(450px, 90vw); }
.modal-lg { width: min(600px, 90vw); }

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-4, 1rem) var(--spacing-5, 1.25rem);
  border-bottom: 1px solid var(--color-border, rgba(71, 85, 105, 0.5));
}

.modal-header h3 {
  margin: 0;
  font-size: var(--font-size-lg, 1.125rem);
  color: var(--color-text, #e2e8f0);
}

.modal-close {
  background: none;
  border: none;
  color: var(--color-text-secondary, #94a3b8);
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0;
  line-height: 1;
}

.modal-close:hover { color: var(--color-text, #e2e8f0); }

.modal-body {
  padding: var(--spacing-5, 1.25rem);
}

.modal-body p {
  margin: 0 0 var(--spacing-2, 0.5rem) 0;
  color: var(--color-text-secondary, #94a3b8);
  line-height: 1.6;
}

.modal-body p:last-child { margin-bottom: 0; }

.modal-footer {
  padding: var(--spacing-4, 1rem) var(--spacing-5, 1.25rem);
  border-top: 1px solid var(--color-border, rgba(71, 85, 105, 0.5));
  display: flex;
  justify-content: flex-end;
  gap: var(--spacing-3, 0.75rem);
}

/* Button styles - can be overridden by parent */
.btn {
  padding: var(--spacing-3, 0.75rem) var(--spacing-5, 1.25rem);
  border: none;
  border-radius: var(--radius-md, 6px);
  font-size: var(--font-size-sm, 0.875rem);
  font-weight: var(--font-weight-semibold, 600);
  cursor: pointer;
  transition: all var(--transition-base, 200ms);
}

.btn-primary {
  background: #DC382C;
  color: white;
}
.btn-primary:hover { background: #c42f24; }

.btn-outline {
  background: transparent;
  border: 1px solid var(--color-border, rgba(71, 85, 105, 0.5));
  color: var(--color-text, #e2e8f0);
}
.btn-outline:hover { background: var(--color-border, rgba(71, 85, 105, 0.5)); }
</style>
