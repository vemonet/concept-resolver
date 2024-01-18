from fastapi import FastAPI, File, UploadFile, Form, Depends, HTTPException, Body, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, conint
from typing import Dict, List, Union, Annotated
from starlette.middleware.cors import CORSMiddleware
from fastembed.embedding import FlagEmbedding as Embedding
from qdrant_client import QdrantClient


app = FastAPI(
    title="Concept resolver",
    description="""This service takes lexical strings and attempts to map them to identifiers
    (CURIEs) from a vocabulary or ontology.  The lookup is not exact, but includes partial matches.<p/>
     Multiple results may be returned representing possible conceptual matches, but all of the identifiers
     have been correctly normalized using the
     <a href="https://github.com/TranslatorSRI/NodeNormalization">Node Normalization</a> service""",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize FastEmbed and Qdrant Client
embedding_model = Embedding(model_name="BAAI/bge-small-en-v1.5", max_length=512)
embedding_size = 384

vectordb = QdrantClient(
    host="qdrant",
    prefer_grpc=True,
)


class LookupResult(BaseModel):
    curie:str
    label: str
    synonyms: List[str]
    types: List[str]
    score: float


@app.get(
    "/lookup",
    summary="Look up cliques for a fragment of a name or synonym.",
    description="Returns cliques with a name or synonym that contains a specified string.",
    response_model=List[LookupResult],
    tags=["lookup"],
)
async def lookup_curies_get(
    string: Annotated[str, Query(description="The string to search for.")],
    autocomplete: Annotated[
        bool,
        Query(
            description="Is the input string incomplete (autocomplete=true) or a complete phrase (autocomplete=false)?"
        ),
    ] = True,
    offset: Annotated[
        int,
        Query(
            description="The number of results to skip. Can be used to page through the results of a query.",
            # Offset should be greater than or equal to zero.
            ge=0,
        ),
    ] = 0,
    limit: Annotated[
        int,
        Query(
            description="The number of results to skip. Can be used to page through the results of a query.",
            # Limit should be greater than or equal to zero and less than or equal to 1000.
            ge=0,
            le=1000,
        ),
    ] = 10,
    biolink_type: Annotated[
        Union[str, None],
        Query(
            description="The Biolink type to filter to (with or without the `biolink:` prefix), e.g. `biolink:Disease` or `Disease`.",
            # We can't use `example` here because otherwise it gets filled in when filling this in.
            # example="biolink:Disease"
        ),
    ] = None,
    only_prefixes: Annotated[
        Union[str, None],
        Query(
            description="Pipe-separated, case-sensitive list of prefixes to filter to, e.g. `MONDO|EFO`.",
            # We can't use `example` here because otherwise it gets filled in when filling this in.
            # example="MONDO|EFO"
        ),
    ] = None,
    exclude_prefixes: Annotated[
        Union[str, None],
        Query(
            description="Pipe-separated, case-sensitive list of prefixes to exclude, e.g. `UMLS|EFO`.",
            # We can't use `example` here because otherwise it gets filled in when filling this in.
            # example="UMLS|EFO"
        ),
    ] = None,
) -> list[LookupResult]:
    """
    Returns cliques with a name or synonym that contains a specified string.
    """
    return await lookup(
        string,
        autocomplete,
        offset,
        limit,
        biolink_type,
        only_prefixes,
        exclude_prefixes,
    )


@app.post(
    "/lookup",
    summary="Look up cliques for a fragment of a name or synonym.",
    description="Returns cliques with a name or synonym that contains a specified string.",
    response_model=List[LookupResult],
    tags=["lookup"],
)
async def lookup_curies_post(
    string: Annotated[str, Query(description="The string to search for.")],
    autocomplete: Annotated[
        bool,
        Query(
            description="Is the input string incomplete (autocomplete=true) or a complete phrase (autocomplete=false)?"
        ),
    ] = True,
    offset: Annotated[
        int,
        Query(
            description="The number of results to skip. Can be used to page through the results of a query.",
            # Offset should be greater than or equal to zero.
            ge=0,
        ),
    ] = 0,
    limit: Annotated[
        int,
        Query(
            description="The number of results to skip. Can be used to page through the results of a query.",
            # Limit should be greater than or equal to zero and less than or equal to 1000.
            ge=0,
            le=1000,
        ),
    ] = 10,
    biolink_type: Annotated[
        Union[str, None],
        Query(
            description="The Biolink type to filter to (with or without the `biolink:` prefix), e.g. `biolink:Disease` or `Disease`.",
            # We can't use `example` here because otherwise it gets filled in when filling this in.
            # example="biolink:Disease"
        ),
    ] = None,
    only_prefixes: Annotated[
        Union[str, None],
        Query(
            description="Pipe-separated, case-sensitive list of prefixes to filter to, e.g. `MONDO|EFO`.",
            # We can't use `example` here because otherwise it gets filled in when filling this in.
            # example="MONDO|EFO"
        ),
    ] = None,
    exclude_prefixes: Annotated[
        Union[str, None],
        Query(
            description="Pipe-separated, case-sensitive list of prefixes to exclude, e.g. `UMLS|EFO`.",
            # We can't use `example` here because otherwise it gets filled in when filling this in.
            # example="UMLS|EFO"
        ),
    ] = None,
) -> list[LookupResult]:
    """
    Returns cliques with a name or synonym that contains a specified string.
    """
    return await lookup(
        string,
        autocomplete,
        offset,
        limit,
        biolink_type,
        only_prefixes,
        exclude_prefixes,
    )


async def lookup(
    string: str,
    autocomplete: bool = False,
    offset: int = 0,
    limit: conint(le=1000) = 10,
    biolink_type: str = None,
    only_prefixes: str = "",
    exclude_prefixes: str = "",
) -> list[LookupResult]:
    query_embeddings = list(embedding_model.embed([string]))[0]

    hits = vectordb.search(
        collection_name="concept-resolver",
        query_vector=query_embeddings,
        limit=limit,
    )

    # Deduplicate match on the same ID
    seen_ids = set()
    new_list = []
    for obj in hits:
        id_ = obj.payload["id"]
        if id_ not in seen_ids:
            seen_ids.add(id_)
            if "embedded_label" in obj.payload:
                del obj.payload["embedded_label"]
            obj.payload["score"] = obj.score
            new_list.append(obj.payload)
    print(new_list)
    return new_list



@app.get("/", include_in_schema=False)
async def docs_redirect():
    """
    Redirect requests to `/` (where we don't have any content) to `/docs` (which is our Swagger interface).
    """
    return RedirectResponse(url="/docs")
