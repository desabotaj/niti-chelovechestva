import { motion } from 'framer-motion'
import { useData } from '../store/useData'

export function StatusBar() {
  const status = useData((s) => s.status)
  const error = useData((s) => s.error)
  if (status === 'ready') return null
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="pointer-events-none absolute inset-x-0 bottom-3 z-30 flex justify-center"
    >
      <div className="glass rounded-full px-5 py-2 font-mono text-[11px] uppercase tracking-[0.2em] text-thread-300/80">
        {status === 'loading' && 'читаем реку человечества…'}
        {status === 'idle' && 'подготавливаем сцену…'}
        {status === 'error' && (error || 'не удалось загрузить')}
      </div>
    </motion.div>
  )
}
