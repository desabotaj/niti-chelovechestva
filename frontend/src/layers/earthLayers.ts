import { GeoJsonLayer } from '@deck.gl/layers'
import * as topojson from 'topojson-client'
import type { FeatureCollection, Geometry } from 'geojson'
import worldData from 'world-atlas/countries-110m.json'

type CountriesGeo = FeatureCollection<Geometry, { name?: string }>

let _countries: CountriesGeo | null = null

export function getCountriesGeo(): CountriesGeo {
  if (_countries) return _countries
  const topo = worldData as unknown as Parameters<typeof topojson.feature>[0]
  const fc = topojson.feature(topo, (topo as any).objects.countries) as unknown as CountriesGeo
  _countries = fc
  return fc
}

export function countriesFillLayer() {
  return new GeoJsonLayer({
    id: 'earth-countries-fill',
    data: getCountriesGeo() as any,
    getFillColor: [22, 28, 56, 255],
    getLineColor: [60, 78, 130, 220],
    lineWidthMinPixels: 0.5,
    stroked: true,
    filled: true,
    pickable: false,
    parameters: { depthTest: false } as any,
  })
}

export function countriesGlowLayer() {
  return new GeoJsonLayer({
    id: 'earth-countries-glow',
    data: getCountriesGeo() as any,
    getFillColor: [0, 0, 0, 0],
    getLineColor: [110, 130, 220, 110],
    lineWidthMinPixels: 1.6,
    stroked: true,
    filled: false,
    pickable: false,
    parameters: { depthTest: false } as any,
  })
}
