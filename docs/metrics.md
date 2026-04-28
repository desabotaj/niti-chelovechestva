# Метрики / Metrics

## RU

Все цифры ниже воспроизводимы локально через пайплайн генерации.

### Пресеты масштаба

| Пресет | Начальная популяция | Итого individuals | Цель migrations | Оценка времени | Диск (Parquet) |
|--------|----------------------|-------------------|-----------------|----------------|----------------|
| `tiny` | 20 K                 | 600 K             | ~365 K          | ~17 с          | ~22 МБ         |
| `small`| 200 K                | 6 M               | ~4 M            | ~1-3 мин       | ~220 МБ        |
| `medium` | 2 M                | 60 M              | ~40 M           | ~30 мин        | ~2 ГБ          |
| `big`  | 20 M                 | 600 M             | ~400 M          | кластер        | ~25 ГБ         |

### Измерения для `tiny`

Наблюдаемая последовательность:

- генерация: ~17.4 с
- агрегация: ~1.6 с
- экспорт: ~1.0 с
- итого: ~20 с

Агрегированные размеры:

- `hex_agg`: ~137k строк
- `arcs`: ~12.5k строк
- `lineages`: ~700 строк

### Фронтенд

- Суммарный размер файлов в `frontend/public/data`: ~14.8 МБ
- JS-бандл (gzip): ~410 КБ
- CSS (gzip): ~4.6 КБ

### Воспроизводимость

Seed проекта фиксирован:

- `GLOBAL_SEED = 20260429`

Это обеспечивает повторяемый результат генерации при одинаковых входных
параметрах и пресете масштаба.

### Масштабирование

При переходе от `medium` к `big`:

- генерация масштабируется по когортам `(decade_idx, region_idx)`;
- агрегация в DuckDB масштабируется близко к линейной по объему;
- стоимость фронтенда остается ограниченной за счет тайлов и top-N срезов.

---

## EN

All numbers below are reproducible locally through the generation pipeline.

### Scale presets

| Preset | Initial population | Total individuals | Migration target | Time estimate | Disk (Parquet) |
|--------|---------------------|-------------------|------------------|---------------|----------------|
| `tiny` | 20 K                | 600 K             | ~365 K           | ~17 s         | ~22 MB         |
| `small`| 200 K               | 6 M               | ~4 M             | ~1-3 min      | ~220 MB        |
| `medium` | 2 M               | 60 M              | ~40 M            | ~30 min       | ~2 GB          |
| `big`  | 20 M                | 600 M             | ~400 M           | cluster        | ~25 GB         |

### `tiny` measurements

Observed sequence:

- generation: ~17.4 s
- aggregation: ~1.6 s
- export: ~1.0 s
- total: ~20 s

Aggregate sizes:

- `hex_agg`: ~137k rows
- `arcs`: ~12.5k rows
- `lineages`: ~700 rows

### Frontend

- Total size of files in `frontend/public/data`: ~14.8 MB
- JS bundle (gzip): ~410 KB
- CSS (gzip): ~4.6 KB

### Reproducibility

Project seed is fixed:

- `GLOBAL_SEED = 20260429`

This guarantees repeatable generation output for the same input parameters
and scale preset.

### Scaling

When moving from `medium` to `big`:

- generation scales across cohorts `(decade_idx, region_idx)`;
- DuckDB aggregation scales close to linearly with data volume;
- frontend cost stays bounded via tiling and top-N slicing.
