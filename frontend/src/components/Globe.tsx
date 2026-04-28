import { useEffect, useMemo, useRef, useState } from 'react'
import DeckGL from '@deck.gl/react'
import { _GlobeView as GlobeView } from '@deck.gl/core'
import {
  countriesFillLayer,
  countriesGlowLayer,
} from '../layers/earthLayers'
import { populationHexLayer } from '../layers/populationHexLayer'
import { migrationArcsLayer } from '../layers/migrationArcsLayer'
import { lineageThreadsLayer } from '../layers/lineageThreadsLayer'
import { useTime, decadeIndexForYear, decadeProgressForYear } from '../store/useTime'
import { useData } from '../store/useData'
import { useLayers } from '../store/useLayers'
import { useLineage } from '../store/useLineage'
import { blendArcs, blendHexTiles } from '../data/interpolation'
import { loadArcsTile, loadHexTile, dedupe } from '../data/loader'

const initialViewState = {
  longitude: -10,
  latitude: 22,
  zoom: 0.65,
  pitch: 0,
  bearing: 0,
}

const MIN_ZOOM = -0.5
const MAX_ZOOM = 4.5

export function Globe() {
  const year = useTime((s) => s.year)
  const isPlaying = useTime((s) => s.isPlaying)
  const meta = useData((s) => s.meta)
  const hexCache = useData((s) => s.hexCache)
  const arcCache = useData((s) => s.arcCache)
  const putHex = useData((s) => s.putHex)
  const putArcs = useData((s) => s.putArcs)
  const showHex = useLayers((s) => s.showHexDensity)
  const showArcs = useLayers((s) => s.showArcs)
  const showLineage = useLayers((s) => s.showLineage)
  const showCountries = useLayers((s) => s.showCountries)
  const hexOpacity = useLayers((s) => s.hexOpacity)
  const arcOpacity = useLayers((s) => s.arcOpacity)
  const lineages = useLineage((s) => s.lineages)
  const selectedId = useLineage((s) => s.selectedId)
  const hoveredId = useLineage((s) => s.hoveredId)

  const [viewState, setViewState] = useState<typeof initialViewState>(initialViewState)
  const lastInteract = useRef(0)
  const autoRotateRef = useRef(true)

  useEffect(() => {
    const onMove = () => {
      lastInteract.current = performance.now()
      autoRotateRef.current = false
    }
    window.addEventListener('pointerdown', onMove)
    window.addEventListener('wheel', onMove, { passive: true })
    return () => {
      window.removeEventListener('pointerdown', onMove)
      window.removeEventListener('wheel', onMove)
    }
  }, [])

  useEffect(() => {
    let raf = 0
    let prev = performance.now()
    const tick = (now: number) => {
      const dt = (now - prev) / 1000
      prev = now
      const idle = now - lastInteract.current > 6000
      if (idle && !isPlaying) autoRotateRef.current = true
      if (autoRotateRef.current) {
        setViewState((vs) => ({ ...vs, longitude: (vs.longitude + dt * 1.4) % 360 }))
      }
      raf = requestAnimationFrame(tick)
    }
    raf = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(raf)
  }, [isPlaying])

  const decadeIdx = useMemo(
    () => (meta ? decadeIndexForYear(year, meta.startYear, 10) : 0),
    [year, meta],
  )
  const decadeT = useMemo(
    () => (meta ? decadeProgressForYear(year, meta.startYear, 10) : 0),
    [year, meta],
  )
  const renderProgress = isPlaying ? Math.round(decadeT * 12) / 12 : decadeT

  useEffect(() => {
    if (!meta) return
    const wanted = [decadeIdx, decadeIdx + 1, decadeIdx + 2, decadeIdx - 1].filter(
      (i) => i >= 0 && i < meta.decadeCount,
    )
    for (const i of wanted) {
      if (!hexCache.has(i)) {
        dedupe(`hex-${i}`, () => loadHexTile(i))
          .then((tile) => putHex(i, tile))
          .catch(() => undefined)
      }
      if (!arcCache.has(i)) {
        dedupe(`arcs-${i}`, () => loadArcsTile(i))
          .then((tile) => putArcs(i, tile))
          .catch(() => undefined)
      }
    }
  }, [decadeIdx, meta, hexCache, arcCache, putHex, putArcs])

  const blendedHex = useMemo(() => {
    if (!meta) return []
    const a = hexCache.get(decadeIdx)
    const b = hexCache.get(Math.min(decadeIdx + 1, meta.decadeCount - 1))
    const maxCells = isPlaying ? 2200 : 4200
    return blendHexTiles(a, b, renderProgress, maxCells)
  }, [decadeIdx, renderProgress, hexCache, meta, isPlaying])

  const maxPop = useMemo(
    () => blendedHex.reduce((m, c) => (c.pop > m ? c.pop : m), 1),
    [blendedHex],
  )

  const blendedArcs = useMemo(() => {
    if (!meta) return []
    const a = arcCache.get(decadeIdx)
    const b = arcCache.get(Math.min(decadeIdx + 1, meta.decadeCount - 1))
    const topN = isPlaying ? 42 : 72
    return blendArcs(a, b, renderProgress, topN)
  }, [decadeIdx, renderProgress, arcCache, meta, isPlaying])

  const layers = useMemo(() => {
    const out: any[] = []
    if (showCountries) {
      out.push(countriesFillLayer())
      out.push(countriesGlowLayer())
    }
    if (showHex) {
      out.push(
        populationHexLayer({
          data: blendedHex,
          maxPop,
          opacity: hexOpacity,
          visible: true,
        }),
      )
    }
    if (showArcs) {
      out.push(
        migrationArcsLayer({
          data: blendedArcs,
          opacity: arcOpacity,
          visible: true,
        }),
      )
    }
    if (showLineage && lineages.length > 0) {
      out.push(
        ...lineageThreadsLayer({
          lineages,
          selectedId,
          hoveredId,
          currentYear: year,
          visible: true,
        }),
      )
    }
    return out
  }, [
    showCountries,
    showHex,
    showArcs,
    showLineage,
    blendedHex,
    blendedArcs,
    hexOpacity,
    arcOpacity,
    maxPop,
    lineages,
    selectedId,
    hoveredId,
    year,
  ])

  const view = useMemo(() => new GlobeView({ id: 'globe' }), [])

  return (
    <DeckGL
      views={view as any}
      viewState={viewState as any}
      controller={
        {
          dragRotate: true,
          scrollZoom: { speed: 0.01, smooth: true },
        } as any
      }
      onViewStateChange={((p: any) => {
        const next = { ...(p.viewState as typeof initialViewState) }
        next.zoom = Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, next.zoom))
        setViewState(next)
        return next
      }) as any}
      layers={layers}
      style={{ position: 'absolute', top: '0', left: '0', right: '0', bottom: '0' } as any}
    />
  )
}
