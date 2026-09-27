# Результаты HW3: учебник Ганошенко

В Git сохранён один исходный граф и снимок каждого законченного запуска после предобработки. Эти файлы можно просматривать без рабочих каталогов `local_runs/` и `hw3_runs/`.

| Результат | До предобработки | После предобработки, запуск `ganoshenko-hw3-3248caaa7ac4` |
|---|---|---|
| Интерактивный просмотр | [graph.html](baseline/graph.html) | [graph.html](runs/ganoshenko-hw3-3248caaa7ac4/graph.html) |
| Данные графа GraphML | [graph.graphml](baseline/graph.graphml) | [graph.graphml](runs/ganoshenko-hw3-3248caaa7ac4/graph.graphml) |

GraphML — нормализованная версия графа, по которой считались метрики сравнения. HTML — сохранённая визуализация. Число вершин и связей само по себе не доказывает качество извлечения.

Метрики этого запуска:

- [Метрики этапов в Markdown](runs/ganoshenko-hw3-3248caaa7ac4/stage_metrics/stage_metrics.md) и [JSON](runs/ganoshenko-hw3-3248caaa7ac4/stage_metrics/stage_metrics.json).
- [Сравнение графов в Markdown](runs/ganoshenko-hw3-3248caaa7ac4/comparison/comparison.md) и [JSON](runs/ganoshenko-hw3-3248caaa7ac4/comparison/comparison.json).
- [Метрики поиска](runs/ganoshenko-hw3-3248caaa7ac4/comparison/retrieval.json) и [оценка покрытия LLM](runs/ganoshenko-hw3-3248caaa7ac4/comparison/llm_judge.json).
- [Отчёт подготовки](runs/ganoshenko-hw3-3248caaa7ac4/report.json), [аудит технических элементов](runs/ganoshenko-hw3-3248caaa7ac4/stage_metrics/technical_source_audit.csv) и [манифест файлов](runs/ganoshenko-hw3-3248caaa7ac4/manifest.json).

CER/WER и ручная оценка смысловой корректности связей здесь отсутствуют: эталонный текст PDF и ручная разметка ещё не подготовлены. Семь вопросов для поиска и LLM judge не измеряют покрытие всего учебника.

После следующего запуска выполните [`HW3_export_results.ipynb`](../../HW3_export_results.ipynb). Новый идентификатор запуска создаст новую папку в `runs/`; исходный граф останется в `baseline/`. Полные промежуточные файлы GraphRAG остаются только в локальных рабочих папках.
