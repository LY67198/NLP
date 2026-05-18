import { defineStore } from 'pinia'
import {
  agentChatStream,
  getRagStatus,
  clearSession as apiClearSession
} from '../api/client.js'

function genId() {
  return crypto.randomUUID ? crypto.randomUUID() : Date.now().toString(36) + Math.random().toString(36).slice(2)
}

export const useChatStore = defineStore('chat', {
  state: () => ({
    sessions: {},
    activeSessionId: null,
    ragTotalChunks: 0,
    pendingImage: null,        // { file, previewUrl }
    isStreaming: false,
  }),

  getters: {
    sessionsList(state) {
      return Object.values(state.sessions).sort((a, b) => b.updatedAt - a.updatedAt)
    },
    activeSession(state) {
      return state.activeSessionId ? state.sessions[state.activeSessionId] : null
    },
    activeMessages(state) {
      return state.activeSessionId ? state.sessions[state.activeSessionId]?.messages ?? [] : []
    }
  },

  actions: {
    createSession() {
      const id = genId()
      this.sessions[id] = {
        id,
        name: '新对话',
        messages: [],
        createdAt: Date.now(),
        updatedAt: Date.now()
      }
      this.activeSessionId = id
      this.pendingImage = null
      return id
    },

    ensureSession() {
      if (!this.activeSessionId || !this.sessions[this.activeSessionId]) {
        return this.createSession()
      }
      return this.activeSessionId
    },

    switchSession(id) {
      if (this.sessions[id]) {
        this.activeSessionId = id
        this.pendingImage = null
      }
    },

    async deleteSession(id) {
      try {
        await apiClearSession(id)
      } catch { /* ignore */ }
      delete this.sessions[id]
      if (this.activeSessionId === id) {
        const sorted = Object.values(this.sessions).sort((a, b) => b.updatedAt - a.updatedAt)
        this.activeSessionId = sorted.length > 0 ? sorted[0].id : null
        this.pendingImage = null
      }
    },

    setPendingImage(file) {
      if (this.pendingImage?.previewUrl) {
        URL.revokeObjectURL(this.pendingImage.previewUrl)
      }
      this.pendingImage = {
        file,
        previewUrl: URL.createObjectURL(file)
      }
    },

    clearPendingImage() {
      if (this.pendingImage?.previewUrl) {
        URL.revokeObjectURL(this.pendingImage.previewUrl)
      }
      this.pendingImage = null
    },

    _addMessage(sessionId, role, content, meta = {}) {
      const session = this.sessions[sessionId]
      if (!session) return null

      if (role === 'user' && session.name === '新对话') {
        session.name = content.slice(0, 30) || '新对话'
      }

      const msg = {
        id: genId(),
        role,
        content,
        meta,
        timestamp: Date.now()
      }
      session.messages.push(msg)
      session.updatedAt = Date.now()
      return msg
    },

    _updateLastAI(sessionId, token) {
      const session = this.sessions[sessionId]
      if (!session) return
      const msgs = session.messages
      if (msgs.length > 0 && msgs[msgs.length - 1].role === 'ai') {
        msgs[msgs.length - 1].content += token
      }
    },

    // Unified send: text / image / image+text all go through agentChatStream
    async sendMessage(text) {
      const sid = this.ensureSession()
      const hasImage = !!this.pendingImage

      if (!text && !hasImage) return

      // Build user message for display
      const displayText = text || '帮我看看这是什么食材'
      this._addMessage(sid, 'user', displayText, {
        type: hasImage ? 'vision' : 'text',
        imageUrl: hasImage ? this.pendingImage.previewUrl : undefined
      })

      this._addMessage(sid, 'ai', '', { type: 'text' })
      this.isStreaming = true

      const file = hasImage ? this.pendingImage.file : null

      try {
        await new Promise((resolve) => {
          agentChatStream({
            sessionId: sid,
            message: text,
            file,
            onToken: (token) => this._updateLastAI(sid, token),
            onSessionId: () => {},
            onDone: resolve,
            onError: (err) => {
              this._updateLastAI(sid, `[错误] ${err}`)
              resolve()
            }
          })
        })
      } finally {
        this.isStreaming = false
        this.clearPendingImage()
      }
    },

    async fetchRagStatus() {
      try {
        const data = await getRagStatus()
        this.ragTotalChunks = data.total_chunks ?? 0
      } catch {
        this.ragTotalChunks = 0
      }
    }
  }
})
