import logging
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.prompts import retrieve_context


class DummyChroma:
    def __init__(self, results):
        self.results = results
        self.calls = []

    def similarity_search_with_score(self, query, k):
        self.calls.append((query, k))
        return self.results[:k]


def test_retrieve_context_filters_on_distance_and_logs_top_result(caplog):
    db = DummyChroma(
        [
            (SimpleNamespace(page_content="relevant context"), 0.12),
            (SimpleNamespace(page_content="less relevant"), 0.85),
        ]
    )

    with caplog.at_level(logging.INFO):
        contexts = retrieve_context(db, "first question", top_k=2, threshold=0.5)

    assert contexts == ["relevant context"]
    assert ("first question", 2) in db.calls
    assert "Top result distance 0.1200" in caplog.text
