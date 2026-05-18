<template>
  <div class="input-area">
    <div class="input-wrapper">
      <!-- Image upload button -->
      <label class="btn-upload" title="上传食材图片">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
          <circle cx="8.5" cy="8.5" r="1.5"/>
          <polyline points="21 15 16 10 5 21"/>
        </svg>
        <input
          type="file"
          accept="image/jpeg,image/png,image/webp"
          hidden
          @change="onImagePicked"
        />
      </label>

      <!-- Text input -->
      <textarea
        ref="textareaRef"
        v-model="inputText"
        :disabled="store.isStreaming"
        :placeholder="placeholder"
        class="text-input"
        rows="1"
        @input="autoResize"
        @keydown.enter.exact="onSend"
      ></textarea>

      <!-- Send button -->
      <button
        :disabled="!canSend"
        class="btn-send"
        @click="onSend"
        title="发送"
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="22" y1="2" x2="11" y2="13"/>
          <polygon points="22 2 15 22 11 13 2 9 22 2"/>
        </svg>
      </button>
    </div>
    <p class="input-hint">Enter 发送 · Shift+Enter 换行</p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useChatStore } from '../stores/chat.js'

const store = useChatStore()
const inputText = ref('')
const textareaRef = ref(null)

const placeholder = computed(() => {
  if (store.pendingImage) return '描述图片或直接发送进行食材识别…'
  return '输入你想做的菜或食材…'
})

const canSend = computed(() =>
  !store.isStreaming && (inputText.value.trim() || store.pendingImage)
)

function autoResize() {
  const el = textareaRef.value
  if (!el) return
  el.style.height = 'auto'
  el.style.height = Math.min(el.scrollHeight, 160) + 'px'
}

function onImagePicked(e) {
  const file = e.target.files?.[0]
  if (file) {
    store.setPendingImage(file)
  }
  e.target.value = ''
}

async function onSend(e) {
  if (e) e.preventDefault()
  if (!canSend.value) return

  const text = inputText.value.trim()
  inputText.value = ''
  if (textareaRef.value) {
    textareaRef.value.style.height = 'auto'
  }

  await store.sendMessage(text)
}
</script>

<style scoped>
.input-area {
  padding: 16px 24px 20px;
  max-width: 720px;
  width: 100%;
  margin: 0 auto;
}

.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 8px;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  padding: 8px 12px;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-wrapper:focus-within {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(196, 149, 106, 0.12);
}

.btn-upload {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  color: var(--text-muted);
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: color 0.15s, background 0.15s;
  flex-shrink: 0;
}

.btn-upload:hover {
  color: var(--accent);
  background: var(--accent-light);
}

.text-input {
  flex: 1;
  border: none;
  outline: none;
  resize: none;
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-primary);
  background: transparent;
  padding: 4px 0;
  max-height: 160px;
}

.text-input::placeholder {
  color: var(--text-muted);
}

.text-input:disabled {
  opacity: 0.5;
}

.btn-send {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius-sm);
  background: var(--accent);
  color: #fff;
  flex-shrink: 0;
  transition: background 0.15s, opacity 0.15s;
}

.btn-send:hover:not(:disabled) {
  background: var(--accent-hover);
}

.btn-send:disabled {
  opacity: 0.35;
  cursor: not-allowed;
}

.input-hint {
  font-size: 11px;
  color: var(--text-muted);
  text-align: center;
  margin-top: 6px;
}
</style>
