import { motion } from 'framer-motion'
import { useLayers } from '../store/useLayers'

type LegendProps = {
  className?: string
}

export function Legend({ className }: LegendProps) {
  const showHex = useLayers((s) => s.showHexDensity)
  const showArcs = useLayers((s) => s.showArcs)
  const showLineage = useLayers((s) => s.showLineage)
  const showCountries = useLayers((s) => s.showCountries)
  const setLayer = useLayers((s) => s.setLayer)

  return (
    <motion.div
      initial={{ opacity: 0, x: 12 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: 0.8, delay: 2 }}
      className={`pointer-events-auto hidden sm:block ${className ?? ''}`}
    >
      <div className="glass w-96 rounded-xl px-6 py-5">
        <h3 className="font-mono text-[12px] uppercase tracking-[0.24em] text-thread-300/80">
          легенда и слои
        </h3>

        <div className="mt-4">
          <div className="font-mono text-[12px] uppercase tracking-[0.18em] text-thread-300/60">
            плотность населения
          </div>
          <div className="mt-1.5 h-2.5 w-full rounded-full bg-gradient-to-r from-cosmos-700 via-violet-700 via-fuchsia-700 via-thread-500 to-thread-100" />
          <div className="mt-1 flex justify-between font-mono text-[12px] text-thread-300/40">
            <span>редко</span>
            <span>плотно</span>
          </div>
        </div>

        <div className="mt-4">
          <div className="font-mono text-[12px] uppercase tracking-[0.18em] text-thread-300/60">
            направление миграции
          </div>
          <div className="mt-1.5 h-2.5 w-full rounded-full bg-gradient-to-r from-flow-cyan via-flow-violet to-flow-rose" />
          <div className="mt-1 flex justify-between font-mono text-[12px] text-thread-300/40">
            <span>← на запад</span>
            <span>на восток →</span>
          </div>
        </div>

        <div className="my-4 divider" />

        <ul className="flex flex-col gap-2 text-base">
          {[
            {
              k: 'showHexDensity',
              v: showHex,
              label: 'Гексагональная плотность',
              key: 'H',
              hint: 'Показывает, сколько людей живет в каждой зоне карты. Чем ярче и светлее гексагон — тем выше плотность.',
            },
            {
              k: 'showArcs',
              v: showArcs,
              label: 'Дуги миграций',
              key: 'M',
              hint: 'Это направления перемещений людей между регионами. Толще и ярче дуга — сильнее миграционный поток.',
            },
            {
              k: 'showLineage',
              v: showLineage,
              label: 'Нити родов',
              key: 'L',
              hint: 'Личные родовые траектории через поколения: где рождались предки и как их линия проходила по миру.',
            },
            { k: 'showCountries', v: showCountries, label: 'Страны', key: 'C' },
          ].map(({ k, v, label, key, hint }) => (
            <li key={k}>
              <button
                onClick={() => setLayer(k as any, !v)}
                className="flex w-full items-center justify-between rounded-md px-2.5 py-1.5 text-left hover:bg-thread-400/5"
              >
                <span className="flex items-center gap-2">
                  <span
                    className={`h-4 w-8 rounded-full transition ${
                      v ? 'bg-thread-300' : 'bg-cosmos-700'
                    }`}
                  >
                    <span
                      className={`block h-4 w-4 rounded-full bg-cosmos-950 shadow transition ${
                        v ? 'translate-x-4' : 'translate-x-0'
                      }`}
                    />
                  </span>
                  <span className={`flex min-w-0 items-center gap-1 ${v ? 'text-thread-100' : 'text-thread-300/40'}`}>
                    {hint && (
                      <span className="group relative inline-flex shrink-0 items-center">
                    <span className="inline-flex h-5 w-5 items-center justify-center rounded-full border border-thread-300/50 text-[11px] leading-none text-thread-300/80">
                          i
                        </span>
                        <span className="pointer-events-none absolute left-0 top-full z-30 mt-1 w-64 rounded-md border border-thread-400/20 bg-cosmos-900/95 px-3 py-2 text-[12px] normal-case tracking-normal text-thread-100 opacity-0 shadow-xl transition-opacity group-hover:opacity-100">
                          {hint}
                        </span>
                      </span>
                    )}
                    <span className="truncate pr-1 text-base">{label}</span>
                  </span>
                </span>
                <kbd className="font-mono text-[12px] uppercase tracking-widest text-thread-300/40">
                  {key}
                </kbd>
              </button>
            </li>
          ))}
        </ul>

        <div className="my-4 divider" />

        <div className="flex flex-wrap gap-2 text-[12px] text-thread-300/60">
          <span>
            <kbd className="rounded bg-cosmos-700/60 px-1.5 py-px font-mono text-[11px] text-thread-100">space</kbd> пауза/пуск
          </span>
          <span>
            <kbd className="rounded bg-cosmos-700/60 px-1.5 py-px font-mono text-[11px] text-thread-100">←/→</kbd> прокрутка
          </span>
          <span>
            <kbd className="rounded bg-cosmos-700/60 px-1.5 py-px font-mono text-[11px] text-thread-100">drag</kbd> вращение
          </span>
        </div>
      </div>
    </motion.div>
  )
}
