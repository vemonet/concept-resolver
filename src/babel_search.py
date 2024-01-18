import os
import pandas as pd
from qdrant_client import QdrantClient
from qdrant_client.http.models import (
    Distance,
    FieldCondition,
    Filter,
    MatchText,
    PointStruct,
    UpdateResult,
    VectorParams,
    PointStruct,
    SearchParams,
)

from fastembed.embedding import FlagEmbedding as Embedding

# from qdrant_client.http.models import Filter, FieldCondition, Range, GeoBoundingBox, Point


# Initialize FastEmbed and Qdrant Client
embedding_model = Embedding(model_name="BAAI/bge-small-en-v1.5", max_length=512)
embedding_size = 384

# vectordb = QdrantClient(":memory:")
vectordb = QdrantClient(
    host="qdrant",
    prefer_grpc=True,
)


print(
    f"Qdrant VectorDB loaded with {vectordb.get_collection('concept-resolver').points_count} vectors"
)

search_query = "headache"
# search_query = "Skin structure of female perineum (body structure)"

query_embeddings = list(embedding_model.embed([search_query]))

hits = vectordb.search(
    collection_name="concept-resolver",
    query_vector=query_embeddings[0],
    limit=5,
)
for hit in hits:
    print(hit.payload, "score:", hit.score)
