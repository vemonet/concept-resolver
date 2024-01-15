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
from tqdm import tqdm

from fastembed.embedding import FlagEmbedding as Embedding
# from qdrant_client.http.models import Filter, FieldCondition, Range, GeoBoundingBox, Point



# Initialize FastEmbed and Qdrant Client
flag_embeddings = Embedding(model_name="BAAI/bge-base-en", max_length=512)
flag_embeddings_size = 768

# fastembed supports flag (5th MTEB) and jinaai: https://qdrant.github.io/fastembed/examples/Supported_Models/
# BioBERT: https://pypi.org/project/biobert-embedding/
# Angle embedding (2nd MTEB): https://huggingface.co/WhereIsAI/UAE-Large-V1

# vectordb = QdrantClient(":memory:")
# vectordb = QdrantClient(path="data/vectordb")
vectordb = QdrantClient(
    host="localhost",
    # prefer_grpc=True,
)

vectordb.recreate_collection(
    collection_name="concept-resolver",
    vectors_config=VectorParams(size=flag_embeddings_size, distance=Distance.COSINE),
    # force_recreate=True,
)

# Directory containing the .txt files
synonym_dir = "data/synonyms"
chunk_size = 1000

for filename in os.listdir(synonym_dir):
    if filename.endswith(".txt"):
        # print(f"Loading {filename}")
        file_path = os.path.join(synonym_dir, filename)
        category = filename.replace('.txt', '')

        points_count = 0
        # Stream the file
        # tqdm(os.listdir(synonym_dir), desc="Processing files")
        for chunk in tqdm(pd.read_csv(file_path, sep='\t', header=None, chunksize=chunk_size), desc=f"Loading {filename}"):
            curies = chunk[0].tolist()
            labels = chunk[2].tolist()

            # print("Generating embeddings")
            # Generate embeddings
            embeddings = list(flag_embeddings.embed(labels))
            # print(f"Embeddings generated for {len(embeddings)}")
            # print(embeddings)
            # TODO: add other embeddings model? BioBERT?

            # Create points to be inserted in Qdrant
            points = [
                PointStruct(id=points_count + i, vector=embedding, payload={"id": curie, "label": label, "category": category})
                for i, (curie, label, embedding) in enumerate(zip(curies, labels, embeddings))
            ]
            points_count += chunk_size


            # Insert into Qdrant
            vectordb.upsert(
                collection_name="concept-resolver",
                points=points
            )
            # TODO: add milvus?

print("Data processing and insertion completed.")
