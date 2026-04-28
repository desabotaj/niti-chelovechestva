import { ArcLayer } from '@deck.gl/layers'
import type { BlendedArc } from '../data/interpolation'
import { colorForArcDirection } from '../utils/colors'

export interface ArcsLayerOpts {
  data: BlendedArc[]
  opacity: number
  visible: boolean
  highlightCause?: string | null
}

export function migrationArcsLayer({ data, opacity, visible, highlightCause }: ArcsLayerOpts) {
  return new ArcLayer<BlendedArc>({
    id: 'migration-arcs',
    data,
    getSourcePosition: (d) => [d.from.lon, d.from.lat],
    getTargetPosition: (d) => [d.to.lon, d.to.lat],
    getSourceColor: (d) => {
      const dim = highlightCause && d.cause !== highlightCause ? 0.18 : 1
      const c = colorForArcDirection(d.to.lon - d.from.lon, d.intensity, 220)
      c[3] = Math.round(c[3] * dim)
      return c
    },
    getTargetColor: (d) => {
      const dim = highlightCause && d.cause !== highlightCause ? 0.18 : 1
      const c = colorForArcDirection(d.to.lon - d.from.lon, d.intensity, 255)
      c[0] = Math.min(255, c[0] + 30)
      c[1] = Math.min(255, c[1] + 20)
      c[2] = Math.min(255, c[2] + 30)
      c[3] = Math.round(c[3] * dim)
      return c
    },
    getWidth: (d) => 0.4 + Math.sqrt(d.intensity) * 2.6,
    getHeight: (d) => 0.18 + 0.4 * d.intensity,
    greatCircle: true,
    widthMinPixels: 0.6,
    widthMaxPixels: 4.5,
    opacity,
    visible,
    pickable: true,
    updateTriggers: {
      getSourceColor: highlightCause,
      getTargetColor: highlightCause,
    },
    parameters: {
      depthTest: false,
      blendFunc: [770, 1] as any, // additive
    } as any,
  })
}
