import { motion } from 'framer-motion'
import type { KnowledgeBase } from '../types'

const KB_NAMES: Record<string, string> = {
  dongba: '东巴文化', puercha: '普洱茶', zharan: '扎染', huobajie: '火把节',
  poshuijie: '泼水节', kongquewu: '孔雀舞', naxiguyue: '纳西古乐',
  jianshuizitao: '建水紫陶', wutong: '乌铜走银', heqingyinqi: '鹤庆银器',
}

interface Props {
  currentKB: string
  kbs: KnowledgeBase[]
  onClear: () => void
}

export default function Header({ currentKB, kbs, onClear }: Props) {
  return (
    <motion.header
      initial={{ y: -60 }}
      animate={{ y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="glass mx-4 mt-3 px-6 py-3 flex items-center justify-between z-20"
    >
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full flex items-center justify-center"
          style={{ background: '#7CB7FF' }}>
          <span className="text-[14px] font-medium text-white select-none">Y</span>
        </div>
        <span className="text-[15px] font-medium" style={{ color: 'var(--text)' }}>Yuti</span>
        {currentKB && (
          <span className="text-[12px] px-2.5 py-1 rounded-full ml-1"
            style={{ background: '#DCEBFF', color: '#7CB7FF' }}>
            {KB_NAMES[currentKB] || currentKB}
          </span>
        )}
      </div>
    </motion.header>
  )
}
