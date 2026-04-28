import { motion } from 'framer-motion'
import { useData } from '../store/useData'
import { useLineage } from '../store/useLineage'

export function DataBadge() {
  const meta = useData((s) => s.meta)
  const lineages = useLineage((s) => s.lineages)
  if (!meta) return null

  const stats = [
    { v: meta.regions.length, l: 'регионов' },
    { v: meta.events.length, l: 'событий' },
    { v: meta.decadeCount, l: 'декад' },
    { v: lineages.length, l: 'линий рода' },
  ]

  return (
    <motion.aside
      initial={{ opacity: 0, x: -8 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.8, delay: 1.6 }}
      className="pointer-events-auto absolute left-4 top-24 z-20 hidden w-96 sm:block"
    >
      <div className="glass rounded-xl px-6 py-5">
        <h2 className="font-mono text-[12px] uppercase tracking-[0.24em] text-thread-300/80">
          синтетический датасет
        </h2>
        <p className="mt-2 font-display text-lg italic leading-snug text-thread-100/85">
          Калиброванная детерминированная модель <span className="text-thread-300">500 лет</span>{' '}
          генеалогии и миграций человечества.
        </p>
        <div className="mt-4 grid grid-cols-2 gap-2.5">
          {stats.map((s) => (
            <div key={s.l} className="rounded-md border border-thread-400/10 bg-thread-400/[0.04] px-2.5 py-2">
              <div className="font-mono text-3xl text-thread-50 tabular-nums">{s.v}</div>
              <div className="font-mono text-[11px] uppercase tracking-[0.14em] text-thread-300/60">
                {s.l}
              </div>
            </div>
          ))}
        </div>
      </div>
    </motion.aside>
  )
}
