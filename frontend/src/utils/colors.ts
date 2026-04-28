import { interpolateRgbBasis } from 'd3-interpolate'
import { rgb, type RGBColor } from 'd3-color'
import { scaleLinear, scaleSqrt } from 'd3-scale'
import type { Continent } from '../types'

export type RGBA = [number, number, number, number]

const POPULATION_RAMP = [
  '#1a1d35', // very low
  '#312e81',
  '#4338ca',
  '#7e22ce',
  '#c026d3',
  '#f59e0b',
  '#fcd34d',
  '#fff7e6', // very high
]

const populationInterp = interpolateRgbBasis(POPULATION_RAMP)

export const populationColorScale = scaleSqrt<number, number>()
  .domain([0, 1])
  .range([0, 1])
  .clamp(true)

export function colorForPopulationDensity(t: number, alpha = 220): RGBA {
  const tt = populationColorScale(Math.max(0, Math.min(1, t)))
  const c = rgb(populationInterp(tt))
  return [Math.round(c.r), Math.round(c.g), Math.round(c.b), alpha]
}

export const CONTINENT_COLORS: Record<Continent, RGBA> = {
  Europe:   [220, 230, 255, 240],
  MENA:     [255, 220, 160, 240],
  Africa:   [255, 200, 130, 240],
  Asia:     [255, 170, 200, 240],
  Americas: [180, 240, 220, 240],
  Oceania:  [200, 200, 255, 240],
}

const ARC_RAMP = [
  '#22d3ee', // cyan — westward
  '#a78bfa', // violet — neutral
  '#fb7185', // rose — eastward
]
const arcInterp = interpolateRgbBasis(ARC_RAMP)

export function colorForArcDirection(deltaLon: number, intensity: number, alpha = 200): RGBA {
  const t = (Math.tanh(deltaLon / 90) + 1) * 0.5
  const c = rgb(arcInterp(t))
  return [
    Math.round(c.r),
    Math.round(c.g),
    Math.round(c.b),
    Math.round(alpha * Math.min(1, 0.4 + intensity * 0.6)),
  ]
}

export const THREAD_GLOW: RGBA = [253, 224, 71, 240]
export const THREAD_TAIL: RGBA = [251, 191, 36, 90]
export const THREAD_DIM: RGBA = [120, 113, 108, 120]

export const SELECTION_GLOW: RGBA = [255, 240, 200, 255]

export function rgbaToCss([r, g, b, a]: RGBA): string {
  return `rgba(${r}, ${g}, ${b}, ${(a / 255).toFixed(3)})`
}

export function lerpRgba(a: RGBA, b: RGBA, t: number): RGBA {
  return [
    Math.round(a[0] + (b[0] - a[0]) * t),
    Math.round(a[1] + (b[1] - a[1]) * t),
    Math.round(a[2] + (b[2] - a[2]) * t),
    Math.round(a[3] + (b[3] - a[3]) * t),
  ]
}

export const ALPHA_RAMP = scaleLinear<number, number>()
  .domain([0, 0.5, 1])
  .range([90, 200, 240])
  .clamp(true)

const _u: RGBColor | null = null
void _u
