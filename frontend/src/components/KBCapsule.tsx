import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, Check } from 'lucide-react'
import type { KnowledgeBase } from '../types'

const NAMES: Record<string, string> = {
  dongba: '东巴文化', puercha: '普洱茶', zharan: '扎染', huobajie: '火把节',
  poshuijie: '泼水节', kongquewu: '孔雀舞', naxiguyue: '纳西古乐',
  jianshuizitao: '建水紫陶', wutong: '乌铜走银', heqingyinqi: '鹤庆银器',
}

interface Props {
  kbs: KnowledgeBase[]
  currentKB: string
  onSwitch: (name: string) => void
}

export default function KBCapsule({ kbs, currentKB, onSwitch }: Props) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  return (
    <div ref={ref} className="relative inline-block">
      <motion.button
        whileHover={{ scale: 1.03 }}
        whileTap={{ scale: 0.97 }}
        onClick={() => setOpen(!open)}
        className="kb-capsule flex items-center gap-2 px-4 py-2 text-[13px]"
      >
        <span className="text-[var(--text-muted)]">知识库</span>
        <span className="font-medium" style={{ color: 'var(--text)' }}>{NAMES[currentKB] || currentKB}</span>
        <ChevronDown className={`w-3.5 h-3.5 text-[var(--text-muted)] transition-transform ${open ? 'rotate-180' : ''}`} />
      </motion.button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 8 }}
            transition={{ duration: 0.18 }}
            className="absolute top-full left-0 mt-2 w-52 glass py-1.5 z-50 max-h-64 overflow-y-auto"
            style={{ borderRadius: 20 }}
          >
            {kbs.map((kb) => (
              <button
                key={kb.name}
                onClick={() => { onSwitch(kb.name); setOpen(false) }}
                className="w-full flex items-center justify-between px-4 py-2.5 text-[13px] text-left hover:bg-[var(--blue-light)] transition-colors"
                style={{ color: 'var(--text)' }}
              >
                <span className="truncate">{NAMES[kb.name] || kb.name}</span>
                {kb.name === currentKB && <Check className="w-3.5 h-3.5 flex-shrink-0" style={{ color: '#7CB7FF' }} />}
              </button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}
