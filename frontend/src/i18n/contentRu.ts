import type { HistoricalEvent, Lineage, LineagesFile, Meta } from '../types'
import { eventNameRu } from './eventsRu'

const REGION_NAME_RU: Record<string, string> = {
  gbr: 'Британские острова',
  fra: 'Франция',
  deu: 'Германия',
  nld: 'Нидерланды',
  esp: 'Иберия (Испания)',
  prt: 'Иберия (Португалия)',
  ita: 'Италия',
  sca: 'Скандинавия',
  pol: 'Польша',
  rus_eu: 'Европейская Россия',
  ukr: 'Украина',
  bal: 'Балканы',
  tur: 'Анатолия',
  lev: 'Левант',
  arab: 'Аравийский полуостров',
  per: 'Иранское нагорье',
  cas: 'Центральная Азия',
  mar: 'Магриб',
  egy: 'Египет',
  waf: 'Западная Африка',
  caf: 'Центральная Африка',
  eaf: 'Восточная Африка',
  hoa: 'Африканский Рог',
  saf: 'Южная Африка',
  ind_n: 'Северная Индия',
  ind_s: 'Южная Индия',
  ben: 'Бенгалия',
  pak: 'Инд / Пакистан',
  chn_n: 'Северный Китай',
  chn_s: 'Южный Китай',
  jpn: 'Япония',
  kor: 'Корея',
  twn: 'Тайвань',
  idn: 'Индонезия',
  phl: 'Филиппины',
  vnm: 'Вьетнам',
  tha: 'Материковая ЮВА',
  mly: 'Малайский полуостров',
  usa_ne: 'Северо-восток США',
  usa_ma: 'Среднеатлантический регион США',
  usa_se: 'Юго-восток США',
  usa_mw: 'Средний Запад США',
  usa_w: 'Запад США',
  can: 'Канада',
  mex: 'Мексика',
  cam: 'Центральная Америка',
  car: 'Карибский регион',
  bra_ne: 'Бразилия — северо-восток',
  bra_se: 'Бразилия — юго-восток',
  arg: 'Ла-Плата',
  and: 'Анды',
  aus: 'Австралия',
  nzl: 'Новая Зеландия',
  oce: 'Океания',
}

export function regionNameRu(regionId: string, fallbackName: string): string {
  return REGION_NAME_RU[regionId] ?? fallbackName
}

export function localizeEvent(event: HistoricalEvent): HistoricalEvent {
  return { ...event, name: eventNameRu(event) }
}

export function localizeMeta(meta: Meta): Meta {
  return {
    ...meta,
    regions: meta.regions.map((r) => ({ ...r, name: regionNameRu(r.id, r.name) })),
    events: meta.events.map(localizeEvent),
  }
}

function localizeLineage(lineage: Lineage): Lineage {
  const nodes = lineage.nodes.map((n) => ({ ...n, n: regionNameRu(n.r, n.n) }))
  const ordered = [...nodes].sort((a, b) => a.y - b.y)
  const start = ordered[0]?.n ?? ''
  const end = ordered[ordered.length - 1]?.n ?? ''
  return {
    ...lineage,
    title: start && end ? `${start} -> ${end}` : lineage.title,
    nodes,
  }
}

export function localizeLineages(file: LineagesFile): LineagesFile {
  return { lineages: file.lineages.map(localizeLineage) }
}

