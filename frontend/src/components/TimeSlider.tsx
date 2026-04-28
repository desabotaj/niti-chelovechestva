import { useEffect, useMemo, useRef } from 'react'
import { motion } from 'framer-motion'
import { useTime } from '../store/useTime'
import { useData } from '../store/useData'
import { eventNameRu } from '../i18n/eventsRu'

const MAJOR_TICKS = [1525, 1600, 1700, 1800, 1900, 2000, 2025]

export function TimeSlider() {
  const startYear = useTime((s) => s.startYear)
  const endYear = useTime((s) => s.endYear)
  const year = useTime((s) => s.year)
  const isPlaying = useTime((s) => s.isPlaying)
  const setYear = useTime((s) => s.setYear)
  const togglePlay = useTime((s) => s.togglePlay)
  const speed = useTime((s) => s.playbackSpeed)
  const setSpeed = useTime((s) => s.setSpeed)
  const meta = useData((s) => s.meta)
  const sliderRef = useRef<HTMLDivElement>(null)
  const draggingRef = useRef(false)
  const accumulatorRef = useRef(0)
  const PLAYBACK_TICK_SECONDS = 1 / 24

  useEffect(() => {
    let raf = 0
    let prev = performance.now()
    const tick = (now: number) => {
      const dt = (now - prev) / 1000
      prev = now
      accumulatorRef.current += dt
      if (accumulatorRef.current >= PLAYBACK_TICK_SECONDS) {
        useTime.getState().step(accumulatorRef.current)
        accumulatorRef.current = 0
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [])

  const progress = (year - startYear) / (endYear - startYear)

  const setPlaying = useTime((s) => s.setPlaying)
  const handlePointer = (e: React.PointerEvent | PointerEvent) => {
    const el = sliderRef.current
    if (!el) return
    const rect = el.getBoundingClientRect()
    const t = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width))
    setYear(startYear + t * (endYear - startYear))
  }

  useEffect(() => {
    const onMove = (e: PointerEvent) => {
      if (!draggingRef.current) return
      handlePointer(e)
    }
    const onUp = () => {
      draggingRef.current = false
    }
    window.addEventListener('pointermove', onMove)
    window.addEventListener('pointerup', onUp)
    return () => {
      window.removeEventListener('pointermove', onMove)
      window.removeEventListener('pointerup', onUp)
    }
  })

  const activeEvents = useMemo(() => {
    if (!meta) return []
    const yr = Math.round(year)
    return meta.events.filter((e) => yr >= e.start && yr <= e.end)
  }, [year, meta])

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.8, delay: 1.6, ease: 'easeOut' }}
      className="pointer-events-auto absolute inset-x-0 bottom-6 z-20 mx-auto flex w-[calc(100%-2rem)] max-w-[38rem] flex-col gap-2.5 sm:w-[calc(100%-4rem)]"
    >
      <div className="glass rounded-2xl px-5 py-4">
        <div className="flex items-center gap-4">
          <button
            onClick={togglePlay}
            className="grid h-10 w-10 place-items-center rounded-full bg-thread-400/15 text-thread-200 transition hover:bg-thread-400/30 hover:text-thread-50"
            aria-label={isPlaying ? 'Пауза' : 'Воспроизведение'}
          >
            {isPlaying ? (
              <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor"><rect x="2" y="2" width="3.5" height="10" rx="1" /><rect x="8.5" y="2" width="3.5" height="10" rx="1" /></svg>
            ) : (
              <svg width="14" height="14" viewBox="0 0 14 14" fill="currentColor"><path d="M3 2 L12 7 L3 12 Z" /></svg>
            )}
          </button>
          <div className="flex flex-1 flex-col">
            <div className="flex items-baseline justify-between font-mono text-[12px] uppercase tracking-[0.22em] text-thread-300/70">
              <span>{startYear}</span>
              <span className="font-display text-[2rem] font-medium tracking-normal text-thread-50 thread-glow">
                {Math.round(year)}
              </span>
              <span>{endYear}</span>
            </div>
            <div
              ref={sliderRef}
              onPointerDown={(e) => {
                draggingRef.current = true
                setPlaying(false)
                handlePointer(e)
              }}
              className="relative mt-2.5 h-4 w-full cursor-pointer touch-none"
            >
              <div className="absolute inset-y-1 left-0 right-0 rounded-full bg-cosmos-700/80" />
              <div
                className="absolute inset-y-1 left-0 rounded-full bg-gradient-to-r from-thread-700/40 via-thread-400 to-thread-100 shadow-[0_0_20px_rgba(252,211,77,0.5)]"
                style={{ width: `${progress * 100}%` }}
              />
              {MAJOR_TICKS.map((y) => {
                const t = (y - startYear) / (endYear - startYear)
                return (
                  <div
                    key={y}
                    className="absolute top-1/2 h-2.5 w-px -translate-y-1/2 bg-thread-300/30"
                    style={{ left: `${t * 100}%` }}
                  />
                )
              })}
              <div
                className="absolute top-1/2 -translate-x-1/2 -translate-y-1/2"
                style={{ left: `${progress * 100}%` }}
              >
                <div className="h-6 w-6 rounded-full bg-thread-300 shadow-[0_0_24px_rgba(252,211,77,0.7)] ring-2 ring-cosmos-950" />
              </div>
            </div>
            <div className="mt-1.5 flex justify-between font-mono text-[10px] uppercase tracking-[0.14em] text-thread-300/40">
              {MAJOR_TICKS.map((y) => (
                <span key={y}>{y}</span>
              ))}
            </div>
          </div>
          <div className="hidden flex-col items-end gap-1.5 sm:flex">
            <span className="font-mono text-[11px] uppercase tracking-[0.2em] text-thread-300/60">скорость</span>
            <div className="flex gap-2">
              {[1, 3, 6].map((s) => (
                <button
                  key={s}
                  onClick={() => setSpeed(s)}
                  className={`rounded-full px-3 py-1 font-mono text-[11px] tracking-widest transition ${
                    speed === s
                      ? 'bg-thread-300 text-cosmos-950'
                      : 'bg-cosmos-700/50 text-thread-300/70 hover:bg-cosmos-700'
                  }`}
                >
                  {s}×
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {activeEvents.length > 0 && (
        <div className="glass rounded-xl px-5 py-2.5">
          <div className="flex flex-wrap items-center gap-2.5 text-[12px]">
            <span className="font-mono uppercase tracking-[0.2em] text-thread-300/60">
              сейчас происходят
            </span>
            <span className="divider flex-1" />
            {activeEvents.slice(0, 6).map((e) => (
              <span
                key={e.id}
                className="rounded-full border border-thread-400/20 bg-thread-400/5 px-2.5 py-1 text-thread-100"
              >
                {eventNameRu(e)}
              </span>
            ))}
            {activeEvents.length > 6 && (
              <span className="text-thread-300/60">+еще {activeEvents.length - 6}</span>
            )}
          </div>
        </div>
      )}
    </motion.div>
  )
}
