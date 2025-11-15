<script setup lang="ts">
import { ref, watch } from 'vue'
import { X } from 'lucide-vue-next'

interface FormField {
  key: string
  label: string
  type: 'text' | 'email' | 'number' | 'date' | 'select' | 'checkbox' | 'textarea'
  required?: boolean
  options?: { value: string | number; label: string }[]
  placeholder?: string
  min?: number
  max?: number
  step?: number
}

interface Props {
  fields: FormField[]
  initialData?: Record<string, any> | null
  title?: string
  submitLabel?: string
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  submitLabel: 'Salvar',
  loading: false
})

const emit = defineEmits<{
  submit: [data: Record<string, any>]
  cancel: []
}>()

const formData = ref<Record<string, any>>({})

// Initialize form data
watch(() => props.initialData, (data) => {
  if (data) {
    formData.value = { ...data }
  } else {
    formData.value = {}
    props.fields.forEach(field => {
      if (field.type === 'checkbox') {
        formData.value[field.key] = false
      } else if (field.type === 'number') {
        formData.value[field.key] = 0
      } else {
        formData.value[field.key] = ''
      }
    })
  }
}, { immediate: true })

function handleSubmit() {
  // Validate required fields
  for (const field of props.fields) {
    if (field.required && !formData.value[field.key]) {
      alert(`O campo "${field.label}" é obrigatório`)
      return
    }
  }
  
  emit('submit', { ...formData.value })
}

function handleCancel() {
  emit('cancel')
}

function getFieldValue(field: FormField): any {
  return formData.value[field.key] ?? (field.type === 'checkbox' ? false : '')
}
</script>

<template>
  <div class="admin-form-container">
    <div v-if="title" class="form-header">
      <h2 class="form-title">{{ title }}</h2>
      <button @click="handleCancel" class="close-button" title="Fechar">
        <X :size="20" />
      </button>
    </div>

    <form @submit.prevent="handleSubmit" class="admin-form">
      <div
        v-for="field in fields"
        :key="field.key"
        class="form-field"
      >
        <label :for="field.key" class="field-label">
          {{ field.label }}
          <span v-if="field.required" class="required">*</span>
        </label>

        <!-- Text Input -->
        <input
          v-if="field.type === 'text' || field.type === 'email'"
          :id="field.key"
          v-model="formData[field.key]"
          :type="field.type"
          :placeholder="field.placeholder"
          :required="field.required"
          class="form-input"
        />

        <!-- Number Input -->
        <input
          v-else-if="field.type === 'number'"
          :id="field.key"
          v-model.number="formData[field.key]"
          type="number"
          :placeholder="field.placeholder"
          :required="field.required"
          :min="field.min"
          :max="field.max"
          :step="field.step"
          class="form-input"
        />

        <!-- Date Input -->
        <input
          v-else-if="field.type === 'date'"
          :id="field.key"
          v-model="formData[field.key]"
          type="date"
          :required="field.required"
          class="form-input"
        />

        <!-- Select -->
        <select
          v-else-if="field.type === 'select'"
          :id="field.key"
          v-model="formData[field.key]"
          :required="field.required"
          class="form-select"
        >
          <option value="">Selecione...</option>
          <option
            v-for="option in field.options"
            :key="option.value"
            :value="option.value"
          >
            {{ option.label }}
          </option>
        </select>

        <!-- Checkbox -->
        <div v-else-if="field.type === 'checkbox'" class="checkbox-wrapper">
          <input
            :id="field.key"
            v-model="formData[field.key]"
            type="checkbox"
            class="form-checkbox"
          />
          <label :for="field.key" class="checkbox-label">
            {{ field.placeholder || 'Ativo' }}
          </label>
        </div>

        <!-- Textarea -->
        <textarea
          v-else-if="field.type === 'textarea'"
          :id="field.key"
          v-model="formData[field.key]"
          :placeholder="field.placeholder"
          :required="field.required"
          rows="4"
          class="form-textarea"
        />
      </div>

      <div class="form-actions">
        <button
          type="button"
          @click="handleCancel"
          class="button button-secondary"
          :disabled="loading"
        >
          Cancelar
        </button>
        <button
          type="submit"
          class="button button-primary"
          :disabled="loading"
        >
          <span v-if="loading">Salvando...</span>
          <span v-else>{{ submitLabel }}</span>
        </button>
      </div>
    </form>
  </div>
</template>

<style scoped>
.admin-form-container {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.form-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #e2e8f0;
}

.form-title {
  font-size: 20px;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}

.close-button {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  border: none;
  background: #f1f5f9;
  border-radius: 6px;
  cursor: pointer;
  color: #64748b;
  transition: all 0.2s;
}

.close-button:hover {
  background: #e2e8f0;
  color: #0f172a;
}

.admin-form {
  padding: 24px;
}

.form-field {
  margin-bottom: 20px;
}

.field-label {
  display: block;
  font-size: 14px;
  font-weight: 600;
  color: #0f172a;
  margin-bottom: 8px;
}

.required {
  color: #dc2626;
}

.form-input,
.form-select,
.form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 14px;
  font-family: inherit;
  transition: all 0.2s;
  background: white;
}

.form-input:focus,
.form-select:focus,
.form-textarea:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-textarea {
  resize: vertical;
  min-height: 100px;
}

.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-checkbox {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.checkbox-label {
  font-size: 14px;
  color: #64748b;
  cursor: pointer;
  margin: 0;
}

.form-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
  padding-top: 24px;
  border-top: 1px solid #e2e8f0;
}

.button {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.button-primary {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
}

.button-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

.button-secondary {
  background: #f1f5f9;
  color: #64748b;
}

.button-secondary:hover:not(:disabled) {
  background: #e2e8f0;
  color: #0f172a;
}
</style>

