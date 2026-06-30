const BASE = '/api'

async function request<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || `HTTP ${res.status}`)
  }
  return res.json()
}

// ── KB ──
export const getKBList = () =>
  request<{ knowledge_bases: import('../types').KnowledgeBase[]; total: number }>('/kb/list')

export const getKBInfo = (name: string) =>
  request<import('../types').KnowledgeBase & { documents: import('../types').KBDocument[] }>(`/kb/${name}/info`)

export const createKB = (name: string) =>
  request<{ status: string }>('/kb/create', { method: 'POST', body: JSON.stringify({ name }) })

export const deleteKB = (name: string) =>
  request<{ status: string }>(`/kb/${name}`, { method: 'DELETE' })

export const buildKB = (name: string) =>
  request<{ status: string; chunks: number; vectors: number }>(`/kb/build?kb_name=${encodeURIComponent(name)}`, { method: 'POST' })

export const uploadDocuments = async (kbName: string, files: FileList) => {
  const form = new FormData()
  for (let i = 0; i < files.length; i++) form.append('files', files[i])
  form.append('auto_rebuild', 'true')
  const res = await fetch(`${BASE}/kb/${kbName}/upload`, { method: 'POST', body: form })
  if (!res.ok) throw new Error((await res.json().catch(() => ({ detail: '' }))).detail)
  return res.json()
}

export const deleteDocument = (kbName: string, filename: string) =>
  request<{ status: string }>(`/kb/${kbName}/documents/${encodeURIComponent(filename)}?auto_rebuild=false`, { method: 'DELETE' })

// ── Chat ──
export const sendMessage = (question: string, knowledgeBase: string, sessionId: string) =>
  request<import('../types').ChatResponse>('/chat', {
    method: 'POST',
    body: JSON.stringify({ question, knowledge_base: knowledgeBase, session_id: sessionId }),
  })

// ── History ──
export const getHistory = (sessionId: string) =>
  request<{ session_id: string; messages: import('../types').HistoryMessage[]; total: number }>(`/history?session_id=${encodeURIComponent(sessionId)}`)

export const listSessions = () =>
  request<{ sessions: import('../types').HistorySession[] }>('/history/sessions')

export const clearHistory = (sessionId: string) =>
  request(`/history?session_id=${encodeURIComponent(sessionId)}`, { method: 'DELETE' })

export const deleteSession = (sessionId: string) =>
  request(`/history/sessions/${encodeURIComponent(sessionId)}`, { method: 'DELETE' })

// ── Feedback ──
export const sendFeedback = (messageId: string, type: 'like' | 'dislike') =>
  request('/feedback', { method: 'POST', body: JSON.stringify({ message_id: messageId, type }) })
