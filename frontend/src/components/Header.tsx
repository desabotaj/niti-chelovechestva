import { motion } from 'framer-motion'
import { useTime } from '../store/useTime'

export function Header() {
  const startYear = useTime((s) => s.startYear)
  const endYear = useTime((s) => s.endYear)
  return (
    <motion.header
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 1.2, delay: 1.4, ease: 'easeOut' }}
      className="pointer-events-none absolute left-0 right-0 top-0 z-20 flex flex-col items-center pt-6 sm:pt-8"
    >
      <h1 className="font-display text-3xl font-medium tracking-tight text-thread-50 thread-glow sm:text-5xl">
        Нити человечества
      </h1>
      <p className="mt-1 font-mono text-[11px] uppercase tracking-[0.3em] text-thread-300/80 sm:text-xs">
        {startYear} &nbsp;·&nbsp; СИНТЕТИЧЕСКАЯ ГЕНЕАЛОГИЯ &nbsp;·&nbsp; {endYear}
      </p>
    </motion.header>
  )
}
