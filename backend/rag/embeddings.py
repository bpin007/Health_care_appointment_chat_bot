"""
Lightweight embedding alternative without PyTorch dependency.
Uses OpenAI API or a simple TF-IDF approach.
"""
import os
from typing import List

# Option 1: Using OpenRouter API (requires OPENROUTER_API_KEY environment variable)
def embed_text_openai(text: str) -> List[float]:
    """
    Generate embeddings using OpenRouter's API.
    Requires: pip install openai
    """
    try:
        from openai import OpenAI
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        
        response = client.embeddings.create(
            model="text-embedding-3-small",  # OpenAI model via OpenRouter
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"OpenRouter embedding error: {e}")
        return embed_text_fallback(text)


# Option 2: Simple TF-IDF based approach (no external API needed)
def embed_text_tfidf(text: str, dimension: int = 384) -> List[float]:
    """
    Simple hash-based embedding for development/testing.
    Not as accurate as transformer models but works without dependencies.
    Requires: pip install scikit-learn
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.decomposition import TruncatedSVD
    import numpy as np
    
    # Create a simple vectorizer
    vectorizer = TfidfVectorizer(max_features=1000)
    
    # Fit and transform (in production, you'd fit once on your corpus)
    try:
        vector = vectorizer.fit_transform([text]).toarray()[0]
        
        # Pad or truncate to desired dimension
        if len(vector) < dimension:
            vector = np.pad(vector, (0, dimension - len(vector)))
        else:
            vector = vector[:dimension]
            
        return vector.tolist()
    except:
        return embed_text_fallback(text)


# Option 3: Ultra-simple fallback (deterministic hash-based)
def embed_text_fallback(text: str, dimension: int = 384) -> List[float]:
    """
    Fallback embedding using simple hashing.
    Good enough for development but not recommended for production.
    """
    import hashlib
    import struct
    
    # Create deterministic embedding from text hash
    hash_obj = hashlib.sha256(text.encode())
    hash_bytes = hash_obj.digest()
    
    # Convert to floats
    embedding = []
    for i in range(0, len(hash_bytes) - 3, 4):
        val = struct.unpack('f', hash_bytes[i:i+4])[0]
        embedding.append(val)
    
    # Pad or truncate to dimension
    while len(embedding) < dimension:
        embedding.extend(embedding[:min(len(embedding), dimension - len(embedding))])
    
    return embedding[:dimension]


# Main function - choose your preferred method
def embed_text(text: str) -> List[float]:
    """
    Generate embeddings. Choose one of the methods above.
    """
    # Try OpenRouter first if API key is available
    if os.getenv("OPENROUTER_API_KEY"):
        return embed_text_openai(text)
    
    # Fall back to TF-IDF
    try:
        return embed_text_tfidf(text)
    except ImportError:
        # Ultimate fallback
        return embed_text_fallback(text)


# If you still want to use sentence-transformers but avoid the DLL issue,
# you can try using ONNX runtime instead:
def embed_text_onnx(text: str) -> List[float]:
    """
    Use ONNX runtime which often has fewer DLL issues.
    Requires: pip install optimum[onnxruntime] sentence-transformers
    """
    try:
        from optimum.onnxruntime import ORTModelForFeatureExtraction
        from transformers import AutoTokenizer
        import torch
        
        model_id = "sentence-transformers/all-MiniLM-L6-v2"
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = ORTModelForFeatureExtraction.from_pretrained(model_id, export=True)
        
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        outputs = model(**inputs)
        
        # Mean pooling
        embeddings = outputs.last_hidden_state.mean(dim=1)
        return embeddings[0].detach().numpy().tolist()
    except Exception as e:
        print(f"ONNX embedding error: {e}")
        return embed_text_fallback(text)