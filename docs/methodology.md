# Методология / Methodology — синтетическая демография и миграции

## RU

В этой главе формализована генеративная модель проекта
**Threads of Humanity**. Исходный код находится в
[`backend/generator/`](../backend/generator).

### 1. Пространство и время

Мир разбит на 54 опорных региона (`geography.py`), каждый регион `R_i`
описывается:

| Обозначение | Смысл |
|-------------|-------|
| `(\phi_i, \lambda_i)` | центр региона (широта/долгота) |
| `\rho_i` | радиус джиттера (в градусах) |
| `w_i` | доля начальной популяции в 1525 г. |
| `e_i` | макроэтнокультурный вектор размерности 8 |
| `c_i` | континентальная метка |

Время дискретизируется декадами:

- `Y_d = 1525 + 10d`, `d = 0..49`.
- всего 50 декад.

### 2. Динамика населения

Для каждой пары (декада, регион) считается матрица населения:

`P in R^(50 x 54)`.

Эволюция задается логистической моделью с историческими шоками:

`P_{d,i} = P_{d-1,i} * (1 + n_{d,i} * L_{d,i})`

где:

- `n_{d,i}` — чистый темп роста;
- `L_{d,i}` — логистический ограничитель емкости среды.

Компоненты роста:

- базовые рождаемость/смертность меняются по времени;
- события из `events.yaml` модифицируют региональные коэффициенты:
  - `beta_{d,i}` — множитель рождаемости;
  - `mu_{d,i}` — множитель смертности.

Логистический ограничитель:

`L_{d,i} = clip(1 - P_{d-1,i}/K_{d,i}, -0.5, 1)`

где `K_{d,i}` растет со временем (эффект индустриализации).

### 3. Рождение когорты

Ожидаемое число новорожденных в `(d, i)`:

`W_{d,i} = b_d * 0.5*(P_{d-1,i}+P_{d,i}) * beta_{d,i}`

После нормализации `W` формируется распределение вероятностей, затем
целевое число записей `N_tot` распределяется методом **largest remainder**
(крупнейших остатков) так, чтобы сумма совпала точно.

Реализация: `cohort_plan_from_weights(...)`.

### 4. Длительность жизни

Длина жизни моделируется смесью двух распределений:

- инфантильная смертность `U(0, 8)` с вероятностью `p_infant(d)`;
- взрослая компонента `N(mu(d), sigma(d))` с отсечением `[10, 100]`.

С течением времени:

- `p_infant` снижается,
- средняя взрослая продолжительность жизни растет.

### 5. Синтетическая генеалогия

ID человека — упакованный 64-битный ключ:

`[6 бит decade][6 бит region][52 бит within_cohort_idx]`.

Для ребенка в когорте `(d, i)` выбираются два родителя:

1. Регион родителя выбирается по гауссовому ядру расстояний
   (ближайшие регионы вероятнее).
2. Декада родителя выбирается из смещения `{2, 3}` (20–30 лет).
3. Индекс внутри когорты выбирается равномерно с учетом размера когорты.

Если целевая когорта пуста, применяется fallback к непустой когорте
в той же/предыдущей декаде.

Это не «биологически точное» дерево, но структурно согласованный граф,
пригодный для глубокого lineage drill-in.

### 6. Миграционная модель

Вероятность потока из региона `i` в `j` в декаде `d`:

`Pi_{d,i,j} ∝ alpha*G_{d,i,j} + (1-alpha)*E_{d,i,j}`

где:

- `G` — gravity baseline (`pop_i * pop_j / (dist + d0)^2`);
- `E` — event pulls из `events.yaml` (`from -> to` с весами).

Если активны события, их вклад усиливается (`alpha = 0.3`), иначе
работает почти чистая gravity-схема (`alpha = 1.0`).

Интенсивность миграций также масштабируется числом активных событий
в текущей декаде.

### 7. Агрегация для визуализации

Сырые таблицы агрегируются в DuckDB:

- H3, resolution=3 (около 12k ячеек мира);
- плотность населения по декадам;
- топ-250 миграционных дуг на декаду;
- 50 «звездных» родовых линий (примерно 14 поколений).

Результат сохраняется в Parquet и затем экспортируется в JSON-тайлы
для фронтенда.

### 8. Воспроизводимость

Все случайные процедуры используют детерминированный seed:

`GLOBAL_SEED = 20260429`.

Сид комбинируется с `(decade_idx, region_idx, salt)`, поэтому генерация
параллелится без потери воспроизводимости.

### 9. Ограничения модели

- Модель оперирует макроэтническими признаками, а не языками/гаплогруппами.
- Родительские связи топологические, а не демографически «идеально реалистичные».
- Смертность «в пути» не моделируется отдельно.
- Емкость среды задана упрощенно.

Это осознанные упрощения: цель — масштабируемая и выразительная
синтетическая модель для data-art, а не реконструкция всех
историко-демографических деталей.

---

## EN

This chapter formalizes the generative model used in
**Threads of Humanity**. Source code lives in
[`backend/generator/`](../backend/generator).

### 1. Space and time

The world is partitioned into 54 anchor regions (`geography.py`), each region
`R_i` is defined by:

| Symbol | Meaning |
|-------------|-------|
| `(\phi_i, \lambda_i)` | region center (latitude/longitude) |
| `\rho_i` | jitter radius (degrees) |
| `w_i` | initial population share in 1525 |
| `e_i` | macro-ethnocultural vector of size 8 |
| `c_i` | continent label |

Time is discretized into decades:

- `Y_d = 1525 + 10d`, `d = 0..49`
- total of 50 decades

### 2. Population dynamics

For each (decade, region) pair, we compute:

`P in R^(50 x 54)`.

Evolution follows a logistic model with historical shocks:

`P_{d,i} = P_{d-1,i} * (1 + n_{d,i} * L_{d,i})`

where:

- `n_{d,i}` is net growth rate
- `L_{d,i}` is logistic carrying-capacity limiter

Growth components:

- baseline birth/death rates evolve over time
- events from `events.yaml` modify regional coefficients:
  - `beta_{d,i}` birth multiplier
  - `mu_{d,i}` death multiplier

Logistic limiter:

`L_{d,i} = clip(1 - P_{d-1,i}/K_{d,i}, -0.5, 1)`

where `K_{d,i}` grows over time (industrialization effect).

### 3. Cohort births

Expected newborn count in `(d, i)`:

`W_{d,i} = b_d * 0.5*(P_{d-1,i}+P_{d,i}) * beta_{d,i}`

After normalizing `W`, probabilities are built and the target record count
`N_tot` is allocated via **largest remainder** so totals match exactly.

Implementation: `cohort_plan_from_weights(...)`.

### 4. Lifespan

Lifespan is modeled as a two-component mixture:

- infant mortality `U(0, 8)` with probability `p_infant(d)`
- adult component `N(mu(d), sigma(d))` clipped to `[10, 100]`

Over time:

- `p_infant` decreases
- mean adult lifespan increases

### 5. Synthetic genealogy

Person ID is a packed 64-bit key:

`[6 bits decade][6 bits region][52 bits within_cohort_idx]`.

For each child in cohort `(d, i)`, two parents are sampled:

1. Parent region sampled by Gaussian distance kernel
   (nearby regions are more likely)
2. Parent decade sampled from offsets `{2, 3}` (20-30 years)
3. Within-cohort index sampled uniformly with cohort-size constraints

If a target cohort is empty, fallback selects a non-empty cohort in the same
or previous decade.

This is not a biologically exact family tree, but a structurally coherent graph
suitable for deep lineage drill-in.

### 6. Migration model

Flow probability from region `i` to `j` in decade `d`:

`Pi_{d,i,j} ∝ alpha*G_{d,i,j} + (1-alpha)*E_{d,i,j}`

where:

- `G` is gravity baseline (`pop_i * pop_j / (dist + d0)^2`)
- `E` is event pulls from `events.yaml` (`from -> to` with weights)

When events are active, event contribution is amplified (`alpha = 0.3`);
otherwise migration is near pure gravity (`alpha = 1.0`).

Migration intensity is also scaled by number of active events in the decade.

### 7. Visualization aggregation

Raw tables are aggregated in DuckDB:

- H3, resolution=3 (about 12k world cells)
- population density by decade
- top 250 migration arcs per decade
- 50 star lineages (about 14 generations each)

Results are stored in Parquet, then exported to JSON tiles for frontend.

### 8. Reproducibility

All random procedures use a deterministic seed:

`GLOBAL_SEED = 20260429`.

Seed is combined with `(decade_idx, region_idx, salt)`, enabling parallel
generation without losing reproducibility.

### 9. Model limitations

- Model uses macro-ethnic features, not languages/haplogroups.
- Parent links are topological, not perfectly demographic-realistic.
- In-transit mortality is not modeled separately.
- Carrying capacity is simplified.

These simplifications are intentional: the goal is a scalable, expressive
synthetic model for data-art, not full historical-demographic reconstruction.
