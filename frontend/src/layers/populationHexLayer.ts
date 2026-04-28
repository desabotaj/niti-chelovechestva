import { H3HexagonLayer } from '@deck.gl/geo-layers'
import type { BlendedHex } from '../data/interpolation'
import { CONTINENT_COLORS, colorForPopulationDensity, lerpRgba } from '../utils/colors'

export interface HexLayerOpts {
  data: BlendedHex[]
  maxPop: number
  opacity: number
  visible: boolean
}

export function populationHexLayer({ data, maxPop, opacity, visible }: HexLayerOpts) {
  return new H3HexagonLayer<BlendedHex>({
    id: 'population-hex',
    data,
    getHexagon: (d) => d.h,
    getFillColor: (d) => {
      const t = Math.min(1, d.pop / Math.max(maxPop, 1))
      const popColor = colorForPopulationDensity(t, 230)
      const contColor = CONTINENT_COLORS[d.cont] ?? [255, 255, 255, 220]
      const blend = lerpRgba(contColor, popColor, 0.85)
      blend[3] = Math.round(80 + 175 * t)
      return blend
    },
    pickable: false,
    extruded: false,
    filled: true,
    stroked: false,
    coverage: 0.96,
    opacity,
    visible,
    updateTriggers: {
      getFillColor: maxPop,
    },
    parameters: {
      depthTest: false,
      blendFunc: [770, 1] as any, // SRC_ALPHA, ONE — additive
    } as any,
  })
}
