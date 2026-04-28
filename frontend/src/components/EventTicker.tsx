import { AnimatePresence, motion } from 'framer-motion'
import { useMemo } from 'react'
import { useTime } from '../store/useTime'
import { useData } from '../store/useData'
import { eventNameRu } from '../i18n/eventsRu'

const TYPE_COLOR: Record<string, string> = {
  war: 'text-rose-300',
  plague: 'text-emerald-300',
  famine: 'text-amber-200',
  revolution: 'text-violet-300',
  colonization: 'text-cyan-200',
  industrialization: 'text-thread-200',
  persecution: 'text-rose-200',
  goldrush: 'text-yellow-200',
  partition: 'text-orange-200',
  natural: 'text-sky-200',
  exploration: 'text-thread-100',
  abolition: 'text-emerald-200',
  exodus: 'text-pink-200',
}

const TYPE_LABEL_RU: Record<string, string> = {
  war: 'война',
  plague: 'эпидемия',
  famine: 'голод',
  revolution: 'революция',
  colonization: 'колонизация',
  industrialization: 'индустриализация',
  persecution: 'преследования',
  goldrush: 'золотая лихорадка',
  partition: 'раздел',
  natural: 'природное событие',
  exploration: 'экспансия',
  abolition: 'отмена рабства',
  exodus: 'исход',
}

type EventTickerProps = {
  className?: string
}

export function EventTicker({ className }: EventTickerProps) {
  const year = useTime((s) => s.year)
  const meta = useData((s) => s.meta)

  const events = useMemo(() => {
    if (!meta) return []
    const yr = Math.round(year)
    return meta.events
      .filter((e) => yr >= e.start && yr <= e.end)
      .sort((a, b) => a.start - b.start)
      .slice(0, 6)
  }, [year, meta])

  return (
    <motion.aside
      initial={{ opacity: 0, x: 12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.8, delay: 1.8 }}
      className={`pointer-events-auto hidden w-96 sm:block ${className ?? ''}`}
    >
      <div className="glass max-h-[30vh] overflow-y-auto rounded-xl px-6 py-5 scrollbar-thin">
        <div className="mb-3 flex items-center gap-2">
          <span className="h-2 w-2 rounded-full bg-thread-300 animate-slow-pulse" />
          <h2 className="font-mono text-[12px] uppercase tracking-[0.24em] text-thread-300/80">
            исторический пульс
          </h2>
        </div>
        <AnimatePresence initial={false}>
          {events.length === 0 ? (
            <motion.p
              key="quiet"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="font-display text-lg italic text-thread-300/50"
            >
              Спокойный период. Жизни текут своим чередом.
            </motion.p>
          ) : (
            events.map((e) => (
              <motion.div
                key={e.id}
                layout
                initial={{ opacity: 0, x: 8 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -8 }}
                transition={{ duration: 0.4 }}
                className="mb-3 border-l-2 border-thread-400/30 pl-4"
              >
                <div className="flex items-baseline justify-between gap-2">
                  <span className="font-display text-lg leading-tight text-thread-50">
                    {eventNameRu(e)}
                  </span>
                  <span className="font-mono text-[12px] tabular-nums text-thread-300/60">
                    {e.start}–{e.end}
                  </span>
                </div>
                <div
                  className={`mt-1 font-mono text-[12px] uppercase tracking-[0.14em] ${
                    TYPE_COLOR[e.type] ?? 'text-thread-200/80'
                  }`}
                >
                  {TYPE_LABEL_RU[e.type] ?? e.type}
                </div>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>
    </motion.aside>
  )
}
