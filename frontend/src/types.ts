export type Continent = 'Europe' | 'MENA' | 'Africa' | 'Asia' | 'Americas' | 'Oceania'

export interface Region {
  id: string
  name: string
  lat: number
  lon: number
  continent: Continent
}

export interface HistoricalEvent {
  id: string
  name: string
  start: number
  end: number
  type: string
  regions: string[]
}

export interface Meta {
  version: number
  startYear: number
  endYear: number
  decades: number[]
  decadeCount: number
  regions: Region[]
  ethnoGroups: string[]
  events: HistoricalEvent[]
}

export interface HexCell {
  h: string
  p: number
  c: Continent
}

export interface HexTile {
  d: number
  cells: HexCell[]
}

export interface ArcEnd {
  id: string
  name: string
  lat: number
  lon: number
  cont: Continent
}

export interface ArcRecord {
  from: ArcEnd
  to: ArcEnd
  n: number
  cause: string
}

export interface ArcsTile {
  d: number
  year: number
  arcs: ArcRecord[]
}

export interface LineageNode {
  d: number
  y: number
  r: string
  n: string
  c: Continent
  lat: number
  lon: number
}

export interface Lineage {
  id: number
  title: string
  span: [number, number]
  nodes: LineageNode[]
}

export interface LineagesFile {
  lineages: Lineage[]
}

export interface EventTimelineYear {
  year: number
  names: string[]
}

export interface EventTimelineFile {
  yearly: EventTimelineYear[]
}
