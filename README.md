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

* BioWiC: An Evaluation Benchmark for Biomedical Concept Representation
    * https://github.com/hrouhizadeh/BioWiC
    * https://huggingface.co/datasets/hrouhizadeh/BioWiC


##### Mapping issues in Name Resolution service

* "Fluphenazine Decanoate Injectio, USP" should match `UMLS:C2355623` before `UMLS:C0573089` (overdose)
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

### Run the project

Install dependencies:

```bash
pip install -r requirements.txt
```

Start services:

```bash
docker compose up -d
```
