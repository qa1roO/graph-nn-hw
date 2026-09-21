"""Conservative, auditable graph normalization for display, not a replacement RAG index."""
from pathlib import Path
import hashlib
import json
import re
import unicodedata
import pandas as pd
import networkx as nx

VERSION = "metallurgy-v2"
TYPES = ["ХИМИЧЕСКИЙ_ЭЛЕМЕНТ", "МАТЕРИАЛ", "СОЕДИНЕНИЕ", "МИКРОСТРУКТУРА",
         "ТЕХНОЛОГИЧЕСКИЙ_ПРОЦЕСС", "СВОЙСТВО"]
ALIASES = {"NB": "НИОБИЙ", "V": "ВАНАДИЙ", "TI": "ТИТАН", "NBC": "КАРБИД НИОБИЯ"}
PROCESS_NAMES = {"РЕКРИСТАЛЛИЗАЦИЯ", "РЕКРИСТАЛЛИЗАЦИЯ АУСТЕНИТА", "РОСТ ЗЕРНА",
                 "ГОРЯЧАЯ ПРОКАТКА", "ТЕРМИЧЕСКАЯ ОБРАБОТКА"}
SUSPICIOUS = {"РАСТ", "РАСТВОРЕХА ЗЕРНА"}

def canonical(value):
    name = re.sub(r"\s+", " ", unicodedata.normalize("NFC", str(value)).replace("_", " ")).strip().upper()
    return ALIASES.get(name, name)

def items(value):
    if value is None or isinstance(value, float):
        return []
    if isinstance(value, str):
        return [value]
    return [str(x) for x in value]

def union(series):
    return sorted({x for value in series for x in items(value)})

def descriptions(series):
    return "\n\n".join(dict.fromkeys(str(x) for x in series if pd.notna(x) and str(x).strip()))

def normalize_graph(artifacts):
    artifacts = Path(artifacts)
    entities = pd.read_parquet(artifacts / "entities.parquet")
    relationships = pd.read_parquet(artifacts / "relationships.parquet")
    work = entities.copy()
    work["canonical"] = work["title"].map(canonical)
    audit, node_rows = [], []
    for name, group in work.groupby("canonical", sort=True):
        original_types = sorted(set(group["type"].dropna().astype(str)))
        kind = "ТЕХНОЛОГИЧЕСКИЙ_ПРОЦЕСС" if name in PROCESS_NAMES else (original_types[0] if len(original_types) == 1 else "НЕОДНОЗНАЧНО")
        reasons = []
        if kind not in TYPES:
            reasons.append("тип вне предметной области или конфликт типов")
        if name in SUSPICIOUS or not name:
            reasons.append("подозрительное название; проверить OCR")
        for row in group.to_dict("records"):
            audit.append({"original": row["title"], "canonical": name, "original_type": row["type"],
                          "type": kind, "status": "review" if reasons else "kept", "reason": "; ".join(reasons)})
        # Keep uncertain nodes in the derived data with explicit flags; do not guess corrections.
        node_rows.append({"id": name, "title": name, "type": kind,
                          "description": descriptions(group["description"]),
                          "text_unit_ids": union(group["text_unit_ids"]),
                          "aliases": sorted(set(group["title"].astype(str))),
                          "review_reason": "; ".join(reasons)})
    nodes = pd.DataFrame(node_rows, columns=["id", "title", "type", "description", "text_unit_ids", "aliases", "review_reason"])
    rel = relationships.copy()
    rel["source"] = rel["source"].map(canonical)
    rel["target"] = rel["target"].map(canonical)
    # Do not merge reverse edges: source/target order and descriptions are preserved.
    edge_rows = []
    for (source, target), group in rel.groupby(["source", "target"], sort=True):
        edge_rows.append({"id": hashlib.sha256((source + "\0" + target).encode()).hexdigest()[:20],
                          "source": source, "target": target, "description": descriptions(group["description"]),
                          "text_unit_ids": union(group["text_unit_ids"]),
                          "original_ids": sorted(group["id"].astype(str)),
                          "review_reason": "петля после объединения названий" if source == target else ""})
    edges = pd.DataFrame(edge_rows, columns=["id", "source", "target", "description", "text_unit_ids", "original_ids", "review_reason"])
    degree = pd.concat([edges["source"], edges["target"]]).value_counts()
    nodes["degree"] = nodes["title"].map(degree).fillna(0).astype(int)
    nodes["frequency"] = nodes["text_unit_ids"].map(len)
    units_path = artifacts / "text_units.parquet"
    units = pd.read_parquet(units_path).set_index("id")["text"].to_dict() if units_path.exists() else {}
    checks = []
    compact = lambda s: re.sub(r"\s+", " ", str(s)).strip()
    for row in edges.to_dict("records"):
        quotes = re.findall(r"Цитата:\s*«([^»]+)»", row["description"])
        texts = [units[x] for x in row["text_unit_ids"] if x in units]
        valid = sum(any(compact(q) in compact(t) for t in texts) for q in quotes)
        checks.append({**row, "quotes": quotes, "quotes_found": valid,
                       "evidence_status": "цитаты найдены; смысл проверить вручную" if quotes and valid == len(quotes)
                       else "нет цитаты" if not quotes else "часть цитат не найдена",
                       "source_text": "\n\n---\n\n".join(texts), "manual_verdict": "", "manual_note": ""})
    output = artifacts.parent / "normalized"
    output.mkdir(exist_ok=True)
    nodes.to_parquet(output / "entities.parquet", index=False)
    edges.to_parquet(output / "relationships.parquet", index=False)
    pd.DataFrame(audit).to_csv(output / "normalization_audit.csv", index=False, encoding="utf-8-sig")
    pd.DataFrame(checks).to_json(output / "relationship_review.json", orient="records", force_ascii=False, indent=2)
    # Separate blank review template, never overwrite a user's filled review.
    review_path = output / "manual_review.csv"
    if not review_path.exists():
        pd.DataFrame(checks).head(20).to_csv(review_path, index=False, encoding="utf-8-sig")
    graph = nx.MultiGraph()
    for row in nodes.to_dict("records"):
        graph.add_node(row["title"], type=row["type"], description=row["description"], review_reason=row["review_reason"])
    for row in edges.to_dict("records"):
        graph.add_edge(row["source"], row["target"], description=row["description"], text_unit_ids=json.dumps(row["text_unit_ids"]))
    nx.write_graphml(graph, output / "graph.graphml")
    stats = {"version": VERSION, "raw_nodes": len(entities), "nodes": len(nodes), "raw_edges": len(relationships),
             "edges": len(edges), "isolated_nodes": int((nodes["degree"] == 0).sum()),
             "nodes_to_review": int(nodes["review_reason"].ne("").sum()),
             "edges_without_quotes": sum(not x["quotes"] for x in checks)}
    (output / "quality_report.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    return output, stats
