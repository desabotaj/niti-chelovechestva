import { create } from 'zustand'

interface LayersState {
  showHexDensity: boolean
  showArcs: boolean
  showLineage: boolean
  showCountries: boolean
  arcOpacity: number
  hexOpacity: number
  setLayer: (key: keyof LayersState, value: boolean) => void
  setOpacity: (key: 'arcOpacity' | 'hexOpacity', value: number) => void
}

export const useLayers = create<LayersState>((set) => ({
  showHexDensity: true,
  showArcs: true,
  showLineage: true,
  showCountries: true,
  arcOpacity: 1,
  hexOpacity: 0.85,
  setLayer: (key, value) => set(() => ({ [key]: value }) as Partial<LayersState>),
  setOpacity: (key, value) => set(() => ({ [key]: value }) as Partial<LayersState>),
}))
