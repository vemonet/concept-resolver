---
title: 'A name resolution service for biomedical concepts using vector databases and similarity search'
title_short: 'A name resolution service for biomedical concepts using vector databases and similarity search'
tags:
  - biomedical concepts
  - normalization
authors:
  - name: Vincent Emonet
    orcid: 0000-0002-1501-1082
    affiliation: 1

affiliations:
  - name: Department of Advanced Computing Sciences, Maastricht University, The Netherlands
    index: 1

date: 19 January 2024
cito-bibliography: paper.bib
event: BLAH8
biohackathon_name: "Biomedical Linked Annotation Hackathon 8"
biohackathon_url:   "https://blah8.linkedannotation.org/"
biohackathon_location: "Chiba, Japan, 2024"
# group: Project 35
# URL to project git repo --- should contain the actual paper.md:
git_url: https://github.com/vemonet/concept-resolver
# This is the short authors description that is used at the
# bottom of the generated paper (typically the first two authors):
authors_short: Vincent Emonet
---

# Introduction

Resolving concept labels to standardized identifiers from existing databases is a fundamental requirement in the process of annotating biomedical data. While several annotation services, including [BioPortal](https://bioportal.bioontology.org/) and the [Translator Name Resolution service](https://name-resolution-sri.renci.org/docs), are available, most of them rely on straightforward matching mechanisms (respectively mgrep and solr). Unfortunately, these mechanisms often fall short when dealing with concept labels that exhibit substantial variations from standardized identifiers or when dealing with synonyms.

# Discussion

We propose to explore the use of vector similarity search to improve the accuracy of concept resolution. We will leverage the extensive dataset gathered by the [Translator Babel project](https://github.com/TranslatorSRI/Babel), which includes a vast repository of identifiers, labels, and synonyms from the biomedical domain (PubChem, CHEMBL, UniProt, MONDO, OMIM, HGNC, DrugBank, and more), for a uncompressed total size of 170G of synonyms in the JSONL format.

## Vector database

We used the Qdrant dedicated vector database. It was chosen for its simplicity of use and efficiency, as it has been written in Rust, and offers a gRPC API for communication.

We also experimented with the pgvector extension for PostgreSQL databases, which is more adapted to technological stacks relying on SQL databases.

## Embeddings model

For embedding the Babel synonyms dataset, we selected the small english version v1.5 of the Flag Embeddings model (`BAAI/bge-small-en-v1.5`) [@bge_embedding]. We chose this embedding model because it is the small model that ranks the best on the [Massive Text Embedding Benchmark](https://huggingface.co/spaces/mteb/leaderboard) (MTEB) [@muennighoff2022mteb], and it has been well optimized to run on CPU.

## Results

With one-third of the extensive synonyms dataset loaded, we observed a marked improvement in resolving  issues inherent to the original SOLR full-text search system. Notably, it accurately resolved  originally problematic queries like "diabetes type 2", and even colloquial variations such as "diabetes number two".

The vector-based system delivered more consistent and faster response times, effectively eliminating timeouts from every test we did.


## Additional investigation

We extended our work by implementing similarity search for the [PubDictionaries](https://pubdictionaries.org/) service, using the [pgvector](https://github.com/pgvector/pgvector) extension, as postgreSQL was already used by the PubDictionaries services.

We produced a script to load all dictionaries, and a script to search them. Showing how easy it can be to setup a similarity search engine in a different system.

## Limitations

A notable challenge was the inability of self-hosted dedicated vector databases to support multiple vectors for a single concept, necessitating the creation of multiple points per concept and a subsequent deduplication step in result retrieval. While pgvector offered a solution, it introduced increased system complexity. 

Additionally, embedding a large corpus proved to be CPU/GPU intensive: after ~20 days of CPU time only ~60G of the dataset has been embedded.

# Conclusion

Our findings underscore the efficacy of vector-based similarity search  systems over traditional full-text search methods. They offer substantial improvements in accuracy and efficiency with reduced configuration and maintenance demands. The ease of transitioning between vector databases was also a significant advantage. However, the  considerable computational resources required for embedding large  datasets remain a challenge.

# Future work

* Improve the API to support most features from the original API (e.g. filtering by type)
* Setup a benchmarking workflow using a concept normalization dataset, such as the NCBI disease corpus [@Dogan2014-rh]
* Evaluate the efficiency of various embeddings model, such as the AnglE text embeddings model [@li2023angle] or BioBERT [@lee2019biobert]

# GitHub repositories

* https://github.com/vemonet/concept-resolver

# Acknowledgements
We would like to thank the BLAH Hackathon organisers for hosting this event. And all the Hackathon participants for the great interactions.

# References
