import os
import pandas as pd
from fastembed.embedding import FlagEmbedding as Embedding
import psycopg
from pgvector.psycopg import register_vector

from src.pubdict_load import embed_model

search = "Agoraphobia"

embeddings = embed_model.embed([search])

pg_connect = "dbname=postgres user=postgres password=password host=db"
with psycopg.connect(pg_connect) as conn:
    # Open a cursor to perform database operations
    with conn.cursor() as cursor:
        conn.execute('CREATE EXTENSION IF NOT EXISTS vector')
        register_vector(conn)

        # print(embeddings[0])

        similar = conn.execute('SELECT * FROM pubdictionaries_embeddings ORDER BY embedding <-> %s LIMIT 5', (embeddings[0],)).fetchall()
        # similar = conn.execute("SELECT * FROM pubdictionaries_embeddings LIMIT 5").fetchall()
        print(similar)


# TODO: add to ruby https://github.com/ankane/neighbor#getting-started
# https://github.com/pubannotation/pubdictionaries/blob/master/db/schema.rb#L48
