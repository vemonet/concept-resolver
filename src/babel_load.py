import os
import json
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
flag_embeddings = Embedding(model_name="BAAI/bge-small-en-v1.5", max_length=512)
flag_embeddings_size = 384

# fastembed supports flag (5th MTEB) and jinaai: https://qdrant.github.io/fastembed/examples/Supported_Models/
# BioBERT: https://pypi.org/project/biobert-embedding/
# Angle embedding (2nd MTEB): https://huggingface.co/WhereIsAI/UAE-Large-V1

# vectordb = QdrantClient(":memory:")
# vectordb = QdrantClient(path="data/vectordb")
vectordb = QdrantClient(
    url="https://qdrant.blah.137.120.31.102.nip.io",
    # host="qdrant",
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

points_count = 0
for filename in os.listdir(synonym_dir):
    if filename.endswith(".txt"):
        # print(f"Loading {filename}")
        file_path = os.path.join(synonym_dir, filename)
        category = filename.replace('.txt', '')

        # {"curie": "UMLS:C4085944", "names": ["ATIR101", "allodepleted T cell immunotherapeutic ATIR101", "Allodepleted T Cell Immunotherapeutic ATIR101"], "types": ["Cell", "AnatomicalEntity", "PhysicalEssence", "OrganismalEntity", "SubjectOfInvestigation", "BiologicalEntity", "ThingWithTaxon", "NamedThing", "Entity", "PhysicalEssenceOrOccurrent"], "preferred_name": "Allodepleted T Cell Immunotherapeutic ATIR101", "shortest_name_length": 7}

        # Stream the file
        # tqdm(os.listdir(synonym_dir), desc="Processing files")
        # for chunk in tqdm(pd.read_csv(file_path, sep='\t', header=None, chunksize=chunk_size), desc=f"Loading {filename}"):
        with open(file_path, 'r') as file:
            for line in tqdm(file, desc=f"Loading {filename}"):
                json_obj = json.loads(line)
                curie = json_obj['curie']
                labels = json_obj['names']
                preferred_name = json_obj['preferred_name']

                if preferred_name not in labels:
                    labels.append(preferred_name)

                # print("Generating embeddings")
                # Generate embeddings
                embeddings = list(flag_embeddings.embed(labels))
                # print(f"Embeddings generated for {len(embeddings)}")
                # print(embeddings)
                # TODO: add other embeddings model? BioBERT?

                # Create points to be inserted in Qdrant
                points = [
                    PointStruct(id=points_count + i, vector=embedding, payload={
                        "id": curie, "label": label, "category": category
                    }) for i, (label, embedding) in enumerate(zip(labels, embeddings))
                ]
                points_count += len(labels)


                # Insert into Qdrant
                vectordb.upsert(
                    collection_name="concept-resolver",
                    points=points
                )
                # TODO: add milvus?

print("Data processing and insertion completed.")
