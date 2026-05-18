<template>
  <aside class="sidebar">
    <div class="sidebar-header">
      <h1 class="logo">🍳 SmartChef</h1>
      <p class="subtitle">智能厨房助手</p>
    </div>

    <button class="btn-new" @click="store.createSession()">
      <span class="icon">+</span> 新建对话
    </button>

    <div class="session-list">
      <div
        v-for="sess in store.sessionsList"
        :key="sess.id"
        :class="['session-item', { active: sess.id === store.activeSessionId }]"
        @click="store.switchSession(sess.id)"
      >
        <span class="session-name">{{ sess.name }}</span>
        <button
          class="btn-del"
          title="删除对话"
          @click.stop="store.deleteSession(sess.id)"
        >×</button>
      </div>
      <div v-if="store.sessionsList.length === 0" class="empty-hint">
        暂无对话，点击上方按钮开始
      </div>
    </div>

    <div class="sidebar-footer">
      <div class="rag-status">
        <div class="rag-label">菜谱知识库</div>
        <div class="rag-value">{{ store.ragTotalChunks }} 条菜谱</div>
        <div class="rag-bar">
          <div class="rag-fill" :style="{ width: Math.min(100, store.ragTotalChunks * 10) + '%' }"></div>
        </div>
      </div>
      <div class="tips">
        <p>💡 试试上传食材图片</p>
        <p>💡 可以问我菜谱做法</p>
      </div>
    </div>
  </aside>
</template>

<script setup>
import { onMounted } from 'vue'
import { useChatStore } from '../stores/chat.js'

const store = useChatStore()

onMounted(() => {
  store.fetchRagStatus()
})
</script>

<style scoped>
.sidebar {
  width: 260px;
  min-width: 260px;
  background: var(--bg-sidebar);
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--border-light);
  user-select: none;
}

.sidebar-header {
  padding: 24px 20px 16px;
}

.logo {
  font-size: 22px;
  font-weight: 700;
  color: var(--accent);
  letter-spacing: -0.5px;
}

.subtitle {
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 2px;
}

.btn-new {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  margin: 0 16px 16px;
  padding: 10px 0;
  background: var(--accent-light);
  color: var(--accent);
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 600;
  transition: background 0.2s;
}

.btn-new:hover {
  background: var(--accent);
  color: #fff;
}

.btn-new .icon {
  font-size: 18px;
  font-weight: 300;
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 12px;
}

.session-item {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.15s;
  margin-bottom: 2px;
}

.session-item:hover {
  background: var(--hover);
}

.session-item.active {
  background: var(--bg-card);
  box-shadow: var(--shadow-sm);
}

.session-name {
  flex: 1;
  font-size: 13px;
  color: var(--text-primary);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.btn-del {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  color: var(--text-muted);
  border-radius: 50%;
  font-size: 16px;
  opacity: 0;
  transition: opacity 0.15s, color 0.15s;
}

.session-item:hover .btn-del {
  opacity: 1;
}

.btn-del:hover {
  color: var(--danger);
  background: var(--bg-dialog);
}

.empty-hint {
  text-align: center;
  color: var(--text-muted);
  font-size: 13px;
  padding: 32px 16px;
}

.sidebar-footer {
  padding: 16px;
  border-top: 1px solid var(--border-light);
}

.rag-status {
  margin-bottom: 12px;
}

.rag-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.rag-value {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-primary);
  margin-bottom: 6px;
}

.rag-bar {
  height: 4px;
  background: var(--border);
  border-radius: 2px;
  overflow: hidden;
}

.rag-fill {
  height: 100%;
  background: var(--success);
  border-radius: 2px;
  transition: width 0.6s ease;
  min-width: 4px;
}

.tips {
  font-size: 11px;
  color: var(--text-muted);
  line-height: 1.8;
}
</style>
