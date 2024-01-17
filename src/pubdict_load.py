import os
from typing import Any
import pandas as pd
import zipfile
from io import BytesIO
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
import psycopg
from pgvector.psycopg import register_vector
from tqdm import tqdm
from fastembed.embedding import FlagEmbedding
import requests
from bs4 import BeautifulSoup


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


class GenEmbeddings:
    def __init__(self):
        """Initialize the Embedding object with a model and embedding size."""
        print("⏳ Downloading embedding model")
        # self.embedding_model = FlagEmbedding(model_name="BAAI/bge-base-en-v1.5", max_length=512)
        # self.embedding_size = 768
        self.embedding_model = FlagEmbedding(model_name="BAAI/bge-small-en-v1.5", max_length=512)
        self.embedding_size = 384

    def embed(self, labels: list[str]):
        """
        Generate embeddings for the given input data using the specified model.
        This is a placeholder function and should be implemented according to the specific model's requirements.

        :param labels: The data for which embeddings are to be generated.
        :return: Embeddings for the input data.
        """
        return [
            embedding.tolist() for embedding in self.embedding_model.embed(labels)
        ]
        # return list(self.embedding_model.embed(labels).ravel())

embed_model = GenEmbeddings()

# qdrant_url = "qdrant.blah.137.120.31.102.nip.io"
# qdrant_url = "qdrant.blah.137.120.31.148.nip.io"
# qdrant_url = "qdrant.137.120.31.148.nip.io"

# vectordb = QdrantClient(
#     host="qdrant",
#     # port=443,
#     # api_key="MAMAMIA",
#     prefer_grpc=True,
# )

# vectordb.recreate_collection(
#     collection_name="pubdictionaries-flag",
#     vectors_config=VectorParams(size=embed_model.embedding_size, distance=Distance.COSINE),
#     # force_recreate=True,
# )


def download_dict(dict_name) -> str:
    print(f"Downloading {dict_name}")
    ddl_dir = "data/pubdict"
    os.makedirs(ddl_dir, exist_ok=True)

    zip_url = f"https://pubdictionaries.org/dictionaries/{dict_name}/downloadable"
    zip_filename = f"{ddl_dir}/{dict_name}.zip"

    try:
        # Try to download the zipped file
        zip_response = requests.get(zip_url)
        zip_response.raise_for_status()

        # Save the zip file locally
        with open(zip_filename, 'wb') as f:
            f.write(zip_response.content)
        print(f"Downloaded {dict_name}.zip")

        # Unzipping the content
        with zipfile.ZipFile(zip_filename, 'r') as z:
            z.extractall(ddl_dir)
        print(f"Unzipped {dict_name}")
        # NOTE: inside the zip file the dict in a .csv, but the content is TSV
        return f"{ddl_dir}/{dict_name}.csv"

    except (requests.exceptions.HTTPError, zipfile.BadZipFile) as e:
        try:
            # If the zipped file download fails, fallback to TSV download
            print(f"{e} for {dict_name}, downloading TSV file instead")
            tsv_url = f"https://pubdictionaries.org/dictionaries/{dict_name}.tsv?mode=3"
            tsv_filename = f"{ddl_dir}/{dict_name}.tsv"

            tsv_response = requests.get(tsv_url)
            tsv_response.raise_for_status()
            with open(tsv_filename, 'wb') as f:
                f.write(tsv_response.content)
            print(f"Downloaded {tsv_filename}")
            return tsv_filename
        except:
            print(f"Error downloading {dict_name} (probably timeout, because bad zipfile)")
            bad_zipfiles.append(dict_name)
            return ""



if __name__ == "__main__":
    bad_zipfiles = []

    pg_connect = "dbname=postgres user=postgres password=password host=db"

    # Get all dicts
    dicts_url = "https://pubdictionaries.org/dictionaries?grid%5Border%5D=created_at&grid%5Border_direction%5D=desc&grid%5Bpp%5D=187"

    chunk_size = 100000
    points_count = 0

    # dict_names = extract_pubdictionaries(dicts_url)
    dict_names = [ "ICD10" ]
    # dict_names = [ "PD-ORYZAGP2022" ]


    # https://github.com/pgvector/pgvector-python
    with psycopg.connect(pg_connect) as conn:
        # Open a cursor to perform database operations
        with conn.cursor() as cursor:

            conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
            register_vector(conn)

            # Create a table with a vector column if it doesn't already exist
            cursor.execute(f"""
            CREATE TABLE IF NOT EXISTS pubdictionaries_embeddings (
                label_id TEXT,
                label TEXT,
                dictionary TEXT,
                embedding vector({embed_model.embedding_size})
            )
            """)
            conn.commit()

            # Truncate the table to clean it before inserting new data
            cursor.execute("TRUNCATE TABLE pubdictionaries_embeddings")
            conn.commit()

            for dict_name in dict_names:
                filename = download_dict(dict_name)
                if not filename or "SNOMEDCT" in filename:
                    continue

                # NOTE: fastembed fails when embedding SNOMEDCT
                # Probably we need to escape some chars but it's not mentioned in their doc
                #   File "/usr/local/lib/python3.11/site-packages/fastembed/embedding.py", line 116, in onnx_embed
                #     encoded = self.tokenizer.encode_batch(documents)
                #             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                # TypeError: TextEncodeInput must be Union[TextInputSequence, Tuple[InputSequence, InputSequence]]

                # TODO: get total number of lines and chunks for loading bar?
                # with open(filename, 'r', encoding='utf-8') as file:
                #     line_count=sum(1 for _ in file)
                # total_chunks = (line_count // chunk_size)
                # print(f"Downloaded {dict_name}")

                # df = pd.read_csv(filename, sep='\t')
                # total_chunks = len(df)
                # total_chunks = estimate_total_chunks(ddl_url, chunk_size)

                # for df in tqdm(pd.read_csv(filename, sep='\t', chunksize=chunk_size), desc=f"Processing {dict_name}", total=total_chunks):
                for df in tqdm(pd.read_csv(filename, sep='\t', chunksize=chunk_size), desc=f"Processing {dict_name}"):
                    labels = df["#label"].tolist()
                    ids = df["id"].tolist()
                    # print(labels)
                    # print(ids)
                    embeddings = embed_model.embed(labels)
                    # print(embeddings)

                    for label_id, label, embedding in zip(ids, labels, embeddings):
                        cursor.execute(
                            "INSERT INTO pubdictionaries_embeddings (label_id, label, dictionary, embedding) VALUES (%s, %s, %s, %s)",
                            (label_id, label, dict_name, embedding,)
                        )

                    conn.commit()

                    similar = conn.execute("SELECT * FROM pubdictionaries_embeddings LIMIT 5").fetchall()
                    print(similar)

                    # # Create points to be inserted in Qdrant
                    # points = [
                    #     PointStruct(id=points_count + i, vector=embedding, payload={"id": label_id, "label": label, "dictionary": dict_name})
                    #     for i, (label_id, label, embedding) in enumerate(zip(ids, labels, embeddings))
                    # ]
                    # points_count += len(labels)

                    # # Insert into Qdrant
                    # vectordb.upsert(
                    #     collection_name="pubdictionaries-flag",
                    #     points=points
                    # )
