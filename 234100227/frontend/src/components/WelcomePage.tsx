import { motion } from 'framer-motion'
import KBCapsule from './KBCapsule'
import ChatInput from './ChatInput'
import type { KnowledgeBase } from '../types'

interface Props {
  kbs: KnowledgeBase[]
  currentKB: string
  onSwitchKB: (name: string) => void
  onSend: (text: string) => void
  isLoading: boolean
}

export default function WelcomePage({ kbs, currentKB, onSwitchKB, onSend, isLoading }: Props) {
  return (
    <div className="flex-1 flex flex-col items-center justify-center px-8 pb-32">
      {/* Yuti Logo */}
      <motion.h1
        initial={{ opacity: 0, y: -24 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
        className="select-none mb-5"
        style={{
          fontFamily: "'Cormorant Garamond', 'Georgia', 'Times New Roman', serif",
          fontSize: '64px',
          fontWeight: 500,
          letterSpacing: '0.12em',
          color: '#111827',
          lineHeight: 1.1,
        }}
      >
        Yuti
      </motion.h1>

      {/* Subtitle */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.15, duration: 0.5 }}
        className="text-[15px] mb-10"
        style={{ color: 'var(--text-muted)' }}
      >
        What do you want to learn today?
      </motion.p>

      {/* Input */}
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3, duration: 0.5 }}
        className="w-full max-w-2xl mb-5"
      >
        <ChatInput
          onSend={onSend}
          isLoading={isLoading}
          disabled={!currentKB}
          compact
        />
      </motion.div>

      {/* KB Capsule */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5, duration: 0.4 }}
      >
        <KBCapsule kbs={kbs} currentKB={currentKB} onSwitch={onSwitchKB} />
      </motion.div>
    </div>
  )
}
