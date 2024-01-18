import os
import pandas as pd
import numpy as np
from fastembed.embedding import FlagEmbedding as Embedding
import psycopg
from pgvector.psycopg import register_vector

from src.pubdict_load import embed_model

search = "sensory loss"

embeddings = embed_model.embed([search])

pg_connect = "dbname=postgres user=postgres password=password host=db"
with psycopg.connect(pg_connect) as conn:
    with conn.cursor() as cursor:
        register_vector(conn)

        similars = conn.execute(
            "SELECT embedding <-> %s AS distance, * FROM pubdictionaries_embeddings ORDER BY distance LIMIT 50",
            (np.array(embeddings[0]),),
        ).fetchall()
        # all = conn.execute("SELECT * FROM pubdictionaries_embeddings LIMIT 5").fetchall()

        for sim in similars:
            print(f"{sim[2]} - {sim[3]} - {sim[0]} - {sim[1]}")


# TODO: add to ruby? https://github.com/ankane/neighbor#getting-started
# https://github.com/pubannotation/pubdictionaries/blob/master/db/schema.rb#L48
