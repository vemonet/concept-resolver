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
import time

start_time = time.time()

# Initialize embedding model and vectordb client
flag_embeddings = Embedding(model_name="BAAI/bge-small-en-v1.5", max_length=512)
flag_embeddings_size = 384

# NOTE: fastembed supports flag (5th MTEB) and jinaai: https://qdrant.github.io/fastembed/examples/Supported_Models/
# BioBERT: https://pypi.org/project/biobert-embedding/
# Angle embedding (2nd MTEB): https://huggingface.co/WhereIsAI/UAE-Large-V1


vectordb = QdrantClient(
    host="qdrant",
    prefer_grpc=True,
)


# TODO: load multiple vectors per point?
# We can upload vectors in a point by name: https://qdrant.tech/documentation/concepts/points/
# But the different vectors name need to be set at collection creation
# https://blog.qdrant.tech/storing-multiple-vectors-per-object-in-qdrant-c1da8b1ad727
vectordb.recreate_collection(
    collection_name="concept-resolver",
    vectors_config=VectorParams(size=flag_embeddings_size, distance=Distance.COSINE),
)

# Directory containing the .txt files
synonym_dir = "data/synonyms"
chunk_size = 100000

points_count = 0
for filename in os.listdir(synonym_dir):
    if filename.endswith(".txt"):
        # print(f"Loading {filename}")
        file_path = os.path.join(synonym_dir, filename)
        category = filename.replace(".txt", "")

        # {"curie": "UMLS:C4085944", "names": ["ATIR101", "allodepleted T cell immunotherapeutic ATIR101", "Allodepleted T Cell Immunotherapeutic ATIR101"], "types": ["Cell", "AnatomicalEntity", "PhysicalEssence", "OrganismalEntity", "SubjectOfInvestigation", "BiologicalEntity", "ThingWithTaxon", "NamedThing", "Entity", "PhysicalEssenceOrOccurrent"], "preferred_name": "Allodepleted T Cell Immunotherapeutic ATIR101", "shortest_name_length": 7}

        chunk_data = []
        with open(file_path, "r") as file:
            for line in tqdm(file, desc=f"Loading {filename}"):
                json_obj = json.loads(line)
                if "preferred_name" not in json_obj or "names" not in json_obj:
                    continue
                curie = json_obj["curie"]
                labels = json_obj["names"]
                # print(line)
                preferred_name = json_obj["preferred_name"]

                if preferred_name not in labels:
                    labels.append(preferred_name)

                for label_to_embed in labels:
                    chunk_data.append(
                        (
                            curie,
                            label_to_embed,
                            json_obj["types"],
                            json_obj["preferred_name"],
                            json_obj["names"],
                        )
                    )

                if len(chunk_data) >= chunk_size:
                    # Process the chunk
                    labels = [item[1] for item in chunk_data]
                    embeddings = list(flag_embeddings.embed(labels))
                    points = [
                        PointStruct(
                            id=points_count + i,
                            vector=embedding,
                            payload={
                                "id": chunk_data[i][0],
                                "label": chunk_data[i][3],
                                "synonyms": chunk_data[i][4],
                                "types": chunk_data[i][2],
                                "embedded_label": chunk_data[i][1],
                            },
                        )
                        for i, embedding in enumerate(embeddings)
                    ]
                    vectordb.upsert(collection_name="concept-resolver", points=points)
                    points_count += len(chunk_data)
                    chunk_data = []  # Reset the chunk data

        # Process any remaining data in the chunk
        if chunk_data:
            labels = [item[1] for item in chunk_data]
            embeddings = list(flag_embeddings.embed(labels))
            points = [
                PointStruct(
                    id=points_count + i,
                    vector=embedding,
                    payload={
                        "id": chunk_data[i][0],
                        "label": chunk_data[i][3],
                        "synonyms": chunk_data[i][4],
                        "types": chunk_data[i][2],
                        "embedded_label": chunk_data[i][1],
                    },
                )
                for i, embedding in enumerate(embeddings)
            ]
            vectordb.upsert(collection_name="concept-resolver", points=points)
            points_count += len(chunk_data)


time_taken = (end_time - start_time) / 60
print(f"Data processing and insertion completed in {time_taken}min")
