import { create } from 'zustand'

interface TimeState {
  startYear: number
  endYear: number
  decadeStep: number
  year: number
  isPlaying: boolean
  playbackSpeed: number
  setYear: (year: number) => void
  setRange: (start: number, end: number) => void
  setPlaying: (playing: boolean) => void
  togglePlay: () => void
  setSpeed: (s: number) => void
  step: (dt: number) => void
}

export const useTime = create<TimeState>((set, get) => ({
  startYear: 1525,
  endYear: 2025,
  decadeStep: 10,
  year: 1525,
  isPlaying: false,
  playbackSpeed: 4,
  setYear: (year) => set(() => ({ year: Math.max(get().startYear, Math.min(get().endYear, year)) })),
  setRange: (startYear, endYear) =>
    set(() => ({ startYear, endYear, year: startYear })),
  setPlaying: (isPlaying) => set(() => ({ isPlaying })),
  togglePlay: () => set((s) => ({ isPlaying: !s.isPlaying })),
  setSpeed: (playbackSpeed) => set(() => ({ playbackSpeed })),
  step: (dt) => {
    const { year, endYear, startYear, playbackSpeed, isPlaying } = get()
    if (!isPlaying) return
    let next = year + dt * playbackSpeed
    if (next > endYear) next = startYear
    set({ year: next })
  },
}))

export function decadeIndexForYear(year: number, startYear: number, decadeStep = 10): number {
  return Math.max(0, Math.floor((year - startYear) / decadeStep))
}

export function decadeProgressForYear(year: number, startYear: number, decadeStep = 10): number {
  const idx = decadeIndexForYear(year, startYear, decadeStep)
  const baseYear = startYear + idx * decadeStep
  return Math.max(0, Math.min(1, (year - baseYear) / decadeStep))
}
