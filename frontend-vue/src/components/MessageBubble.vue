<template>
  <div :class="['bubble-row', { user: isUser }]">
    <div class="bubble">
      <!-- Image for vision messages -->
      <img
        v-if="message.meta?.imageUrl"
        :src="message.meta.imageUrl"
        class="msg-image"
        alt="上传的图片"
      />

      <!-- Recipe selection label -->
      <div v-if="message.meta?.type === 'recipe_select'" class="recipe-select-label">
        📖 选择了菜谱：<strong>{{ message.meta.recipeName }}</strong>
      </div>

      <!-- Ingredient tags for vision recognition -->
      <div v-if="message.meta?.ingredients && !isUser" class="rec-tags">
        <span class="rec-label">识别食材</span>
        <span v-for="ing in message.meta.ingredients" :key="ing" class="rec-tag">{{ ing }}</span>
        <span v-if="message.meta.confidence" :class="['confidence', message.meta.confidence]">
          {{ confidenceText(message.meta.confidence) }}
        </span>
      </div>

      <!-- Selected recipe badge on AI messages -->
      <div v-if="message.meta?.selectedRecipe" class="selected-recipe-badge">
        📖 菜谱：{{ message.meta.selectedRecipe }}
      </div>

      <!-- Message text -->
      <div class="msg-content" v-text="message.content"></div>

      <!-- Source badges -->
      <div v-if="message.meta?.sources?.length" class="sources">
        <span v-for="src in message.meta.sources" :key="src" :class="['badge', badgeClass(src)]">
          {{ src }}
        </span>
      </div>

      <!-- Timestamp -->
      <div class="msg-time">{{ formatTime(message.timestamp) }}</div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  message: { type: Object, required: true },
  isUser: { type: Boolean, default: false }
})

function confidenceText(c) {
  const map = { high: '高置信度', medium: '中等置信度', low: '低置信度' }
  return map[c] || c
}

function badgeClass(src) {
  if (src.includes('菜谱')) return 'badge-local'
  if (src.includes('网络')) return 'badge-web'
  if (src.includes('识别') || src.includes('图片')) return 'badge-vision'
  return ''
}

function formatTime(ts) {
  const d = new Date(ts)
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  return `${h}:${m}`
}
</script>

<style scoped>
.bubble-row {
  display: flex;
  margin-bottom: 20px;
}

.bubble-row.user {
  justify-content: flex-end;
}

.bubble {
  max-width: 80%;
  padding: 14px 18px;
  border-radius: var(--radius-md);
  position: relative;
}

.bubble-row:not(.user) .bubble {
  background: var(--bg-dialog);
  border: 1px solid var(--border-light);
  border-bottom-left-radius: 4px;
}

.bubble-row.user .bubble {
  background: var(--accent-light);
  border-bottom-right-radius: 4px;
}

.msg-image {
  max-width: 240px;
  max-height: 180px;
  border-radius: var(--radius-sm);
  margin-bottom: 10px;
  object-fit: cover;
}

.rec-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  margin-bottom: 10px;
  padding: 8px 10px;
  background: var(--bg-card);
  border-radius: var(--radius-sm);
}

.rec-label {
  font-size: 11px;
  color: var(--text-secondary);
  margin-right: 2px;
}

.rec-tag {
  font-size: 12px;
  padding: 2px 10px;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 12px;
  color: var(--text-primary);
}

.confidence {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: auto;
}

.confidence.high { background: #e0ece3; color: #5c8a66; }
.confidence.medium { background: #f5f0e0; color: #b0954a; }
.confidence.low { background: #f5e5e5; color: #b0706b; }

.msg-content {
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary);
  white-space: pre-wrap;
  word-break: break-word;
}

.sources {
  display: flex;
  gap: 6px;
  margin-top: 10px;
  flex-wrap: wrap;
}

.badge {
  font-size: 11px;
  padding: 3px 10px;
  border-radius: 10px;
  font-weight: 500;
}

.badge-local {
  background: #e0ece3;
  color: #5c8a66;
}

.badge-web {
  background: #e2e5f0;
  color: #5a6a8c;
}

.badge-vision {
  background: #efe0e8;
  color: #8c5a7a;
}

.recipe-select-label {
  font-size: 13px;
  color: var(--accent);
  margin-bottom: 6px;
  padding: 6px 10px;
  background: #fdf8f2;
  border-radius: var(--radius-sm);
  border: 1px solid var(--accent-light);
}

.selected-recipe-badge {
  font-size: 12px;
  color: var(--accent);
  margin-bottom: 8px;
  padding: 6px 10px;
  background: #fdf8f2;
  border-radius: var(--radius-sm);
  border: 1px solid var(--accent-light);
}

.msg-time {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 6px;
  text-align: right;
}
</style>
