# Модель данных

Все основные данные хранятся в Parquet (Snappy), с партиционированием
по `decade_idx`. Браузер Parquet не читает напрямую — фронтенд работает
с JSON-тайлами, подготовленными на этапе экспорта.

## Уровень 1 — сгенерированные таблицы

### `individuals.parquet`

Одна строка = один синтетический человек.

| Поле | Тип | Описание |
|------|-----|----------|
| `id` | INT64 | Упакованный ID `(decade, region, within)` |
| `birth_year` | INT16 | Год рождения |
| `death_year` | INT16 | Год смерти |
| `birth_region_idx` | INT8 | Индекс региона рождения |
| `birth_lat`, `birth_lon` | FLOAT32 | Координаты рождения (с джиттером) |
| `sex` | INT8 | Бинарный маркер пола |
| `parent1_id`, `parent2_id` | INT64 | Связи с родителями (или -1) |
| `birth_continent` | STRING | Денормализованный континент |
| `decade_idx` | INT32 | Партиционный ключ |

### `migrations.parquet`

Одна строка = одно миграционное событие.

| Поле | Тип | Описание |
|------|-----|----------|
| `person_id` | INT64 | ID человека |
| `year` | INT16 | Год перемещения |
| `from_region_idx`, `to_region_idx` | INT8 | Источник / цель |
| `from_lat/lon`, `to_lat/lon` | FLOAT32 | Геокоординаты |
| `cause_id` | INT32 | Код причины |
| `cause_label` | STRING | Текстовый label причины |
| `decade_idx` | INT32 | Партиционный ключ |

## Уровень 2 — агрегаты DuckDB/H3

### `hex_agg.parquet`

Агрегаты плотности населения в H3:

- `decade_idx`, `decade_year`
- `h3` (ячейка H3, res=3)
- `pop` (оценка живущих в декаде)
- `dominant_continent`

### `arcs.parquet`

Топ-дуги миграций на декаду:

- источник (`src_*`)
- назначение (`dst_*`)
- `migrations` (мощность потока)
- `top_cause` (доминирующая причина)

Ограничение: top-250 дуг на декаду.

### `lineages.parquet`

Выборка из 50 родовых линий:

- `lineage_id`
- `depth` (поколение)
- `person_id`
- `year`
- `region_*`
- `lat`, `lon`

## Уровень 3 — тайлы для фронтенда

Пишутся в `frontend/public/data/`:

- `meta.json` — метаданные (регионы, события, декады)
- `hex_NN.json` — плотность по декаде
- `arcs_NN.json` — дуги по декаде
- `lineages.json` — набор родовых линий
- `events_timeline.json` — события по годам (для ticker)

Для текущей конфигурации общий размер тайлов составляет ~14.8 МБ.

## Примеры запросов

Топ H3-ячеек по плотности в выбранной декаде:

```sql
SELECT h3, pop
FROM hex_agg.parquet
WHERE decade_idx = 39
ORDER BY pop DESC
LIMIT 50;
```

Самая мощная миграционная дуга в декаде:

```sql
SELECT src_name, dst_name, migrations, top_cause
FROM arcs.parquet
WHERE decade_idx = 36
ORDER BY migrations DESC
LIMIT 1;
```
