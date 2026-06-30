import { useState } from 'react'
import { motion } from 'framer-motion'
import ReactMarkdown from 'react-markdown'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { Copy, Check, ThumbsUp, ThumbsDown, ChevronDown, ChevronUp } from 'lucide-react'
import type { Message } from '../types'

interface Props {
  message: Message
  onFeedback?: (msgId: string, type: 'like' | 'dislike') => void
}

export default function ChatBubble({ message, onFeedback }: Props) {
  const [copied, setCopied] = useState(false)
  const [showSources, setShowSources] = useState(false)
  const isUser = message.role === 'user'

  const handleCopy = async (text: string) => {
    await navigator.clipboard.writeText(text)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: 'easeOut' }}
      className={`flex ${isUser ? 'justify-end' : 'justify-start'} px-6 mb-5`}
    >
      <div className={isUser ? 'bubble-user' : 'bubble-ai'}>
        {isUser ? (
          <p className="whitespace-pre-wrap">{message.content}</p>
        ) : (
          <>
            <div className="markdown">
              <ReactMarkdown
                components={{
                  code({ className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '')
                    const codeStr = String(children).replace(/\n$/, '')
                    const isInline = !match && !codeStr.includes('\n')
                    if (isInline) return <code {...props}>{children}</code>
                    return (
                      <div className="relative group/code my-3">
                        <div className="flex items-center justify-between px-4 py-2 rounded-t-xl" style={{ background: '#334155' }}>
                          <span className="text-[11px] text-slate-300">{match?.[1] || 'code'}</span>
                          <button onClick={() => handleCopy(codeStr)} className="text-slate-300 hover:text-white transition-colors">
                            {copied ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                          </button>
                        </div>
                        <SyntaxHighlighter style={oneDark} language={match?.[1] || 'text'} PreTag="div" className="!my-0 !rounded-t-none !rounded-b-xl">
                          {codeStr}
                        </SyntaxHighlighter>
                      </div>
                    )
                  },
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>

            {/* Bottom bar */}
            <div className="flex items-center gap-2 mt-3 pt-2" style={{ borderTop: '1px solid rgba(0,0,0,0.04)' }}>
              <button onClick={() => onFeedback?.(message.id, 'like')} className={`flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[12px] transition-colors ${message.feedback === 'like' ? '' : ''}`}
                style={{ color: message.feedback === 'like' ? '#7CB7FF' : 'var(--text-muted)' }}>
                <ThumbsUp className={`w-3.5 h-3.5 ${message.feedback === 'like' ? 'fill-[#7CB7FF]' : ''}`} />
              </button>
              <button onClick={() => onFeedback?.(message.id, 'dislike')} className={`flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[12px] transition-colors ${message.feedback === 'dislike' ? '' : ''}`}
                style={{ color: message.feedback === 'dislike' ? '#EF4444' : 'var(--text-muted)' }}>
                <ThumbsDown className={`w-3.5 h-3.5 ${message.feedback === 'dislike' ? 'fill-[#EF4444]' : ''}`} />
              </button>
              <button onClick={() => handleCopy(message.content)} className="flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[12px]" style={{ color: 'var(--text-muted)' }}>
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-500" /> : <Copy className="w-3.5 h-3.5" />}
              </button>

              {message.sources && message.sources.length > 0 && (
                <>
                  <div className="w-px h-4" style={{ background: 'rgba(0,0,0,0.06)' }} />
                  <button onClick={() => setShowSources(!showSources)} className="flex items-center gap-1 px-1.5 py-0.5 rounded-md text-[12px]"
                    style={{ color: '#7CB7FF' }}>
                    {showSources ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    参考来源 ({message.sources.length})
                  </button>
                </>
              )}
            </div>

            {/* Expandable sources */}
            {showSources && message.sources && message.sources.length > 0 && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                transition={{ duration: 0.25 }}
                className="mt-3 space-y-2 pt-3 overflow-hidden"
                style={{ borderTop: '1px solid rgba(0,0,0,0.04)' }}
              >
                {message.sources.map((src, i) => (
                  <motion.div
                    key={i}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: i * 0.04 }}
                    className="p-3 rounded-xl"
                    style={{ background: 'var(--glass-bg)', border: '1px solid var(--glass-border)' }}
                  >
                    <div className="flex items-center justify-between mb-1.5">
                      <span className="text-[12px] font-medium truncate pr-2" style={{ color: 'var(--text)' }}>{src.filename}</span>
                      <span className="text-[11px] px-2 py-0.5 rounded-full flex-shrink-0" style={{ background: '#DCEBFF', color: '#7CB7FF' }}>{(src.score * 100).toFixed(0)}%</span>
                    </div>
                    <div className="w-full h-0.5 rounded-full mb-1.5" style={{ background: 'rgba(0,0,0,0.04)' }}>
                      <div className="h-full rounded-full" style={{ width: `${Math.min(src.score * 100, 100)}%`, background: '#7CB7FF', opacity: 0.5 }} />
                    </div>
                    <p className="text-[12px] leading-relaxed line-clamp-4" style={{ color: 'var(--text-muted)' }}>{src.content}</p>
                  </motion.div>
                ))}
              </motion.div>
            )}
          </>
        )}
      </div>
    </motion.div>
  )
}
