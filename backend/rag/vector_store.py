import math

class VectorStore:
    def __init__(self):
        self.store = []

    def add(self, text, embedding):
        self.store.append({
            "text": text,
            "embedding": embedding
        })

    def _cosine_similarity(self, a, b):
        """Compute cosine similarity between two vectors."""
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(y * y for y in b))

        if norm_a == 0 or norm_b == 0:
            return 0.0  # avoid division by zero

        return dot / (norm_a * norm_b)

    def search(self, query_embedding):
        """Return top 3 most similar items."""
        results = []

        for item in self.store:
            score = self._cosine_similarity(query_embedding, item["embedding"])
            results.append({
                "text": item["text"],
                "score": score
            })

        # Sort by similarity (highest first)
        results.sort(key=lambda x: x["score"], reverse=True)

        # Return top 3 results
        return results[:3]
