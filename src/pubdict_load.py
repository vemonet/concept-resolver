import os
from typing import Any
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

from fastembed.embedding import FlagEmbedding
# from qdrant_client.http.models import Filter, FieldCondition, Range, GeoBoundingBox, Point


import requests
from bs4 import BeautifulSoup


# Get all dicts: https://pubdictionaries.org/dictionaries?grid%5Border%5D=created_at&grid%5Border_direction%5D=desc&grid%5Bpp%5D=187

def extract_pubdictionaries(url):
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, 'html.parser')
    dictionary_names = []
    # Extracting dictionary names
    for td in soup.find_all('td'):
        link = td.find('a')
        if link and 'href' in link.attrs and link.attrs['href'].startswith("/dictionaries/"):
            dictionary_names.append(link.get_text(strip=True))
    return dictionary_names


def gen_embeddings(labels: list[str], embedding_model: Any, embedding_size: int):
    return list(embedding_model.embed(labels))


class OurEmbeddings:
    def __init__(self):
        """Initialize the Embedding object with a model and embedding size."""
        print("⏳ Downloading embedding model")
        self.embedding_model = FlagEmbedding(model_name="BAAI/bge-base-en", max_length=512)
        self.embedding_size = 768

    def embed(self, labels: list[str]):
        """
        Generate embeddings for the given input data using the specified model.
        This is a placeholder function and should be implemented according to the specific model's requirements.

        :param labels: The data for which embeddings are to be generated.
        :return: Embeddings for the input data.
        """
        return list(self.embedding_model.embed(labels))

embedding = OurEmbeddings()

vectordb = QdrantClient(
    url="https://qdrant.findy-curie.137.120.31.148.nip.io"
    # host="qdrant",
    # prefer_grpc=True,
)

vectordb.recreate_collection(
    collection_name="pubdictionaries-flag",
    vectors_config=VectorParams(size=embedding.embedding_size, distance=Distance.COSINE),
    # force_recreate=True,
)



url = "https://pubdictionaries.org/dictionaries?grid%5Border%5D=created_at&grid%5Border_direction%5D=desc&grid%5Bpp%5D=187"

# Extract and print dictionary names
dict_names = extract_pubdictionaries(url)

chunk_size = 1000
points_count = 0

for dict_name in dict_names:
    print(f"Processing {dict_name}")
    ddl_url = f"https://pubdictionaries.org/dictionaries/{dict_name}.tsv?mode=3"

    for df in pd.read_csv(ddl_url, sep='\t', chunksize=chunk_size):
        df = pd.read_csv(ddl_url, sep='\t')
        labels = df["#label"].tolist()
        ids = df["id"].tolist()
        print(labels)
        print(ids)
        embeddings = embedding.embed(labels)

        # Create points to be inserted in Qdrant
        points = [
            PointStruct(id=points_count + i, vector=embedding, payload={"id": label_id, "label": label, "dictionary": dict_name})
            for i, (label_id, label, embedding) in enumerate(zip(ids, labels, embeddings))
        ]
        points_count += chunk_size

        # Insert into Qdrant
        vectordb.upsert(
            collection_name="pubdictionaries-flag",
            points=points
        )

    # for line in pd.read_csv(ddl_url, sep='\t'):
    #     print(line)
    #     curies = chunk[0].tolist()
    #     labels = chunk[2].tolist()


# https://pubdictionaries.org/dictionaries/MeSH2022Disease.tsv?mode=3
# https://pubdictionaries.org/dictionaries/MeSH2022Disease/downloadable

# def gen_embeddings():

# def load_vectordb():



# # Initialize FastEmbed and Qdrant Client
# flag_embeddings = Embedding(model_name="BAAI/bge-base-en", max_length=512)
# flag_embeddings_size = 768

# # fastembed supports flag (5th MTEB) and jinaai: https://qdrant.github.io/fastembed/examples/Supported_Models/
# # BioBERT: https://pypi.org/project/biobert-embedding/
# # Angle embedding (2nd MTEB): https://huggingface.co/WhereIsAI/UAE-Large-V1

# # vectordb = QdrantClient(":memory:")
# # vectordb = QdrantClient(path="data/vectordb")
# vectordb = QdrantClient(
#     url="https://qdrant.findy-curie.137.120.31.148.nip.io"
#     # host="qdrant",
#     # prefer_grpc=True,
# )

# vectordb.recreate_collection(
#     collection_name="flag-concept-resolver",
#     vectors_config=VectorParams(size=flag_embeddings_size, distance=Distance.COSINE),
#     # force_recreate=True,
# )

# # Directory containing the .txt files
# synonym_dir = "data/synonyms"
# chunk_size = 1000

# points_count = 0
# for filename in os.listdir(synonym_dir):
#     if filename.endswith(".txt"):
#         # print(f"Loading {filename}")
#         file_path = os.path.join(synonym_dir, filename)
#         category = filename.replace('.txt', '')

#         # {"curie": "UMLS:C4085944", "names": ["ATIR101", "allodepleted T cell immunotherapeutic ATIR101", "Allodepleted T Cell Immunotherapeutic ATIR101"], "types": ["Cell", "AnatomicalEntity", "PhysicalEssence", "OrganismalEntity", "SubjectOfInvestigation", "BiologicalEntity", "ThingWithTaxon", "NamedThing", "Entity", "PhysicalEssenceOrOccurrent"], "preferred_name": "Allodepleted T Cell Immunotherapeutic ATIR101", "shortest_name_length": 7}

#         # Stream the file
#         # tqdm(os.listdir(synonym_dir), desc="Processing files")
#         # for chunk in tqdm(pd.read_csv(file_path, sep='\t', header=None, chunksize=chunk_size), desc=f"Loading {filename}"):
#         with open(file_path, 'r') as file:
#             for line in tqdm(file, desc=f"Loading {filename}"):
#                 json_obj = json.loads(line)
#                 curie = json_obj['curie']
#                 names = json_obj['names']
#                 preferred_name = json_obj['preferred_name']

#                 if preferred_name not in names:
#                     names.append(preferred_name)

#                 # print("Generating embeddings")
#                 # Generate embeddings
#                 embeddings = list(flag_embeddings.embed(labels))
#                 # print(f"Embeddings generated for {len(embeddings)}")
#                 # print(embeddings)
#                 # TODO: add other embeddings model? BioBERT?

#                 # Create points to be inserted in Qdrant
#                 points = [
#                     PointStruct(id=points_count + i, vector=embedding, payload={
#                         "id": curie, "label": label, "category": category
#                     }) for i, (name, embedding) in enumerate(zip(names, embeddings))
#                 ]
#                 points_count += len(names)


#                 # Insert into Qdrant
#                 vectordb.upsert(
#                     collection_name="concept-resolver",
#                     points=points
#                 )
#                 # TODO: add milvus?

# print("Data processing and insertion completed.")
