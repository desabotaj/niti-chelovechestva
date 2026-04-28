import { create } from 'zustand'
import type { Lineage } from '../types'

interface LineageState {
  lineages: Lineage[]
  selectedId: number | null
  hoveredId: number | null
  setLineages: (lineages: Lineage[]) => void
  selectLineage: (id: number | null) => void
  hoverLineage: (id: number | null) => void
}

export const useLineage = create<LineageState>((set) => ({
  lineages: [],
  selectedId: null,
  hoveredId: null,
  setLineages: (lineages) => set(() => ({ lineages })),
  selectLineage: (selectedId) => set(() => ({ selectedId })),
  hoverLineage: (hoveredId) => set(() => ({ hoveredId })),
}))
