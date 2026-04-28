import type { ArcRecord, ArcsTile, HexCell, HexTile } from '../types'

export interface BlendedHex {
  h: string
  pop: number
  cont: HexCell['c']
}

export function blendHexTiles(
  current: HexTile | undefined,
  next: HexTile | undefined,
  t: number,
  maxCells = 3500,
): BlendedHex[] {
  const map = new Map<string, BlendedHex>()
  const tt = Math.max(0, Math.min(1, t))

  if (current) {
    for (const cell of current.cells) {
      map.set(cell.h, { h: cell.h, pop: cell.p * (1 - tt), cont: cell.c })
    }
  }
  if (next) {
    for (const cell of next.cells) {
      const prev = map.get(cell.h)
      if (prev) {
        prev.pop += cell.p * tt
        if (cell.p * tt > prev.pop * 0.5) prev.cont = cell.c
      } else {
        map.set(cell.h, { h: cell.h, pop: cell.p * tt, cont: cell.c })
      }
    }
  }
  const blended = Array.from(map.values()).filter((c) => c.pop >= 0.5)
  blended.sort((a, b) => b.pop - a.pop)
  return blended.slice(0, maxCells)
}

export interface BlendedArc extends ArcRecord {
  intensity: number
}

export function blendArcs(
  current: ArcsTile | undefined,
  next: ArcsTile | undefined,
  t: number,
  topN = 60,
): BlendedArc[] {
  const tt = Math.max(0, Math.min(1, t))
  const out: BlendedArc[] = []
  if (current) {
    const max = current.arcs[0]?.n || 1
    for (const arc of current.arcs.slice(0, topN)) {
      out.push({ ...arc, intensity: (arc.n / max) * (1 - tt * 0.4) })
    }
  }
  if (next) {
    const max = next.arcs[0]?.n || 1
    for (const arc of next.arcs.slice(0, topN)) {
      out.push({ ...arc, intensity: (arc.n / max) * (0.6 + 0.4 * tt) })
    }
  }
  return out
}
