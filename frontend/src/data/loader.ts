import type {
  ArcsTile,
  EventTimelineFile,
  HexTile,
  LineagesFile,
  Meta,
} from '../types'

const BASE = '/data'

export async function fetchJson<T>(path: string): Promise<T> {
  const res = await fetch(path, { credentials: 'omit' })
  if (!res.ok) {
    throw new Error(`Failed to fetch ${path}: ${res.status} ${res.statusText}`)
  }
  return res.json() as Promise<T>
}

export const loadMeta = () => fetchJson<Meta>(`${BASE}/meta.json`)
export const loadEventsTimeline = () => fetchJson<EventTimelineFile>(`${BASE}/events_timeline.json`)
export const loadLineages = () => fetchJson<LineagesFile>(`${BASE}/lineages.json`)

const pad = (n: number) => String(n).padStart(2, '0')

export const loadHexTile = (decadeIdx: number) =>
  fetchJson<HexTile>(`${BASE}/hex_${pad(decadeIdx)}.json`)

export const loadArcsTile = (decadeIdx: number) =>
  fetchJson<ArcsTile>(`${BASE}/arcs_${pad(decadeIdx)}.json`)

const inflight: Map<string, Promise<unknown>> = new Map()

export function dedupe<T>(key: string, factory: () => Promise<T>): Promise<T> {
  if (inflight.has(key)) return inflight.get(key) as Promise<T>
  const p = factory().finally(() => inflight.delete(key))
  inflight.set(key, p)
  return p
}
