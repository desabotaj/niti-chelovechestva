# Архитектура

Проект построен как трехэтапный конвейер:

1. **Генерация** синтетических данных  
2. **Агрегация** для визуализации  
3. **Экспорт** в статические тайлы для фронтенда

## Общий поток

```mermaid
flowchart LR
    subgraph stage1 [Этап 1 — Генерация]
        events[events.yaml] --> pop[population.py]
        geo[geography.py] --> pop
        pop --> individuals[individuals.parquet]
        pop --> migrations[migrations.parquet]
    end

    subgraph stage2 [Этап 2 — Агрегация]
        individuals --> hex[hex_agg.parquet]
        individuals --> lineages[lineages.parquet]
        migrations --> arcs[arcs.parquet]
    end

    subgraph stage3 [Этап 3 — Экспорт]
        hex --> hexjson[hex_NN.json]
        arcs --> arcsjson[arcs_NN.json]
        lineages --> lineagesjson[lineages.json]
        events --> meta[meta.json]
    end

    subgraph web [Фронтенд]
        hexjson --> globe[deck.gl GlobeView]
        arcsjson --> globe
        lineagesjson --> globe
        meta --> globe
    end
```

## Бэкенд

### Два движка генерации

- `pipeline.local_generate` — локальный Python/NumPy/Parquet путь;
- `pipeline.spark_generate` — PySpark-путь для масштабирования.

Оба используют общие ядра генерации из `generator/spawn.py`, чтобы
результат был консистентным.

### Почему это масштабируется

Ключевая единица вычисления — когорта `(decade_idx, region_idx)`.
Когорты независимы, поэтому генерация почти «embarrassingly parallel»:
минимум shuffle и межпроцессных зависимостей.

### Агрегация

DuckDB + H3 extension:

- быстро считает плотности и топ-дуги;
- читает Parquet напрямую;
- не требует отдельного сервера.

## Фронтенд

Стек:

- React + TypeScript + Vite
- deck.gl (`GlobeView`, `H3HexagonLayer`, `ArcLayer`, `PathLayer`)
- Zustand (состояние)
- Tailwind + Framer Motion (UI/анимации)

Слои рендера:

1. контуры/заливка стран
2. H3-плотность населения
3. дуги миграций
4. родовые линии + endpoint-маркеры

## Поток данных в браузере

```mermaid
flowchart TD
    boot[Запуск приложения] --> load[Загрузка meta + lineages]
    load --> cache[Кэш в Zustand]
    cache --> timeline[TimeSlider]
    timeline --> prefetch[Подгрузка текущей/соседних декад]
    prefetch --> layers[Пересчет слоев]
    layers --> render[Рендер globe]
```

Тайлы загружаются лениво и кэшируются (`loader.dedupe`), чтобы не делать
повторных запросов.

## Причины выбора стека

- **PySpark**: горизонтальное масштабирование без переписывания логики.
- **DuckDB + H3**: быстрые OLAP-агрегации и геопривязка в SQL.
- **Parquet + партиции по декадам**: дешевые выборки по времени.
- **deck.gl**: GPU-рендер больших объемов геоданных.
- **Статические JSON-тайлы**: простой деплой (CDN/статический хостинг).
