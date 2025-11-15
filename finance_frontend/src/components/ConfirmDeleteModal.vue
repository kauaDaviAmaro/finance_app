<script setup lang="ts">
import { X, AlertTriangle } from 'lucide-vue-next'

interface Props {
  show: boolean
  title?: string
  message: string
  warning?: string
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  title: 'Confirmar Exclusão',
  loading: false
})

const emit = defineEmits<{
  confirm: []
  cancel: []
}>()

function handleConfirm() {
  if (!props.loading) {
    emit('confirm')
  }
}

function handleCancel() {
  if (!props.loading) {
    emit('cancel')
  }
}
</script>

<template>
  <Teleport to="body">
    <Transition name="modal">
      <div v-if="show" class="modal-overlay" @click="handleCancel">
        <div class="modal-content" @click.stop>
          <div class="modal-header">
            <div class="modal-title-wrapper">
              <AlertTriangle :size="24" class="modal-icon" />
              <h2 class="modal-title">{{ title }}</h2>
            </div>
            <button 
              @click="handleCancel" 
              class="modal-close"
              :disabled="loading"
            >
              <X :size="20" />
            </button>
          </div>

          <div class="modal-body">
            <p class="modal-message">{{ message }}</p>
            <div v-if="warning" class="modal-warning">
              <AlertTriangle :size="20" />
              <span>{{ warning }}</span>
            </div>
          </div>

          <div class="modal-footer">
            <button 
              @click="handleCancel" 
              class="cancel-button"
              :disabled="loading"
            >
              Cancelar
            </button>
            <button 
              @click="handleConfirm" 
              class="confirm-button"
              :disabled="loading"
            >
              <span v-if="loading">Excluindo...</span>
              <span v-else>Excluir Portfolio</span>
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
  backdrop-filter: blur(4px);
}

.modal-content {
  background: white;
  border-radius: 16px;
  max-width: 500px;
  width: 100%;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px;
  border-bottom: 1px solid #e2e8f0;
}

.modal-title-wrapper {
  display: flex;
  align-items: center;
  gap: 12px;
}

.modal-icon {
  color: #dc2626;
  flex-shrink: 0;
}

.modal-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.modal-close {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 8px;
  background: #f1f5f9;
  border: none;
  border-radius: 8px;
  color: #64748b;
  cursor: pointer;
  transition: all 0.2s;
}

.modal-close:hover:not(:disabled) {
  background: #e2e8f0;
  color: #0f172a;
}

.modal-close:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-body {
  padding: 24px;
}

.modal-message {
  font-size: 15px;
  color: #334155;
  line-height: 1.6;
  margin: 0 0 16px 0;
}

.modal-warning {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: #fef3c7;
  border: 1px solid #fbbf24;
  border-radius: 12px;
  color: #92400e;
  font-size: 14px;
  line-height: 1.5;
}

.modal-warning svg {
  flex-shrink: 0;
  margin-top: 2px;
  color: #f59e0b;
}

.modal-footer {
  display: flex;
  gap: 12px;
  padding: 24px;
  border-top: 1px solid #e2e8f0;
  justify-content: flex-end;
}

.cancel-button {
  padding: 12px 24px;
  background: #f1f5f9;
  color: #64748b;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.cancel-button:hover:not(:disabled) {
  background: #e2e8f0;
  color: #0f172a;
}

.cancel-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.confirm-button {
  padding: 12px 24px;
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.confirm-button:hover:not(:disabled) {
  background: #b91c1c;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
}

.confirm-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none;
}

/* Animations */
.modal-enter-active,
.modal-leave-active {
  transition: opacity 0.2s ease;
}

.modal-enter-active .modal-content,
.modal-leave-active .modal-content {
  transition: transform 0.3s ease, opacity 0.3s ease;
}

.modal-enter-from,
.modal-leave-to {
  opacity: 0;
}

.modal-enter-from .modal-content,
.modal-leave-to .modal-content {
  transform: translateY(-20px) scale(0.95);
  opacity: 0;
}

@media (max-width: 640px) {
  .modal-content {
    max-width: 100%;
    margin: 0;
    border-radius: 16px 16px 0 0;
  }

  .modal-overlay {
    padding: 0;
    align-items: flex-end;
  }

  .modal-header,
  .modal-body,
  .modal-footer {
    padding: 20px;
  }

  .modal-footer {
    flex-direction: column-reverse;
  }

  .cancel-button,
  .confirm-button {
    width: 100%;
    justify-content: center;
  }
}
</style>

