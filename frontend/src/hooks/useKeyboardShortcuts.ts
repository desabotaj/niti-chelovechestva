import { useEffect } from 'react'
import { useTime } from '../store/useTime'
import { useLineage } from '../store/useLineage'
import { useLayers } from '../store/useLayers'

export function useKeyboardShortcuts() {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return
      }
      const { setYear, year, togglePlay, setPlaying } = useTime.getState()
      const { selectLineage } = useLineage.getState()
      const { setLayer, showHexDensity, showArcs, showLineage, showCountries } = useLayers.getState()

      switch (e.code) {
        case 'Space':
          e.preventDefault()
          togglePlay()
          break
        case 'ArrowLeft':
          setPlaying(false)
          setYear(year - (e.shiftKey ? 50 : 5))
          break
        case 'ArrowRight':
          setPlaying(false)
          setYear(year + (e.shiftKey ? 50 : 5))
          break
        case 'KeyH':
          setLayer('showHexDensity', !showHexDensity)
          break
        case 'KeyM':
          setLayer('showArcs', !showArcs)
          break
        case 'KeyL':
          setLayer('showLineage', !showLineage)
          break
        case 'KeyC':
          setLayer('showCountries', !showCountries)
          break
        case 'Escape':
          selectLineage(null)
          break
      }
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [])
}
