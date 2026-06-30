import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import ChatBubble from './ChatBubble'
import ChatInput from './ChatInput'
import KBCapsule from './KBCapsule'
import type { Message, KnowledgeBase } from '../types'

interface Props {
  messages: Message[]
  isLoading: boolean
  onSend: (text: string) => void
  onFeedback: (msgId: string, type: 'like' | 'dislike') => void
  currentKB: string
  kbs: KnowledgeBase[]
  onSwitchKB: (name: string) => void
}

export default function ChatView({ messages, isLoading, onSend, onFeedback, currentKB, kbs, onSwitchKB }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, isLoading])

  return (
    <>
      {/* Top: KB indicator */}
      <div className="flex items-center justify-center py-3">
        <KBCapsule kbs={kbs} currentKB={currentKB} onSwitch={onSwitchKB} />
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto py-4">
        {messages.map((msg) => (
          <ChatBubble key={msg.id} message={msg} onFeedback={onFeedback} />
        ))}

        {/* Loading */}
        {isLoading && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="px-6 py-3">
            <div className="flex items-center gap-3 px-5 py-3 glass" style={{ borderRadius: 20, maxWidth: 'fit-content' }}>
              <span className="text-[14px]" style={{ color: 'var(--text-muted)' }}>Yuti 思考中</span>
              <span className="w-1.5 h-1.5 rounded-full dot-pulse" style={{ background: '#7CB7FF' }} />
              <span className="w-1.5 h-1.5 rounded-full dot-pulse" style={{ background: '#7CB7FF' }} />
              <span className="w-1.5 h-1.5 rounded-full dot-pulse" style={{ background: '#7CB7FF' }} />
            </div>
          </motion.div>
        )}

        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <ChatInput onSend={onSend} isLoading={isLoading} disabled={!currentKB} />
    </>
  )
}
