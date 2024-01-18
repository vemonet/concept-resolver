import os
from typing import Any
import pandas as pd
import numpy as np
import zipfile
from io import BytesIO
import psycopg
from pgvector.psycopg import register_vector
from tqdm import tqdm
from fastembed.embedding import FlagEmbedding
import requests
from bs4 import BeautifulSoup

bad_zipfiles = []
error_gen_embeddings = []
pg_connect = "dbname=postgres user=postgres password=password host=db"

# Get all dicts
dicts_url = "https://pubdictionaries.org/dictionaries?grid%5Border%5D=created_at&grid%5Border_direction%5D=desc&grid%5Bpp%5D=187"

chunk_size = 100000
points_count = 0


def extract_pubdictionaries(url):
    resp = requests.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.content, "html.parser")
    dictionary_names = []
    # Extracting dictionary names
    for td in soup.find_all("td"):
        link = td.find("a")
        if (
            link
            and "href" in link.attrs
            and link.attrs["href"].startswith("/dictionaries/")
        ):
            dictionary_names.append(link.get_text(strip=True))
    return dictionary_names


class GenEmbeddings:
    def __init__(self):
        """Initialize the Embedding object with a model and embedding size."""
        self.embedding_model = FlagEmbedding(
            model_name="BAAI/bge-small-en-v1.5", max_length=512
        )
        self.embedding_size = 384
        # self.embedding_model = FlagEmbedding(model_name="BAAI/bge-base-en-v1.5", max_length=512)
        # self.embedding_size = 768

    def embed(self, labels: list[str]):
        """
        Generate embeddings for the given input data using the specified model.
        This is a placeholder function and should be implemented according to the specific model's requirements.

        :param labels: The data for which embeddings are to be generated.
        :return: Embeddings for the input data.
        """
        return [embedding.tolist() for embedding in self.embedding_model.embed(labels)]


embed_model = GenEmbeddings()


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
        with open(zip_filename, "wb") as f:
            f.write(zip_response.content)
        print(f"Downloaded {dict_name}.zip")

        # Unzipping the content
        with zipfile.ZipFile(zip_filename, "r") as z:
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
            with open(tsv_filename, "wb") as f:
                f.write(tsv_response.content)
            print(f"Downloaded {tsv_filename}")
            return tsv_filename
        except:
            print(
                f"Error downloading {dict_name} (probably timeout, because bad zipfile)"
            )
            bad_zipfiles.append(dict_name)
            return ""


if __name__ == "__main__":
    # dict_names = extract_pubdictionaries(dicts_url)
    # dict_names = [ "ICD10" ]
    dict_names = ["HP-PA"]

    reset_table = False

    # https://github.com/pgvector/pgvector-python
    with psycopg.connect(pg_connect) as conn:
        with conn.cursor() as cursor:
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
            register_vector(conn)

            # Create a table with a vector column if it doesn't already exist
            cursor.execute(
                f"""
            CREATE TABLE IF NOT EXISTS pubdictionaries_embeddings (
                label_id TEXT,
                label TEXT,
                dictionary TEXT,
                embedding vector({embed_model.embedding_size})
            )
            """
            )
            conn.commit()

            # Truncate the table to clean it before inserting new data
            if reset_table:
                cursor.execute("TRUNCATE TABLE pubdictionaries_embeddings")
                conn.commit()

            for dict_name in dict_names:
                filename = download_dict(dict_name)
                if not filename:
                    continue

                # NOTE: fastembed fails when embedding some dictionaries such as SNOMEDCT or Regulation_new_3
                # Probably we need to escape some chars but it's not mentioned in their doc
                #   File "/usr/local/lib/python3.11/site-packages/fastembed/embedding.py", line 116, in onnx_embed
                #     encoded = self.tokenizer.encode_batch(documents)
                #             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                # TypeError: TextEncodeInput must be Union[TextInputSequence, Tuple[InputSequence, InputSequence]]

                for df in tqdm(
                    pd.read_csv(filename, sep="\t", chunksize=chunk_size),
                    desc=f"Processing {dict_name}",
                ):
                    labels = df["#label"].tolist()
                    ids = df["id"].tolist()
                    # print(labels)
                    # print(ids)
                    try:
                        embeddings = embed_model.embed(labels)

                        for label_id, label, embedding in zip(ids, labels, embeddings):
                            cursor.execute(
                                "INSERT INTO pubdictionaries_embeddings (label_id, label, dictionary, embedding) VALUES (%s, %s, %s, %s)",
                                (
                                    label_id,
                                    label,
                                    dict_name,
                                    embedding,
                                ),
                            )

                        conn.commit()
                    except Exception as e:
                        print(f"Error generating embeddings for {dict_name}: {e}")
                        error_gen_embeddings.append(dict_name)

    print(
        f"There was an error when generating embeddings for the following dictionaries: {error_gen_embeddings}"
    )
