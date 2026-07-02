import { useEffect } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { useChat } from './hooks/useChat'
import Sidebar from './components/Sidebar'
import WelcomePage from './components/WelcomePage'
import ChatView from './components/ChatView'
import ThemeToggle from './components/ThemeToggle'

export default function App() {
  const chat = useChat()

  useEffect(() => { chat.loadKBList() }, [])

  return (
    <div className="h-screen flex overflow-hidden">
      {/* Collapsed sidebar strip */}
      <Sidebar
        open={chat.sidebarOpen}
        onToggle={() => chat.setSidebarOpen(!chat.sidebarOpen)}
        kbs={chat.kbs}
        currentKB={chat.currentKB}
        onSwitchKB={chat.switchKB}
        onNewSession={chat.newSession}
        sessionId={chat.sessionId}
        onLoadSession={chat.loadSession}
        sessionTick={chat.sessionTick}
        onRefreshKB={chat.loadKBList}
      />

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0 relative">
        <AnimatePresence mode="wait">
          {chat.showWelcome ? (
            <motion.div
              key="welcome"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 flex flex-col"
            >
              <WelcomePage
                kbs={chat.kbs}
                currentKB={chat.currentKB}
                onSwitchKB={chat.switchKB}
                onSend={chat.sendMessage}
                isLoading={chat.isLoading}
              />
            </motion.div>
          ) : (
            <motion.div
              key="chat"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="flex-1 flex flex-col min-h-0"
            >
              <ChatView
                messages={chat.messages}
                isLoading={chat.isLoading}
                onSend={chat.sendMessage}
                onFeedback={chat.setFeedback}
                currentKB={chat.currentKB}
                kbs={chat.kbs}
                onSwitchKB={chat.switchKB}
              />
            </motion.div>
          )}
        </AnimatePresence>

        {/* Floating theme toggle — top right */}
        <div className="absolute top-4 right-4 z-30">
          <ThemeToggle />
        </div>
      </div>
    </div>
  )
}
