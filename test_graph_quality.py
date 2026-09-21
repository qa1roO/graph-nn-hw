import tempfile
import unittest
from pathlib import Path
import pandas as pd
from graph_quality import canonical, normalize_graph


class QualityTests(unittest.TestCase):
    def test_aliases_do_not_merge_compounds(self):
        self.assertEqual(canonical("горячая_прокатка"), "ГОРЯЧАЯ ПРОКАТКА")
        self.assertEqual(canonical("Nb"), "НИОБИЙ")
        self.assertNotEqual(canonical("NbC"), canonical("Nb"))
        self.assertEqual(canonical("РАСТ"), "РАСТ")  # No speculative OCR correction.

    def test_merge_provenance_and_quote_verification(self):
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmp:
            p = Path(tmp) / "artifacts"
            p.mkdir()
            pd.DataFrame([
                {"title": "Nb", "type": "ХИМИЧЕСКИЙ_ЭЛЕМЕНТ", "description": "A", "text_unit_ids": ["a"]},
                {"title": "НИОБИЙ", "type": "ХИМИЧЕСКИЙ_ЭЛЕМЕНТ", "description": "B", "text_unit_ids": ["b"]},
                {"title": "СТАЛЬ", "type": "МАТЕРИАЛ", "description": "C", "text_unit_ids": ["a"]},
                {"title": "АВТОР", "type": "ПЕРСОНА", "description": "D", "text_unit_ids": ["a"]},
            ]).to_parquet(p / "entities.parquet")
            pd.DataFrame([
                {"id": "1", "source": "Nb", "target": "СТАЛЬ", "description": "Цитата: «Ниобий в стали»", "text_unit_ids": ["a"]},
                {"id": "2", "source": "НИОБИЙ", "target": "СТАЛЬ", "description": "Цитата: «вымышленная цитата»", "text_unit_ids": ["b"]},
            ]).to_parquet(p / "relationships.parquet")
            pd.DataFrame([{"id": "a", "text": "Ниобий в стали"}, {"id": "b", "text": "Другой текст"}]).to_parquet(p / "text_units.parquet")
            out, stats = normalize_graph(p)
            self.assertEqual((stats["nodes"], stats["edges"]), (3, 1))
            edges = pd.read_parquet(out / "relationships.parquet")
            self.assertEqual(set(edges.iloc[0].text_unit_ids), {"a", "b"})
            review = pd.read_json(out / "relationship_review.json")
            self.assertEqual(review.iloc[0].quotes_found, 1)
            self.assertEqual(stats["nodes_to_review"], 1)
            self.assertEqual(len(pd.read_parquet(p / "entities.parquet")), 4)
            (out / "manual_review.csv").write_text("USER REVIEW", encoding="utf-8")
            normalize_graph(p)
            self.assertEqual((out / "manual_review.csv").read_text(), "USER REVIEW")


if __name__ == "__main__":
    unittest.main()
