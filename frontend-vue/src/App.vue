<template>
  <div class="app-layout">
    <Sidebar />
    <main class="main-area">
      <ChatArea />
    </main>
  </div>
</template>

<script setup>
import Sidebar from './components/Sidebar.vue'
import ChatArea from './components/ChatArea.vue'
</script>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
  background: var(--bg-page);
}
</style>
