const API_BASE = '/api'

/**
 * Generic SSE stream reader.
 * Reads the response body as a stream of SSE events and invokes callbacks.
 */
async function fetchSSE(url, options, { onToken, onSessionId, onStatus, onDone, onError }) {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Accept': 'text/event-stream',
        ...options?.headers
      }
    })

    if (!response.ok) {
      const text = await response.text()
      throw new Error(text || `HTTP ${response.status}`)
    }

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const payload = line.slice(6).trim()
        if (!payload || payload === '[DONE]') continue

        try {
          const data = JSON.parse(payload)
          if (data.token) {
            onToken?.(data.token)
          } else if (data.sessionId) {
            onSessionId?.(data.sessionId)
          } else if (data.status) {
            onStatus?.(data.status)
          } else if (data.error) {
            onError?.(data.error)
          }
        } catch {
          // skip unparseable lines
        }
      }
    }

    // Drain remaining buffer
    if (buffer.startsWith('data: ')) {
      const payload = buffer.slice(6).trim()
      if (payload && payload !== '[DONE]') {
        try {
          const data = JSON.parse(payload)
          if (data.token) onToken?.(data.token)
          else if (data.sessionId) onSessionId?.(data.sessionId)
          else if (data.status) onStatus?.(data.status)
        } catch { /* ignore */ }
      }
    }

    onDone?.()
  } catch (err) {
    onError?.(err.message || 'Unknown error')
    onDone?.()
  }
}

/** POST /api/agent/chat — stream agent conversation, supports optional image */
export function agentChatStream({ sessionId, message, file, onToken, onSessionId, onStatus, onDone, onError }) {
  const formData = new FormData()
  formData.append('sessionId', sessionId)
  formData.append('message', message || '')
  if (file) {
    formData.append('file', file)
  }
  return fetchSSE(
    `${API_BASE}/agent/chat`,
    { method: 'POST', body: formData },
    { onToken, onSessionId, onStatus, onDone, onError }
  )
}

/** GET /api/rag/status — get RAG index status */
export async function getRagStatus() {
  const res = await fetch(`${API_BASE}/rag/status`)
  const json = await res.json()
  if (json.code !== 200) {
    throw new Error(json.message || '获取状态失败')
  }
  return json.data
}

/** DELETE /api/agent/clear/{sessionId} — clear agent session */
export async function clearSession(sessionId) {
  const res = await fetch(`${API_BASE}/agent/clear/${encodeURIComponent(sessionId)}`, {
    method: 'DELETE'
  })
  if (res.status === 204) return
  const text = await res.text()
  if (!text) return
  try {
    const json = JSON.parse(text)
    if (json.code !== 200 && json.code !== 404) {
      throw new Error(json.message || '清除会话失败')
    }
  } catch {
    // ignore parse errors for non-JSON responses
  }
}
