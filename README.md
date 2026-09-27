# Учебные графы из учебников

Репозиторий содержит исходный эксперимент GraphRAG (HW2) и сравнение с графом после предобработки текста (HW3).

## Структура

| Путь | Назначение |
|---|---|
| [`hw3/HW3_pipeline.ipynb`](hw3/HW3_pipeline.ipynb) | Основной ноутбук HW3: очистка, деление, токенизация, GraphRAG, векторизация и сравнение. |
| [`hw3/HW3_metrics.ipynb`](hw3/HW3_metrics.ipynb) | Единый отчёт с метриками этапов, поиска и сравнения графов. |
| [`hw3/graphs/`](hw3/graphs/) | Графы до и после предобработки: GraphML и HTML. |
| [`hw3/README.md`](hw3/README.md) | Подробное описание этапов, результатов и соответствия лекции. |
| [`hw3/retrieval_probes.json`](hw3/retrieval_probes.json) | Вопросы для дополнительной проверки поиска. |
| [`hw2/graphtheory-hw2-local.ipynb`](hw2/graphtheory-hw2-local.ipynb), [`hw2/graph-viewer.ipynb`](hw2/graph-viewer.ipynb) | Ноутбуки исходного эксперимента и просмотра графа. |
| [`hw2/README.md`](hw2/README.md) | Инструкция к исходному локальному запуску. |
| [`hw2/graphtheory-hw2-kaggle.ipynb`](hw2/graphtheory-hw2-kaggle.ipynb) | Сохранённый первоначальный Kaggle-ноутбук. |
| `graph_quality.py`, `resume_embeddings.py`, `prompts/`, `Modelfile.*` | Общие компоненты исходного запуска, используемые также в HW3. |
| `ganoshenko.md`, `vanadiy_review.md` | Исходные Markdown после MinerU. |
| `local_runs/`, `hw3_runs/` | Рабочие файлы GraphRAG и промежуточные данные; исключены из Git. |

Общие скрипты и входные учебники остаются в корне: оба сценария используют их по этим путям. Ноутбуки HW2 определяют корень проекта независимо от того, открыт Jupyter из корня или из `hw2/`.

## Запуск HW3

Из корня репозитория в PowerShell:

```powershell
$env:UV_CACHE_DIR = ".uv-cache"
uv sync --locked
uv run jupyter lab hw3/HW3_pipeline.ipynb
```

Выбери ядро `Python (graph-hw)` и выполняй ячейки последовательно. По умолчанию запускаются только подготовка и проверка входа GraphRAG. Для полного построения графа измени `RUN_FULL_INDEX` на `True` в разделе 5 ноутбука; проверка поиска и оценка Qwen включаются отдельно в разделах 7 и 8. Подробности и ограничения приведены в [описании HW3](hw3/README.md).

После завершения GraphRAG открой `hw3/HW3_metrics.ipynb` и выполни все ячейки. Итоги отображаются и сохраняются прямо в ноутбуке. Для CER/WER потребуется заполнить `gold_text` в созданном шаблоне `cleaning_gold.csv`. Графы для сдачи лежат в `hw3/graphs/`; после нового полного запуска обнови четыре файла этой папки из рабочих запусков.
