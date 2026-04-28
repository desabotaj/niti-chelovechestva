import { AnimatePresence, motion } from 'framer-motion'
import { useState } from 'react'
import { useLineage } from '../store/useLineage'
import { useTime } from '../store/useTime'

export function LineageExplorer() {
  const lineages = useLineage((s) => s.lineages)
  const selectedId = useLineage((s) => s.selectedId)
  const selectLineage = useLineage((s) => s.selectLineage)
  const hoverLineage = useLineage((s) => s.hoverLineage)
  const setYear = useTime((s) => s.setYear)
  const [open, setOpen] = useState(false)

  const selected = lineages.find((l) => l.id === selectedId) ?? null

  return (
    <motion.div
      initial={{ opacity: 0, x: -12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.8, delay: 1.8 }}
      className="pointer-events-auto absolute bottom-56 left-4 z-20 sm:bottom-44 sm:left-6"
    >
      <button
        onClick={() => setOpen((v) => !v)}
        className={`glass flex items-center gap-3 rounded-full px-6 py-3 font-mono text-[14px] uppercase tracking-[0.16em] transition ${
          open ? 'text-thread-50' : 'text-thread-300/80 hover:text-thread-100'
        }`}
      >
        <span className="h-2.5 w-2.5 rounded-full bg-thread-300 animate-slow-pulse" />
        Родовые линии · {lineages.length}
      </button>

      <AnimatePresence>
        {open && (
          <motion.div
            initial={{ opacity: 0, y: 8, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 8, scale: 0.96 }}
            transition={{ duration: 0.2 }}
            className="glass absolute bottom-full mb-3 max-h-[52vh] w-[23rem] overflow-y-auto rounded-xl px-4 py-3 scrollbar-thin"
          >
            <h3 className="font-display text-lg text-thread-50">
              Выберите линию для просмотра
            </h3>
            <p className="mt-0.5 mb-2.5 font-mono text-[11px] uppercase tracking-[0.16em] text-thread-300/60">
              ~14 поколений · место рождения → настоящее
            </p>
            <ul className="flex flex-col gap-0.5">
              {lineages.map((l) => {
                const span = `${l.span[0]} – ${l.span[1]}`
                const active = l.id === selectedId
                return (
                  <li key={l.id}>
                    <button
                      onClick={() => {
                        selectLineage(active ? null : l.id)
                        if (!active) {
                          setOpen(false)
                          setYear(l.span[1])
                        }
                      }}
                      onMouseEnter={() => hoverLineage(l.id)}
                      onMouseLeave={() => hoverLineage(null)}
                      className={`flex w-full items-baseline justify-between rounded-md px-2.5 py-2 text-left transition ${
                        active
                          ? 'bg-thread-400/15 text-thread-50'
                          : 'text-thread-200/85 hover:bg-thread-400/10 hover:text-thread-100'
                      }`}
                    >
                      <span className="text-base leading-tight">{l.title}</span>
                      <span className="ml-2 font-mono text-[11px] tabular-nums text-thread-300/60">
                        {span}
                      </span>
                    </button>
                  </li>
                )
              })}
            </ul>
          </motion.div>
        )}
      </AnimatePresence>

      {selected && (
        <motion.div
          initial={{ opacity: 0, y: 6 }}
          animate={{ opacity: 1, y: 0 }}
          className="glass mt-3 max-w-md rounded-xl px-5 py-4"
        >
          <div className="flex items-start justify-between gap-3">
            <span className="pr-2 font-display text-base leading-tight text-thread-50">{selected.title}</span>
            <button
              onClick={() => {
                selectLineage(null)
                setOpen(true)
              }}
              className="shrink-0 rounded-full border border-thread-300/35 bg-thread-400/10 px-3.5 py-1.5 font-mono text-[12px] uppercase tracking-[0.16em] text-thread-200 transition hover:bg-thread-300/25 hover:text-cosmos-950"
            >
              сброс
            </button>
          </div>
          <ol className="mt-2.5 flex flex-col gap-1 text-[12px] text-thread-200/80">
            {selected.nodes
              .slice()
              .sort((a, b) => b.y - a.y)
              .map((n, i) => (
                <li
                  key={`${n.y}-${i}`}
                  className="flex items-baseline justify-between border-l border-thread-400/15 pl-2"
                >
                  <span className="font-mono text-[11px] tabular-nums text-thread-300/80">{n.y}</span>
                  <span className="ml-3 truncate text-thread-100/90">{n.n}</span>
                </li>
              ))}
          </ol>
        </motion.div>
      )}
    </motion.div>
  )
}
