"""Resume only embedding generation using the saved graph and cached responses."""
import argparse
import asyncio
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import time

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
from graphrag.api.index import build_index
from graphrag.config.load_config import load_config


async def resume(project, embedding_model=None):
    project = Path(project).resolve()
    cfg = load_config(project)
    artifacts = Path(cfg.output_storage.base_dir)
    tables = [artifacts / (name + ".parquet") for name in ["entities", "relationships", "text_units"]]
    for path in tables:
        if not path.is_file():
            raise FileNotFoundError(f"Missing saved graph table: {path}")
    before = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in tables}
    backup = project / "recovery" / datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    backup.mkdir(parents=True)
    for name in ["stats.json", "context.json"]:
        if (artifacts / name).exists():
            shutil.copy2(artifacts / name, backup / name)
    cfg.workflows = ["generate_text_embeddings"]
    cfg.reporting.base_dir = str(backup / "reports")
    from graphrag_llm.config.retry_config import RetryConfig
    for model in cfg.embedding_models.values():
        model.retry = RetryConfig(type="exponential_backoff", max_retries=3, base_delay=2.0, max_delay=10.0)
        if embedding_model:
            model.model = embedding_model
    started = time.monotonic()
    print("Resuming embeddings only; saved graph and cache retained.", flush=True)
    outputs = await build_index(cfg)
    errors = [str(o.error) for o in outputs if o.error is not None]
    after = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in tables}
    if before != after:
        raise RuntimeError("Saved graph tables unexpectedly changed")
    report = {"success": not errors, "seconds": time.monotonic() - started,
              "embedding_model": cfg.embedding_models[cfg.embed_text.embedding_model_id].model,
              "errors": errors, "graph_tables_unchanged": before == after,
              "original_stats_backup": str(backup / "stats.json")}
    (backup / "result.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    # Keep the original full-run timing; the recovery has its own statistics.
    if (artifacts / "stats.json").exists():
        shutil.copy2(artifacts / "stats.json", backup / "resume_stats.json")
    if (backup / "stats.json").exists():
        shutil.copy2(backup / "stats.json", artifacts / "stats.json")
    if errors:
        raise RuntimeError(f"Embedding recovery failed: {errors}. See {backup}")
    print(f"Embeddings completed in {report['seconds']:.1f}s. Graph tables unchanged.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("project")
    parser.add_argument("--embedding-model", default=None)
    args = parser.parse_args()
    asyncio.run(resume(args.project, args.embedding_model))
