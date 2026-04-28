import { create } from 'zustand'
import type { ArcsTile, HexTile, Meta } from '../types'

type LoadStatus = 'idle' | 'loading' | 'ready' | 'error'

interface DataState {
  meta: Meta | null
  hexCache: Map<number, HexTile>
  arcCache: Map<number, ArcsTile>
  status: LoadStatus
  error: string | null
  setMeta: (m: Meta) => void
  setStatus: (s: LoadStatus, error?: string) => void
  putHex: (idx: number, tile: HexTile) => void
  putArcs: (idx: number, tile: ArcsTile) => void
}

export const useData = create<DataState>((set) => ({
  meta: null,
  hexCache: new Map(),
  arcCache: new Map(),
  status: 'idle',
  error: null,
  setMeta: (meta) => set({ meta, status: 'ready' }),
  setStatus: (status, error) => set({ status, error: error ?? null }),
  putHex: (idx, tile) =>
    set((s) => {
      const next = new Map(s.hexCache)
      next.set(idx, tile)
      return { hexCache: next }
    }),
  putArcs: (idx, tile) =>
    set((s) => {
      const next = new Map(s.arcCache)
      next.set(idx, tile)
      return { arcCache: next }
    }),
}))
