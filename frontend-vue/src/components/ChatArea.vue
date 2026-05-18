<template>
  <div class="chat-area" ref="scrollContainer">
    <div class="messages-wrapper">
      <!-- Welcome card when no messages -->
      <WelcomeCard
        v-if="!store.activeSessionId || store.activeMessages.length === 0"
        @select-prompt="onPromptSelect"
      />

      <!-- Message list -->
      <template v-else>
        <div class="messages-list">
          <MessageBubble
            v-for="msg in store.activeMessages"
            :key="msg.id"
            :message="msg"
            :is-user="msg.role === 'user'"
          />

        </div>

        <!-- Streaming indicator -->
        <div v-if="store.isStreaming" class="streaming-dot">
          <span></span><span></span><span></span>
        </div>
      </template>
    </div>

    <!-- Image preview + ingredient tags -->
    <div v-if="store.pendingImage" class="context-bar">
      <ImagePreview />
    </div>

    <!-- Input -->
    <ChatInput />
  </div>
</template>

<script setup>
import { watch, nextTick, ref } from 'vue'
import { useChatStore } from '../stores/chat.js'
import MessageBubble from './MessageBubble.vue'
import WelcomeCard from './WelcomeCard.vue'
import ChatInput from './ChatInput.vue'
import ImagePreview from './ImagePreview.vue'

const store = useChatStore()
const scrollContainer = ref(null)

function scrollToBottom() {
  nextTick(() => {
    const el = scrollContainer.value
    if (el) {
      el.scrollTop = el.scrollHeight
    }
  })
}

watch(
  () => store.activeMessages.length,
  () => scrollToBottom()
)

function onPromptSelect(prompt) {
  store.sendMessage(prompt)
}

// Scroll on streaming content updates
watch(
  () => {
    const msgs = store.activeMessages
    if (msgs.length === 0) return ''
    const last = msgs[msgs.length - 1]
    return last.role === 'ai' ? last.content : ''
  },
  () => scrollToBottom()
)
</script>

<style scoped>
.chat-area {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.messages-wrapper {
  flex: 1;
  overflow-y: auto;
  padding: 24px 0;
}

.messages-list {
  max-width: 720px;
  margin: 0 auto;
  padding: 0 24px;
}

.streaming-dot {
  display: flex;
  gap: 4px;
  padding: 8px 24px;
  max-width: 720px;
  margin: 0 auto;
}

.streaming-dot span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--accent);
  animation: bounce 1.2s infinite ease-in-out both;
}

.streaming-dot span:nth-child(1) { animation-delay: -0.32s; }
.streaming-dot span:nth-child(2) { animation-delay: -0.16s; }
.streaming-dot span:nth-child(3) { animation-delay: 0s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0.4); opacity: 0.5; }
  40% { transform: scale(1); opacity: 1; }
}

.context-bar {
  padding: 8px 24px;
  max-width: 720px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
</style>
