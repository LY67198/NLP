<template>
  <div class="ingredient-tags">
    <span class="tag-label">🍎 已识别</span>
    <span v-for="ing in result.ingredients" :key="ing" class="tag-item">{{ ing }}</span>
    <span :class="['tag-conf', result.confidence]">
      {{ result.confidence === 'high' ? '高置信度' : result.confidence === 'medium' ? '中置信度' : '低置信度' }}
    </span>
  </div>
</template>

<script setup>
defineProps({
  result: { type: Object, required: true }
})
</script>

<style scoped>
.ingredient-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  padding: 6px 12px;
  background: #e8f0e6;
  border: 1px solid #c8dcc6;
  border-radius: var(--radius-sm);
}

.tag-label {
  font-size: 12px;
  color: var(--text-secondary);
  margin-right: 2px;
}

.tag-item {
  font-size: 12px;
  padding: 2px 10px;
  background: var(--bg-input);
  border: 1px solid var(--border);
  border-radius: 12px;
  color: var(--text-primary);
}

.tag-conf {
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: auto;
}

.tag-conf.high { background: #e0ece3; color: #5c8a66; }
.tag-conf.medium { background: #f5f0e0; color: #b0954a; }
.tag-conf.low { background: #f5e5e5; color: #b0706b; }
</style>
