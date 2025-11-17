<script setup lang="ts">
import { ref, computed } from 'vue'
import { Save, Trash2, Download, Upload, Edit2, X } from 'lucide-vue-next'
import type { WavePoint, ElliottAnnotation } from '../services/api/types'

interface Props {
  annotations: WavePoint[]
  isEditMode: boolean
  isLoading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  isLoading: false,
})

const emit = defineEmits<{
  (e: 'save', annotations: WavePoint[]): void
  (e: 'delete'): void
  (e: 'load', annotations: WavePoint[]): void
  (e: 'toggle-edit'): void
}>()

const currentWave = ref<string>('1')
const availableWaves = ['1', '2', '3', '4', '5', 'A', 'B', 'C']

const annotationsByWave = computed(() => {
  const grouped: Record<string, WavePoint[]> = {}
  props.annotations.forEach((ann) => {
    if (!grouped[ann.wave]) {
      grouped[ann.wave] = []
    }
    grouped[ann.wave].push(ann)
  })
  return grouped
})

function handleSave() {
  emit('save', props.annotations)
}

function handleDelete() {
  emit('delete')
}

function handleLoad(loadedAnnotations: WavePoint[]) {
  emit('load', loadedAnnotations)
}

function handleToggleEdit() {
  emit('toggle-edit')
}

function removeAnnotation(wave: string, date: string) {
  const filtered = props.annotations.filter(
    (ann) => !(ann.wave === wave && ann.date === date)
  )
  emit('save', filtered)
}
</script>

<template>
  <div class="elliott-wave-editor">
    <div class="editor-header">
      <h4>Editor de Ondas</h4>
      <button
        @click="handleToggleEdit"
        :class="['btn', 'btn-toggle', { active: isEditMode }]"
        :disabled="isLoading"
        title="Alternar modo de edição"
      >
        <Edit2 :size="14" />
        <span v-if="!isEditMode">Editar</span>
        <span v-else>Ativo</span>
      </button>
    </div>

    <div v-if="annotations.length === 0" class="empty-state">
      <p>Nenhuma anotação manual. Clique no gráfico no modo de edição para adicionar ondas.</p>
    </div>

    <div v-else class="annotations-list">
      <div
        v-for="wave in availableWaves"
        :key="wave"
        class="wave-group"
      >
        <h5 class="wave-group-title">Onda {{ wave }}</h5>
        <div v-if="annotationsByWave[wave] && annotationsByWave[wave].length > 0" class="wave-items">
          <div
            v-for="(ann, idx) in annotationsByWave[wave]"
            :key="`${wave}_${idx}`"
            class="wave-item"
          >
            <div class="wave-item-info">
              <span class="wave-date">{{ new Date(ann.date).toLocaleDateString('pt-BR') }}</span>
              <span class="wave-price">
                {{ new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(ann.price) }}
              </span>
            </div>
            <button
              @click="removeAnnotation(wave, ann.date)"
              class="btn-remove"
              :disabled="isLoading"
              title="Remover anotação"
            >
              <X :size="14" />
            </button>
          </div>
        </div>
        <div v-else class="wave-empty">
          <span>Nenhuma anotação</span>
        </div>
      </div>
    </div>

    <div class="editor-footer">
      <button
        @click="handleSave"
        class="btn btn-primary"
        :disabled="isLoading || annotations.length === 0"
      >
        <Save :size="16" />
        Salvar Anotações
      </button>
      <button
        @click="handleDelete"
        class="btn btn-danger"
        :disabled="isLoading || annotations.length === 0"
      >
        <Trash2 :size="16" />
        Deletar Todas
      </button>
    </div>

    <div v-if="isEditMode" class="edit-mode-hint">
      <p>💡 Modo de edição ativo: Clique no gráfico para adicionar pontos de onda.</p>
      <p>Selecione a onda atual usando os botões acima.</p>
    </div>
  </div>
</template>

<style scoped>
.elliott-wave-editor {
  background: transparent;
  border-radius: 0;
  padding: 0;
  box-shadow: none;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.editor-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 700;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.editor-actions {
  display: flex;
  gap: 8px;
}

.btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-toggle {
  background: #f3f4f6;
  color: #374151;
  padding: 6px 10px;
  font-size: 12px;
}

.btn-toggle:hover:not(:disabled) {
  background: #e5e7eb;
}

.btn-toggle.active {
  background: #3b82f6;
  color: white;
}

.btn-primary {
  background: #3b82f6;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #2563eb;
}

.btn-danger {
  background: #ef4444;
  color: white;
}

.btn-danger:hover:not(:disabled) {
  background: #dc2626;
}

.empty-state {
  text-align: center;
  padding: 32px;
  color: #6b7280;
  font-size: 14px;
}

.annotations-list {
  max-height: 300px;
  overflow-y: auto;
  margin-bottom: 16px;
}

.wave-group {
  margin-bottom: 16px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
}

.wave-group-title {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.wave-items {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.wave-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: white;
  border-radius: 4px;
  border: 1px solid #e5e7eb;
}

.wave-item-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.wave-date {
  font-size: 12px;
  color: #6b7280;
}

.wave-price {
  font-size: 14px;
  font-weight: 600;
  color: #111827;
}

.btn-remove {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  background: #fee2e2;
  color: #dc2626;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-remove:hover:not(:disabled) {
  background: #fecaca;
}

.wave-empty {
  padding: 8px;
  text-align: center;
  color: #9ca3af;
  font-size: 12px;
}

.editor-footer {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #e5e7eb;
}

.editor-footer .btn {
  width: 100%;
  justify-content: center;
}

.edit-mode-hint {
  margin-top: 12px;
  padding: 12px;
  background: #eff6ff;
  border-radius: 6px;
  border-left: 4px solid #3b82f6;
}

.edit-mode-hint p {
  margin: 4px 0;
  font-size: 12px;
  color: #1e40af;
}
</style>

