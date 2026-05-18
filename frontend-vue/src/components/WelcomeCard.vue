<template>
  <div class="welcome">
    <div class="welcome-card">
      <div class="welcome-emoji">🍳</div>
      <h2>欢迎使用 SmartChef</h2>
      <p class="welcome-desc">
        我是你的智能厨房助手，可以帮你识别食材、推荐菜谱、解答烹饪问题
      </p>

      <div class="features">
        <div class="feature-item">
          <span class="f-icon">📸</span>
          <span>上传食材图片自动识别</span>
        </div>
        <div class="feature-item">
          <span class="f-icon">🔍</span>
          <span>智能搜索海量菜谱库</span>
        </div>
        <div class="feature-item">
          <span class="f-icon">💬</span>
          <span>对话式烹饪指导</span>
        </div>
      </div>

      <div class="example-prompts">
        <p class="ex-hint">试试这样问我：</p>
        <button
          v-for="p in prompts"
          :key="p"
          class="ex-btn"
          @click="$emit('selectPrompt', p)"
        >
          {{ p }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
defineEmits(['selectPrompt'])
const prompts = [
  '西红柿炒鸡蛋怎么做？',
  '冰箱里有鸡胸肉和青椒，能做什么菜？',
  '推荐几道适合新手的家常菜'
]
</script>

<style scoped>
.welcome {
  display: flex;
  justify-content: center;
  padding: 48px 24px;
}

.welcome-card {
  text-align: center;
  max-width: 480px;
  padding: 40px 36px;
  background: var(--bg-dialog);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

.welcome-emoji {
  font-size: 56px;
  margin-bottom: 12px;
}

h2 {
  font-size: 22px;
  font-weight: 700;
  color: var(--text-primary);
  margin-bottom: 8px;
}

.welcome-desc {
  font-size: 14px;
  color: var(--text-secondary);
  line-height: 1.7;
  margin-bottom: 24px;
}

.features {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 28px;
  text-align: left;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--text-secondary);
  padding: 8px 14px;
  background: var(--bg-card);
  border-radius: var(--radius-sm);
}

.f-icon {
  font-size: 18px;
}

.ex-hint {
  font-size: 12px;
  color: var(--text-muted);
  margin-bottom: 10px;
}

.example-prompts {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.ex-btn {
  display: block;
  width: 100%;
  padding: 10px 16px;
  background: var(--bg-card);
  border: 1px solid var(--border-light);
  border-radius: var(--radius-sm);
  font-size: 13px;
  color: var(--text-primary);
  text-align: left;
  transition: background 0.15s, border-color 0.15s;
}

.ex-btn:hover {
  background: var(--hover);
  border-color: var(--accent);
}
</style>
