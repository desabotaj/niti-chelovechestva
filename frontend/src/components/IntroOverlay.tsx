import { AnimatePresence, motion } from 'framer-motion'
import { useRef, useState } from 'react'
import { useTime } from '../store/useTime'

const SCENES = [
  {
    title: 'В 1525 году',
    body: 'на Земле жило около полумиллиарда людей — основные центры были в речных долинах Китая, Индии и Европы.',
  },
  {
    title: 'Разворачиваются пять веков',
    body: 'эпидемии, завоевания, золотые лихорадки, разделы и революции меняют демографию и переносят судьбы через океаны.',
  },
  {
    title: 'Следите за нитями',
    body: 'каждая линия — синтетическое родовое дерево. Остановите время. Выберите нить. Проследите её путь.',
  },
]

export function IntroOverlay() {
  const [scene, setScene] = useState(0)
  const [closed, setClosed] = useState(false)
  const wheelLockRef = useRef(false)
  const setPlaying = useTime((s) => s.setPlaying)
  const setYear = useTime((s) => s.setYear)
  const setSpeed = useTime((s) => s.setSpeed)

  const dismiss = () => {
    setClosed(true)
    setYear(1525)
    setSpeed(6)
    setPlaying(true)
  }

  const moveScene = (direction: 1 | -1) => {
    setScene((s) => Math.max(0, Math.min(SCENES.length - 1, s + direction)))
  }

  const onWheel: React.WheelEventHandler<HTMLDivElement> = (e) => {
    if (wheelLockRef.current) return
    if (Math.abs(e.deltaY) < 12) return
    wheelLockRef.current = true
    moveScene(e.deltaY > 0 ? 1 : -1)
    window.setTimeout(() => {
      wheelLockRef.current = false
    }, 220)
  }

  if (closed) return null

  return (
    <AnimatePresence>
      <motion.div
        key="intro"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 1 }}
        onWheel={onWheel}
        className="absolute inset-0 z-30 grid place-items-center bg-cosmos-950/60 backdrop-blur-sm"
      >
        <div className="max-w-xl px-8 text-center">
          <AnimatePresence mode="wait">
            <motion.div
              key={scene}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -12 }}
              transition={{ duration: 0.7 }}
            >
              <h2 className="font-display text-4xl font-medium text-thread-50 thread-glow sm:text-6xl">
                {SCENES[scene].title}
              </h2>
              <p className="mt-4 text-base leading-relaxed text-thread-100/80 sm:text-lg">
                {SCENES[scene].body}
              </p>
            </motion.div>
          </AnimatePresence>
          <div className="mt-8 flex justify-center gap-1.5">
            {SCENES.map((_, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setScene(i)}
                aria-label={`Открыть слайд ${i + 1}`}
                className={`h-1 w-8 rounded-full transition ${
                  i <= scene ? 'bg-thread-300' : 'bg-thread-300/20'
                }`}
              />
            ))}
          </div>
          <p className="mt-4 font-mono text-[10px] uppercase tracking-[0.24em] text-thread-300/40">
            прокрутите колесом или нажмите на полоски
          </p>
          <button
            type="button"
            onClick={dismiss}
            className="mt-5 rounded-full border border-thread-300/40 bg-thread-400/10 px-5 py-2 font-mono text-[11px] uppercase tracking-[0.24em] text-thread-100 transition hover:bg-thread-300/30 hover:text-cosmos-950"
          >
            нажмите, чтобы войти
          </button>
        </div>
      </motion.div>
    </AnimatePresence>
  )
}
