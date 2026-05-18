<template>
  <div class="img-preview">
    <img :src="store.pendingImage.previewUrl" alt="待上传" />
    <button class="btn-remove" @click="store.clearPendingImage()" title="移除图片">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
      </svg>
    </button>
    <span class="img-label">待识别食材</span>
  </div>
</template>

<script setup>
import { useChatStore } from '../stores/chat.js'
const store = useChatStore()
</script>

<style scoped>
.img-preview {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: var(--bg-dialog);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  position: relative;
}

.img-preview img {
  width: 40px;
  height: 40px;
  object-fit: cover;
  border-radius: 6px;
}

.img-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.btn-remove {
  position: absolute;
  top: -6px;
  right: -6px;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: var(--bg-input);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--text-secondary);
  font-size: 12px;
  transition: color 0.15s, border-color 0.15s;
}

.btn-remove:hover {
  color: var(--danger);
  border-color: var(--danger);
}
</style>
