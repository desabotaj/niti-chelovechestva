import { PathLayer, ScatterplotLayer } from '@deck.gl/layers'
import type { Lineage } from '../types'
import { SELECTION_GLOW, THREAD_DIM, THREAD_GLOW, THREAD_TAIL } from '../utils/colors'

export interface ThreadsLayerOpts {
  lineages: Lineage[]
  selectedId: number | null
  hoveredId: number | null
  currentYear: number
  visible: boolean
}

interface ThreadPath {
  id: number
  selected: boolean
  hovered: boolean
  spanStart: number
  spanEnd: number
  path: [number, number][]
  endpoint: [number, number]
  endYear: number
}

function lineageToPaths(lin: Lineage, selectedId: number | null, hoveredId: number | null): ThreadPath {
  const ordered = [...lin.nodes].sort((a, b) => a.y - b.y)
  return {
    id: lin.id,
    selected: lin.id === selectedId,
    hovered: lin.id === hoveredId,
    spanStart: ordered[0].y,
    spanEnd: ordered[ordered.length - 1].y,
    path: ordered.map((n) => [n.lon, n.lat] as [number, number]),
    endpoint: [ordered[ordered.length - 1].lon, ordered[ordered.length - 1].lat],
    endYear: ordered[ordered.length - 1].y,
  }
}

export function lineageThreadsLayer({
  lineages,
  selectedId,
  hoveredId,
  currentYear,
  visible,
}: ThreadsLayerOpts) {
  const paths = lineages.map((l) => lineageToPaths(l, selectedId, hoveredId))

  const layers: any[] = []

  layers.push(
    new PathLayer<ThreadPath>({
      id: 'lineage-threads-base',
      data: paths,
      getPath: (d) => d.path,
      getColor: (d) => {
        if (d.selected) return SELECTION_GLOW
        if (d.hovered) return [...THREAD_GLOW]
        const visibleAtTime = currentYear >= d.spanStart && currentYear <= d.spanEnd + 25
        return visibleAtTime ? [...THREAD_TAIL] : [...THREAD_DIM]
      },
      getWidth: (d) => (d.selected ? 3.6 : d.hovered ? 2.4 : 1.0),
      widthUnits: 'pixels',
      widthMinPixels: 0.5,
      jointRounded: true,
      capRounded: true,
      pickable: true,
      visible,
      updateTriggers: {
        getColor: [selectedId, hoveredId, currentYear],
        getWidth: [selectedId, hoveredId],
      },
      parameters: {
        depthTest: false,
        blendFunc: [770, 1] as any,
      } as any,
    }),
  )

  layers.push(
    new ScatterplotLayer<ThreadPath>({
      id: 'lineage-endpoints',
      data: paths,
      getPosition: (d) => d.endpoint,
      getRadius: (d) => (d.selected ? 4.0 : d.hovered ? 2.4 : 0.7),
      radiusUnits: 'pixels',
      radiusMinPixels: 0.5,
      radiusMaxPixels: 8,
      getFillColor: (d) => (d.selected ? SELECTION_GLOW : THREAD_GLOW),
      filled: true,
      stroked: false,
      pickable: false,
      visible,
      parameters: {
        depthTest: false,
        blendFunc: [770, 1] as any,
      } as any,
      updateTriggers: {
        getRadius: [selectedId, hoveredId],
        getFillColor: [selectedId, hoveredId],
      },
    }),
  )

  return layers
}
