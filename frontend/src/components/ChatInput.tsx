import { useState, useRef, useCallback, KeyboardEvent } from 'react'
import { motion } from 'framer-motion'
import { ArrowUp, Loader2 } from 'lucide-react'

interface Props {
  onSend: (text: string) => void
  isLoading: boolean
  disabled: boolean
  compact?: boolean
}

export default function ChatInput({ onSend, isLoading, disabled, compact }: Props) {
  const [value, setValue] = useState('')
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleSend = useCallback(() => {
    const text = value.trim()
    if (!text || isLoading || disabled) return
    onSend(text)
    setValue('')
    if (textareaRef.current) textareaRef.current.style.height = 'auto'
  }, [value, isLoading, disabled, onSend])

  const handleKeyDown = (e: KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleSend() }
  }

  const handleInput = () => {
    const el = textareaRef.current
    if (el) { el.style.height = 'auto'; el.style.height = Math.min(el.scrollHeight, 160) + 'px' }
  }

  return (
    <div className={`input-glass flex items-end gap-3 px-5 py-4 ${compact ? 'max-w-2xl w-full mx-auto' : 'mx-4 mb-3'}`}>
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => { setValue(e.target.value); handleInput() }}
        onKeyDown={handleKeyDown}
        placeholder={disabled ? '请先选择知识库...' : '向 Yuti 提问...'}
        rows={1}
        disabled={disabled || isLoading}
        className="flex-1 resize-none bg-transparent text-[15px] py-1 px-1 max-h-[160px] focus:outline-none disabled:opacity-30 placeholder:text-[var(--text-muted)]"
        style={{ color: 'var(--text)' }}
      />
      <motion.button
        whileHover={{ scale: 1.03 }}
        whileTap={{ scale: 0.97 }}
        onClick={handleSend}
        disabled={!value.trim() || isLoading || disabled}
        className="w-10 h-10 rounded-full flex items-center justify-center flex-shrink-0 transition-all"
        style={{
          background: (!value.trim() || isLoading || disabled) ? 'var(--glass-bg)' : '#7CB7FF',
          color: (!value.trim() || isLoading || disabled) ? 'var(--text-muted)' : '#fff',
          boxShadow: (!value.trim() || isLoading || disabled) ? 'none' : '0 2px 12px rgba(124,183,255,0.25)',
        }}
      >
        {isLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <ArrowUp className="w-5 h-5" />}
      </motion.button>
    </div>
  )
}
