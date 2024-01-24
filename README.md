# A name resolution service for biomedical concepts, using vector databases and similarity search

### Problem Statement

Resolving concept labels to standardized identifiers from existing databases is a fundamental requirement in the process of annotating biomedical data. While several annotation services, including [BioPortal](https://bioportal.bioontology.org/) and the [Translator Name Resolution service](https://name-resolution-sri.renci.org/docs), are available, most of them rely on straightforward matching mechanisms (respectively mgrep and solr). Unfortunately, these mechanisms often fall short when dealing with concept labels that exhibit substantial variations from standardized identifiers or when dealing with synonyms.

### Approach

We propose to explore the use of vector similarity search to improve the accuracy of concept resolution. We will leverage the extensive dataset gathered by the [Translator Babel project](https://github.com/TranslatorSRI/Babel), which includes a vast repository of identifiers, labels, and synonyms from the biomedical domain (PubChem, CHEMBL, UniProt, MONDO, OMIM, HGNC, DrugBank, and more).

### Objectives

During the [Biomedical Linked Annotation Hackathon](https://blah8.linkedannotation.org/), our key objectives are as follows:

1. **Choosing a vector database and text embeddings model**: we will evaluate the available open-source vector database and text embeddings models to choose one that fits our needs. We might also choose multiple, and compare their results.
2. **Data ingestion:** we will establish a workflow to generate embeddings and ingest the data from the Translator Babel project into a vector database. This database will serve as the foundation for our name resolution service.
3. **Vector similarity search:** we will implement a service that will enable users to retrieve potential identifiers for a given concept label, along with scores indicating the degree of confidence. This service will use the vector database similarity search implementation
4. **Evaluation**: we will look into existing datasets to benchmark the efficiency of our approach, and compare it to existing services
5. **Exploring use cases:** in addition to concept resolution, we will explore a range of potential use cases that can benefit from the vector database. These may include synonym discovery, concept mapping, and concept recommendation.

The name resolution service will be exposed as an OpenAPI-described API that takes a concept label as input, and return a list of matching entities, represented by a dictionary with the score and their ID curie, label, synonyms.

#### Vector databases

| Name                                                 | Creation     | GitHub stars | Written in | SDK for                    | Query language/API* | Implement vector functions                                   | Comment                                                      |
| ---------------------------------------------------- | ------------ | ------------ | ---------- | -------------------------- | ------------------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| [**Qdrant**](https://github.com/qdrant/qdrant)       | July 2020    | ~14k         | Rust       | Python, JS, Rust, Go, .NET | OpenAPI, gRPC       | [cosine, euclid, dot](https://qdrant.tech/documentation/concepts/search/#metrics) | Can be used as local standalone tool, in memory or persistent on disk, without to deploy a web service |
| [**Milvus**](https://github.com/milvus-io/milvus)    | October 2019 | ~24k         | Go         | Python, JS, Java, Go       | OpenAPI ❓️           | [cosine, euclid, inner product](https://milvus.io/docs/metric.md) | aka. Zilliz cloud                                            |
| [**Chroma**](https://github.com/chroma-core/chroma)  | October 2022 | ~9k          | Python     | Python, JS                 | OpenAPI ❓️           |                                                              |                                                              |
| [**Weaviate**](https://github.com/weaviate/weaviate) | March 2016   | ~8k          | Go         | Python, JS, Java, Go       | GraphQL API         | [cosine, euclid](https://weaviate.io/developers/weaviate/search/similarity) |                                                              |
| [**pgvector**](https://github.com/pgvector/pgvector) | April 2021   | ~6.5k        | C          | Through Postgres SDK ❓️     | SQL                 | [cosine, euclid, inner product, taxicab](https://github.com/pgvector/pgvector#vector-functions) | Integrated in PostgreSQL                                     |

*Query language/API specifies which type of query language or API can be used to query the information inside the vector database

All those products are Open Source, and they all propose a simple web UI to explore the vector database.

Most of them have a modern and simple API (apart from pgvector which lives within PostgreSQL)

#### Text embedding models

Reference benchmark for text embeddings models: https://huggingface.co/blog/mteb

Leaderboard: https://huggingface.co/spaces/mteb/leaderboard

Popular embedding models:

- FlagEmbedding `bge-large-en-v1.5`
- OpenAI `text-embedding-ada-002`
- HuggingFace `sentence-transformers/all-MiniLM-L6-v2`
- Jina AI `jina-embeddings-v2-base-en`
- Cohere `embed-english-v3.0`

#### Benchmark dataset

To be defined.

Existing benchmarks for Vector databases:

- Benchmarking nearest neighbors: https://github.com/erikbern/ann-benchmarks/
- Article about benchmarks for vector databases: https://marketing.fmops.ai/blog/vector-benchmarking/
- VectorDBBench from Milvus/Zilliz: https://github.com/zilliztech/VectorDBBench
- Benchmark from Qdrant: https://qdrant.tech/benchmarks/


##### Biomedical data Benchmark

* NCBI Disease corpus: https://www.ncbi.nlm.nih.gov/CBBresearch/Dogan/DISEASE/
* Bacteria Biotope 4: https://sites.google.com/view/bb-2019/dataset
* BioWiC: An Evaluation Benchmark for Biomedical Concept Representation
    * https://github.com/hrouhizadeh/BioWiC
    * https://huggingface.co/datasets/hrouhizadeh/BioWiC


##### Mapping issues in Name Resolution service

* https://github.com/TranslatorSRI/NameResolution/issues/81
    * "ischemic fasciitis"
    * "ischemic disease"
* "Rat"/"rats" does not return Rattus norwegicus high enough (https://github.com/TranslatorSRI/NameResolution/issues/127)
* "Angiotensin II" should not match "angiotensin" in first (https://github.com/TranslatorSRI/NameResolution/issues/90)
* "acp-044 dose a" timeout (https://github.com/TranslatorSRI/NameResolution/issues/95)
* "long COVID-19" should not match "long" in first (https://github.com/TranslatorSRI/NameResolution/issues/72)
* "depression" should match "depressive disorder" higher on the list
* "diabetes type ..." hangs
* "alzheimer" gives "Alzheimer Vaccines" before "Alzheimer disease"
* "COAGULASE NEGATIVE STAPHYLOCOCCUS" hangs

Preliminary results on the 19/01/2024 (Babel synonyms not fully loaded yet, missing files after Drug: gene, protein, organisms, pathway, umls): most issues seems to be resolved apart from "Rat" and "acp-044 dose a" (does not time out but no interesting results)

### Run the project

Start services:

```bash
docker compose up -d
```

Get into the `workspace` container to run the loading scripts.

Download the Babel synonyms and load them in the vectordb:

```bash
make load
```

(experimental) Load PubDictionaries in pgvector:

```bash
python src/pubdict_load.py
```

### Current limitations

1. Current self-hosted vector database don't support multiple vectors for a single point. Which forces us to create different points for the different synonyms, and requires deduplication of the results when lookup. Which prevent us to properly use the `limit`feature from the vectordb (if the 2 first results from the vectordb are from the same point, then we will return only 1 results, which will not match the limit of 2 asked by the user)

Possible solution would be to use postgres and pgvector, with 2 tables (one for embeddings, one for concept infos) but that would make the system much more complex than a JSON store.

Is there any self-hosted vectordb that can support multiple unnamed vectors for a single point? (Qdrant currently only supports multiple named vectors which does not fit our use-case)

2. For really large datasets such as the Babel synonym dataset embedding can be quite CPU intensive. It took us ~18 weeks of CPU time to index 14 millions labels.
3. To match the original NameResolution functionalities more work will need to be done to improve the order of the results (prefLabel matches should be more important than matches on synonyms, preference by prefix/biolink types, etc)

## Documents

Introduction presentation: https://docs.google.com/presentation/d/1_nTMF-ltHvYbbvfUSDxSdBEb0Wm_yr_BvNNt-IvLKtc/edit

PubDictionaries experiment: https://docs.google.com/document/d/1nipvy2ZhZedmf5bjcUzcbGZIfN22V9KpZfO4eTXL89M/edit

Conclusion presentation: https://docs.google.com/presentation/d/1sJeuo4oegNmaMTrvCAWb0TZJZR9SGnYH-EFwTjf99lg/edit

Preprint biohackrxiv paper: http://preview.biohackrxiv.org/papers/bdda0f94-f526-4f35-8768-8faf62d731fa/paper.pdf
