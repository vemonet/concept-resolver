import os
import pandas as pd
import numpy as np
from fastembed.embedding import FlagEmbedding as Embedding
import psycopg
from pgvector.psycopg import register_vector

from src.pubdict_load import embed_model

pg_connect = "dbname=postgres user=postgres password=password host=db"
with psycopg.connect(pg_connect) as conn:
    with conn.cursor() as cursor:
        register_vector(conn)

        similars = conn.execute(
            "SELECT * FROM pubdictionaries_embeddings WHERE label_id = %s",
            ("http://purl.obolibrary.org/obo/HP_0003474",),
        ).fetchall()

        vectors = []
        for sim in similars:
            print(f"{sim[2]} - {sim[0]} - {sim[1]}")
            vectors.append(np.array(sim[3]))

        mean_vector = np.mean(np.array(vectors), axis=0)
        print(mean_vector)
