import { useState, useCallback, useEffect, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  PanelLeftOpen, PanelLeftClose, Plus, MoreHorizontal, Upload, Trash2, Zap,
  X, FileText, MessageSquare, ChevronDown, ChevronRight, BookOpen, Clock
} from 'lucide-react'
import type { KnowledgeBase, KBDocument, HistorySession } from '../types'
import * as api from '../api'

const NAMES: Record<string, string> = {
  dongba: '东巴文化', puercha: '普洱茶', zharan: '扎染', huobajie: '火把节',
  poshuijie: '泼水节', kongquewu: '孔雀舞', naxiguyue: '纳西古乐',
  jianshuizitao: '建水紫陶', wutong: '乌铜走银', heqingyinqi: '鹤庆银器',
}

interface Props {
  open: boolean
  onToggle: () => void
  kbs: KnowledgeBase[]
  currentKB: string
  onSwitchKB: (name: string) => void
  onNewSession: () => void
  sessionId: string
  onLoadSession: (sid: string) => void
  sessionTick: number
  onRefreshKB: () => void
}

// ══════════════════════════════════════
// KB 单项 — 可展开文档列表
// ══════════════════════════════════════
function KBItem({
  kb, currentKB, onSwitch, onRefresh,
}: {
  kb: KnowledgeBase
  currentKB: string
  onSwitch: (name: string) => void
  onRefresh: () => void
}) {
  const [expanded, setExpanded] = useState(false)
  const [docs, setDocs] = useState<KBDocument[]>([])
  const [menuOpen, setMenuOpen] = useState(false)
  const [showUpload, setShowUpload] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)
  const [dragOver, setDragOver] = useState(false)

  const loadDocs = useCallback(async () => {
    try { const info = await api.getKBInfo(kb.name); setDocs(info.documents || []) }
    catch { setDocs([]) }
  }, [kb.name])

  const handleUpload = async (files: FileList) => {
    try { await api.uploadDocuments(kb.name, files); await loadDocs(); setShowUpload(false); onRefresh() }
    catch (e: any) { alert('上传失败: ' + e.message) }
  }

  const handleDeleteDoc = async (filename: string) => {
    if (!confirm(`删除 ${filename}?`)) return
    try { await api.deleteDocument(kb.name, filename); await loadDocs(); onRefresh() }
    catch (e: any) { alert('删除失败: ' + e.message) }
  }

  const handleDeleteKB = async () => {
    if (!confirm(`确认删除知识库「${NAMES[kb.name] || kb.name}」?`)) return
    try { await api.deleteKB(kb.name); onRefresh() }
    catch (e: any) { alert('删除失败: ' + e.message) }
  }

  const handleBuild = async () => {
    try { const res = await api.buildKB(kb.name); alert(`索引构建完成: ${res.chunks} chunks, ${res.vectors} vectors`); onRefresh() }
    catch (e: any) { alert('构建失败: ' + e.message) }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault(); setDragOver(false)
    if (e.dataTransfer.files.length) handleUpload(e.dataTransfer.files)
  }

  const isActive = currentKB === kb.name

  return (
    <div>
      {/* ── KB name row ── */}
      <div
        className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg cursor-pointer transition-all group text-[13px] ${isActive ? '' : 'hover:bg-[var(--bg-card-hover)]'}`}
        style={isActive ? { background: 'var(--primary-light)', color: 'var(--primary)', fontWeight: 500 } : { color: 'var(--text)' }}
      >
        <button
          onClick={(e) => { e.stopPropagation(); setExpanded(!expanded); if (!expanded) loadDocs() }}
          className="p-0.5 rounded hover:bg-[var(--bg-card)] flex-shrink-0"
        >
          {expanded ? <ChevronDown className="w-3 h-3" /> : <ChevronRight className="w-3 h-3" />}
        </button>
        <span className="flex-1 truncate" onClick={() => onSwitch(kb.name)}>
          {NAMES[kb.name] || kb.name}
        </span>
        {!kb.indexed && (
          <span className="text-[10px] px-1.5 py-0.5 rounded-full flex-shrink-0" style={{ background: 'var(--bg-card)', color: 'var(--text-muted)' }}>未索引</span>
        )}
        {/* ··· menu */}
        <div className="relative">
          <button
            onClick={(e) => { e.stopPropagation(); setMenuOpen(!menuOpen) }}
            className="p-0.5 rounded opacity-0 group-hover:opacity-100 hover:bg-[var(--bg-card)] transition-opacity flex-shrink-0"
          >
            <MoreHorizontal className="w-3 h-3" />
          </button>
          {menuOpen && (
            <>
              <div className="fixed inset-0 z-20" onClick={() => setMenuOpen(false)} />
              <div className="absolute right-0 top-full mt-1 w-36 z-30 glass py-1" style={{ borderRadius: 12 }}>
                <button onClick={(e) => { e.stopPropagation(); setMenuOpen(false); setShowUpload(true) }} className="w-full flex items-center gap-2 px-3 py-1.5 text-[12px] hover:bg-[var(--primary-light)]" style={{ color: 'var(--text)' }}>
                  <Upload className="w-3 h-3" /> 上传文档
                </button>
                <button onClick={(e) => { e.stopPropagation(); setMenuOpen(false); handleBuild() }} className="w-full flex items-center gap-2 px-3 py-1.5 text-[12px] hover:bg-[var(--primary-light)]" style={{ color: 'var(--text)' }}>
                  <Zap className="w-3 h-3" /> 构建索引
                </button>
                <button onClick={(e) => { e.stopPropagation(); setMenuOpen(false); handleDeleteKB() }} className="w-full flex items-center gap-2 px-3 py-1.5 text-[12px] hover:bg-red-50 dark:hover:bg-red-500/10" style={{ color: '#e05555' }}>
                  <Trash2 className="w-3 h-3" /> 删除知识库
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* ── Expanded: doc list ── */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.18 }}
            className="overflow-hidden ml-4 pl-2"
            style={{ borderLeft: '1px solid var(--border)' }}
          >
            <div className="py-1 space-y-0.5">
              {docs.map((doc) => (
                <div key={doc.filename} className="flex items-center gap-1.5 px-2 py-1 rounded-md hover:bg-[var(--bg-card)] group/doc text-[11px]">
                  <FileText className="w-3 h-3 flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
                  <span className="flex-1 truncate" style={{ color: 'var(--text)' }}>{doc.filename}</span>
                  <span className="text-[10px] flex-shrink-0" style={{ color: 'var(--text-muted)' }}>{Math.round(doc.size / 1024)}KB</span>
                  <button onClick={() => handleDeleteDoc(doc.filename)} className="opacity-0 group-hover/doc:opacity-100 p-0.5 rounded hover:bg-red-50 flex-shrink-0 transition-opacity">
                    <X className="w-3 h-3" style={{ color: '#e05555' }} />
                  </button>
                </div>
              ))}
              {docs.length === 0 && <div className="text-[10px] px-2 py-1" style={{ color: 'var(--text-muted)' }}>暂无文档</div>}
              <button onClick={() => setShowUpload(true)} className="flex items-center gap-1.5 px-2 py-1 rounded-md hover:bg-[var(--bg-card)] text-[11px] w-full" style={{ color: 'var(--text-muted)' }}>
                <Upload className="w-3 h-3" /> 上传文档
              </button>
              <button onClick={handleBuild} className="flex items-center gap-1.5 px-2 py-1 rounded-md hover:bg-[var(--bg-card)] text-[11px] w-full" style={{ color: 'var(--primary)' }}>
                <Zap className="w-3 h-3" /> 构建索引
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Upload modal ── */}
      <AnimatePresence>
        {showUpload && (
          <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: 'rgba(0,0,0,0.25)', backdropFilter: 'blur(4px)' }} onClick={() => setShowUpload(false)}>
            <motion.div initial={{ scale: 0.94, opacity: 0 }} animate={{ scale: 1, opacity: 1 }} exit={{ scale: 0.94, opacity: 0 }} onClick={(e) => e.stopPropagation()} className="glass w-[420px] max-w-[90vw] p-6" style={{ borderRadius: 20 }}>
              <div className="flex items-center justify-between mb-5">
                <h3 className="font-medium text-[14px]" style={{ color: 'var(--text)' }}>上传文档 · {NAMES[kb.name] || kb.name}</h3>
                <button onClick={() => setShowUpload(false)} className="p-1.5 rounded-lg hover:bg-[var(--bg-card)]"><X className="w-4 h-4" style={{ color: 'var(--text-muted)' }} /></button>
              </div>
              <div
                onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
                onDragLeave={() => setDragOver(false)}
                onDrop={handleDrop}
                onClick={() => fileRef.current?.click()}
                className="border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all mb-4"
                style={{ borderColor: dragOver ? 'var(--primary)' : 'var(--border)', background: dragOver ? 'var(--primary-light)' : 'var(--bg-card)' }}
              >
                <Upload className="w-6 h-6 mx-auto mb-2" style={{ color: 'var(--text-muted)' }} />
                <p className="text-[13px] mb-1" style={{ color: 'var(--text)' }}>拖拽文件或点击选择</p>
                <p className="text-[11px]" style={{ color: 'var(--text-muted)' }}>支持 TXT / PDF / DOCX / MD / HTML</p>
              </div>
              <input ref={fileRef} type="file" multiple accept=".txt,.pdf,.docx,.md,.html" className="hidden" onChange={(e) => e.target.files && handleUpload(e.target.files)} />
              <p className="text-[11px] text-center" style={{ color: 'var(--text-muted)' }}>上传后将自动构建向量索引（约30秒）</p>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

// ══════════════════════════════════════
// Main Sidebar
// ══════════════════════════════════════
export default function Sidebar({ open, onToggle, kbs, currentKB, onSwitchKB, onNewSession, sessionId, onLoadSession, sessionTick, onRefreshKB }: Props) {
  const [newKBInput, setNewKBInput] = useState(false)
  const [newKBName, setNewKBName] = useState('')
  const [sessions, setSessions] = useState<HistorySession[]>([])
  const [kbExpanded, setKbExpanded] = useState(true)   // 知识库区域折叠
  const [refreshKey, setRefreshKey] = useState(0)

  const refresh = () => { setRefreshKey((k) => k + 1); onRefreshKB() }

  // 加载最近聊天列表
  const loadSessions = useCallback(async () => {
    try { const data = await api.listSessions(); setSessions(data.sessions || []) }
    catch {}
  }, [])

  // 展开时加载 + sessionTick 变化时刷新
  useEffect(() => {
    if (open) loadSessions()
  }, [open, sessionTick, loadSessions])

  const handleCreateKB = async () => {
    if (!newKBName.trim()) return
    try { await api.createKB(newKBName.trim()); setNewKBInput(false); setNewKBName(''); refresh() }
    catch (e: any) { alert('创建失败: ' + e.message) }
  }

  const handleDeleteSession = async (sid: string) => {
    if (!confirm('删除此对话记录?')) return
    try { await api.deleteSession(sid); loadSessions() }
    catch (e: any) { alert('删除失败: ' + e.message) }
  }

  // 折叠态
  if (!open) {
    return (
      <div className="flex flex-col items-center gap-3 py-4 px-2 glass m-2" style={{ width: 52, borderRadius: 20 }}>
        {/* Logo 小圆 */}
        <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
          style={{ background: '#7CB7FF' }}>
          <span className="text-[11px] font-medium text-white select-none">Y</span>
        </div>
        <button onClick={onNewSession} className="p-1.5 rounded-lg glass-hover transition-colors" title="新对话">
          <Plus className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
        </button>
        <button onClick={onToggle} className="p-1.5 rounded-lg glass-hover transition-colors mt-auto">
          <PanelLeftOpen className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
        </button>
      </div>
    )
  }

  // 展开态
  return (
    <div className="glass m-2 flex flex-col" style={{ width: 260, minWidth: 260, borderRadius: 20 }}>
      {/* ── 顶部：Logo + 折叠按钮 ── */}
      <div className="flex items-center justify-between px-4 py-4" style={{ borderBottom: '1px solid rgba(0,0,0,0.04)' }}>
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0"
            style={{ background: '#7CB7FF' }}>
            <span className="text-[13px] font-medium text-white select-none">Y</span>
          </div>
          <span className="text-[17px] font-medium select-none tracking-tight" style={{
            fontFamily: "'Cormorant Garamond', 'Georgia', serif",
            color: 'var(--text)',
          }}>Yuti</span>
        </div>
        <button onClick={onToggle} className="p-1.5 rounded-lg glass-hover">
          <PanelLeftClose className="w-4 h-4" style={{ color: 'var(--text-muted)' }} />
        </button>
      </div>

      {/* ── 中间：模块列表 ── */}
      <div className="flex-1 overflow-y-auto py-2 px-2 space-y-2">

        {/* 1. 新对话 */}
        <button
          onClick={() => { onNewSession(); loadSessions() }}
          className="glass-btn w-full flex items-center gap-2.5 px-4 py-2.5 text-[13px] font-medium"
          style={{ color: 'var(--text)' }}
        >
          <Plus className="w-4 h-4" /> 新对话
        </button>

        {/* 2. 知识库 — 可折叠 */}
        <div>
          <button
            onClick={() => setKbExpanded(!kbExpanded)}
            className="flex items-center gap-1.5 px-1 py-1 w-full text-left"
          >
            {kbExpanded ? <ChevronDown className="w-3.5 h-3.5 flex-shrink-0" style={{ color: 'var(--text-muted)' }} /> : <ChevronRight className="w-3.5 h-3.5 flex-shrink-0" style={{ color: 'var(--text-muted)' }} />}
            <BookOpen className="w-3.5 h-3.5 flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
            <span className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>知识库</span>
          </button>

          <AnimatePresence>
            {kbExpanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                {/* 新建 KB */}
                {newKBInput ? (
                  <div className="flex items-center gap-1 px-2 mt-1 mb-1">
                    <input autoFocus value={newKBName} onChange={(e) => setNewKBName(e.target.value)}
                      onKeyDown={(e) => { if (e.key === 'Enter') handleCreateKB(); if (e.key === 'Escape') { setNewKBInput(false); setNewKBName('') } }}
                      placeholder="输入名称..."
                      className="flex-1 text-[12px] px-2 py-1.5 rounded-lg bg-transparent border focus:outline-none"
                      style={{ borderColor: 'var(--glass-border)', color: 'var(--text)', background: 'var(--glass-bg)' }} />
                    <button onClick={handleCreateKB} className="p-1 rounded hover:bg-[var(--bg-card)]"><Plus className="w-3 h-3" /></button>
                    <button onClick={() => { setNewKBInput(false); setNewKBName('') }} className="p-1 rounded hover:bg-[var(--bg-card)]"><X className="w-3 h-3" /></button>
                  </div>
                ) : (
                  <button onClick={() => setNewKBInput(true)} className="w-full flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg glass-hover text-[12px] mt-0.5" style={{ color: 'var(--primary)' }}>
                    <Plus className="w-3.5 h-3.5" /> 新建知识库
                  </button>
                )}

                {/* KB 列表 */}
                <div className="mt-1 space-y-0">
                  {kbs.map((kb) => <KBItem key={kb.name + refreshKey} kb={kb} currentKB={currentKB} onSwitch={onSwitchKB} onRefresh={refresh} />)}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* 3. 最近对话 */}
        <div style={{ borderTop: '1px solid var(--border)', paddingTop: 8 }}>
          <div className="flex items-center gap-1.5 px-1 py-1">
            <Clock className="w-3.5 h-3.5 flex-shrink-0" style={{ color: 'var(--text-muted)' }} />
            <span className="text-[11px] font-semibold uppercase tracking-wider" style={{ color: 'var(--text-muted)' }}>最近对话</span>
          </div>
          <div className="space-y-0.5 mt-1">
            {sessions.map((s) => (
              <div key={s.session_id} className={`group/session flex items-center gap-1 px-2.5 py-1.5 rounded-lg cursor-pointer transition-all ${s.session_id === sessionId ? '' : 'hover:bg-[var(--bg-card-hover)]'}`}
                style={s.session_id === sessionId ? { background: 'var(--primary-light)', color: 'var(--primary)' } : { color: 'var(--text)' }}
                onClick={() => onLoadSession(s.session_id)}>
                <MessageSquare className="w-3 h-3 flex-shrink-0" />
                <span className="flex-1 truncate text-[12px]">{s.message_count > 0 ? `对话 (${s.message_count}轮)` : '空对话'}</span>
                <button onClick={(e) => { e.stopPropagation(); handleDeleteSession(s.session_id) }}
                  className="opacity-0 group-hover/session:opacity-100 p-0.5 rounded hover:bg-red-50 flex-shrink-0 transition-opacity">
                  <X className="w-3 h-3" style={{ color: '#e05555' }} />
                </button>
              </div>
            ))}
            {sessions.length === 0 && <div className="text-[11px] px-2 py-2" style={{ color: 'var(--text-muted)' }}>暂无对话记录</div>}
          </div>
        </div>
      </div>
    </div>
  )
}
