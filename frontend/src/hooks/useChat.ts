import { useState, useCallback, useEffect } from 'react'
import type { Message, KnowledgeBase } from '../types'
import * as api from '../api'

const SESSION_KEY = 'yuti_session'

export function useChat() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [kbs, setKBs] = useState<KnowledgeBase[]>([])
  const [currentKB, setCurrentKB] = useState<string>('')
  const [sessionId, setSessionId] = useState<string>(() => localStorage.getItem(SESSION_KEY) || 'default')
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [showWelcome, setShowWelcome] = useState(true)
  const [sessionTick, setSessionTick] = useState(0)

  useEffect(() => { localStorage.setItem(SESSION_KEY, sessionId) }, [sessionId])

  const loadKBList = useCallback(async () => {
    try {
      const data = await api.getKBList()
      setKBs(data.knowledge_bases)
      if (!currentKB && data.knowledge_bases.length > 0) {
        const indexed = data.knowledge_bases.find((k) => k.indexed)
        setCurrentKB(indexed?.name || data.knowledge_bases[0].name)
      }
    } catch (e: any) {
      console.error('load KB list:', e)
    }
  }, [currentKB])

  const bump = useCallback(() => setSessionTick((n) => n + 1), [])

  const sendMessage = useCallback(async (question: string) => {
    if (!question.trim() || !currentKB || isLoading) return

    setShowWelcome(false)
    const userMsg: Message = { id: Date.now().toString(), role: 'user', content: question, timestamp: new Date().toISOString() }
    setMessages((prev) => [...prev, userMsg])
    setIsLoading(true)
    setError(null)

    try {
      const data = await api.sendMessage(question, currentKB, sessionId)
      const aiMsg: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: data.answer,
        sources: data.sources || [],
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, aiMsg])
      bump()  // 刷新侧栏
    } catch (e: any) {
      const errMsg = e.message || '请求失败'
      setError(errMsg)
      setMessages((prev) => [...prev, {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Error: ${errMsg}`,
        timestamp: new Date().toISOString(),
      }])
    } finally {
      setIsLoading(false)
    }
  }, [currentKB, isLoading, sessionId, bump])

  const switchKB = useCallback((name: string) => {
    setCurrentKB(name)
    setMessages([])
    setShowWelcome(true)
    setError(null)
  }, [])

  const newSession = useCallback(() => {
    const id = `s_${Date.now()}`
    setSessionId(id)
    setMessages([])
    setShowWelcome(true)
    setError(null)
    bump()  // 刷新侧栏
  }, [bump])

  const loadSession = useCallback(async (sid: string) => {
    try {
      const data = await api.getHistory(sid)
      const msgs: Message[] = (data.messages || []).flatMap((m) => [
        { id: `u_${m.id}`, role: 'user' as const, content: m.question, timestamp: m.timestamp },
        { id: `a_${m.id}`, role: 'assistant' as const, content: m.answer, sources: m.sources || [], timestamp: m.timestamp },
      ])
      setMessages(msgs)
      setSessionId(sid)
      setShowWelcome(false)
    } catch (e: any) {
      console.error('load session:', e)
    }
  }, [])

  const setFeedback = useCallback((msgId: string, type: 'like' | 'dislike') => {
    setMessages((prev) => prev.map((m) => m.id === msgId ? { ...m, feedback: type } : m))
    api.sendFeedback(msgId, type).catch(() => {})
  }, [])

  return {
    messages, isLoading, error, kbs, currentKB, sessionId,
    sidebarOpen, showWelcome, sessionTick,
    loadKBList, sendMessage, switchKB, newSession, loadSession,
    setSidebarOpen, setFeedback,
  }
}