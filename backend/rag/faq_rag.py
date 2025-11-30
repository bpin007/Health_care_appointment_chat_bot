from .vector_store import VectorStore
from .embeddings import embed_text
import json
from pathlib import Path

class FAQ_RAG:
    def __init__(self):
        self.store = VectorStore()
        data_path = Path(__file__).resolve().parents[2] / "data" / "clinic_info.json"
        self.load_data(data_path)

    def load_data(self, path):
        with open(path, "r") as f:
            data = json.load(f)
        for item in data:
            self.store.add(item["question"] + " " + item["answer"], embed_text(item["question"]))

    def query(self, question: str):
        result = self.store.search(embed_text(question))
        return result[0]["text"]
