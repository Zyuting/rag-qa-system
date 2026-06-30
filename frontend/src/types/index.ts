export interface Source {
  filename: string
  source: string
  content: string
  score: number
}

export interface ChatResponse {
  answer: string
  sources: Source[]
  session_id: string
}

export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
  timestamp: string
  feedback?: 'like' | 'dislike'
}

export interface KnowledgeBase {
  name: string
  display_name: string
  indexed: boolean
  document_count?: number
}

export interface KBDocument {
  filename: string
  size: number
}

export interface HistorySession {
  session_id: string
  updated_at: string
  message_count: number
}

export interface HistoryMessage {
  id: number
  timestamp: string
  question: string
  answer: string
  score: number
  sources: Source[]
}
