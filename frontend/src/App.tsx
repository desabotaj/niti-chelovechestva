import { useEffect } from 'react'
import { useKeyboardShortcuts } from './hooks/useKeyboardShortcuts'
import { Globe } from './components/Globe'
import { Header } from './components/Header'
import { TimeSlider } from './components/TimeSlider'
import { EventTicker } from './components/EventTicker'
import { LineageExplorer } from './components/LineageExplorer'
import { Legend } from './components/Legend'
import { IntroOverlay } from './components/IntroOverlay'
import { StatusBar } from './components/StatusBar'
import { DataBadge } from './components/DataBadge'
import { useData } from './store/useData'
import { useTime } from './store/useTime'
import { useLineage } from './store/useLineage'
import { loadLineages, loadMeta } from './data/loader'
import { localizeLineages, localizeMeta } from './i18n/contentRu'

export default function App() {
  useKeyboardShortcuts()
  const setMeta = useData((s) => s.setMeta)
  const setStatus = useData((s) => s.setStatus)
  const setRange = useTime((s) => s.setRange)
  const setLineages = useLineage((s) => s.setLineages)

  useEffect(() => {
    let cancelled = false
    setStatus('loading')
    Promise.all([loadMeta(), loadLineages()])
      .then(([metaRaw, lineagesRaw]) => {
        if (cancelled) return
        const meta = localizeMeta(metaRaw)
        const lineages = localizeLineages(lineagesRaw)
        setMeta(meta)
        setRange(meta.startYear, meta.endYear)
        setLineages(lineages.lineages)
        setStatus('ready')
      })
      .catch((err) => {
        if (cancelled) return
        console.error(err)
        setStatus('error', err.message ?? 'ошибка загрузки')
      })
    return () => {
      cancelled = true
    }
  }, [setMeta, setRange, setLineages, setStatus])

  return (
    <div className="relative h-full w-full overflow-hidden">
      <Globe />
      <Header />
      <DataBadge />
      <div className="pointer-events-none absolute right-4 top-24 bottom-56 z-20 hidden w-96 sm:flex sm:flex-col sm:gap-4 sm:right-6">
        <EventTicker className="w-full" />
        <Legend className="mt-auto w-full" />
      </div>
      <LineageExplorer />
      <TimeSlider />
      <StatusBar />
      <IntroOverlay />
    </div>
  )
}
