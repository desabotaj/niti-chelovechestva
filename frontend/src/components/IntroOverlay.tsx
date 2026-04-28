import { AnimatePresence, motion } from 'framer-motion'
import { useEffect, useState } from 'react'
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
  const setPlaying = useTime((s) => s.setPlaying)
  const setYear = useTime((s) => s.setYear)
  const setSpeed = useTime((s) => s.setSpeed)

  useEffect(() => {
    const t = window.setInterval(() => {
      setScene((s) => {
        if (s + 1 >= SCENES.length) {
          window.setTimeout(() => {
            setClosed(true)
            setYear(1525)
            setSpeed(6)
            setPlaying(true)
          }, 2400)
          window.clearInterval(t)
          return s
        }
        return s + 1
      })
    }, 2600)
    return () => window.clearInterval(t)
  }, [setPlaying, setSpeed, setYear])

  const dismiss = () => {
    setClosed(true)
    setYear(1525)
    setSpeed(6)
    setPlaying(true)
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
        onClick={dismiss}
        className="absolute inset-0 z-30 grid cursor-pointer place-items-center bg-cosmos-950/60 backdrop-blur-sm"
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
              <span
                key={i}
                className={`h-1 w-8 rounded-full transition ${
                  i <= scene ? 'bg-thread-300' : 'bg-thread-300/20'
                }`}
              />
            ))}
          </div>
          <p className="mt-6 font-mono text-[10px] uppercase tracking-[0.3em] text-thread-300/40">
            нажмите, чтобы войти
          </p>
        </div>
      </motion.div>
    </AnimatePresence>
  )
}
