import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Sun, Moon } from 'lucide-react'

export default function ThemeToggle() {
  const [dark, setDark] = useState(() => localStorage.getItem('yuti-theme') === 'dark')

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark)
    localStorage.setItem('yuti-theme', dark ? 'dark' : 'light')
  }, [dark])

  return (
    <motion.button
      whileHover={{ scale: 1.03 }}
      whileTap={{ scale: 0.97 }}
      onClick={() => setDark(!dark)}
      className="w-9 h-9 glass flex items-center justify-center"
      title={dark ? '浅色模式' : '深色模式'}
    >
      {dark ? <Sun className="w-4 h-4" style={{ color: 'var(--text-muted)' }} /> : <Moon className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />}
    </motion.button>
  )
}
