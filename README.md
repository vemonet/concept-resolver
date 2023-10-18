# A name resolution service for biomedical concepts, using vector databases and similarity search

### Problem Statement

Resolving concept labels to standardized identifiers from existing databases is a fundamental requirement in the process of annotating biomedical data. While several annotation services, including [BioPortal](https://bioportal.bioontology.org/) and the [Translator Name Resolution service](https://name-resolution-sri.renci.org/docs), are available, most of them rely on straightforward matching mechanisms (respectively mgrep and solr). Unfortunately, these mechanisms often fall short when dealing with concept labels that exhibit substantial variations from standardized identifiers or when dealing with synonyms.

### Approach

We propose to explore the use of vector similarity search to improve the accuracy of concept resolution. We will leverage the extensive dataset gathered by the [Translator Babel project](https://github.com/TranslatorSRI/Babel), which includes a vast repository of identifiers, labels, and synonyms from the biomedical domain (PubChem, CHEMBL, UniProt, MONDO, OMIM, HGNC, DrugBank, and more).

### Objectives

During the [Biomedical Linked Annotation Hackathon](https://blah8.linkedannotation.org/), our key objectives are as follows:

1. **Choosing a vector database**: we will evaluate the available open-source vector database to choose one that fits our needs. We might also choose multiple, and compare their results. 
2. **Data ingestion:** we will establish a workflow to generate embeddings and ingest the data from the Translator Babel project into a vector database. This database will serve as the foundation for our name resolution service.
3. **Vector similarity search:** we will implement a service that will enable users to retrieve potential identifiers for a given concept label, along with scores indicating the degree of confidence. This service will use the vector database similarity search implementation
4. **Evaluation**: we will evaluate the accuracy of our service, and compare it to existing services
5. **Exploring use cases:** in addition to concept resolution, we will explore a range of potential use cases that can benefit from the vector database. These may include synonym discovery, concept mapping, and concept recommendation.

The service will be exposed as an OpenAPI-described API that takes a concept label as input, and return a list of matching entities, represented by a dictionary with the score and their ID curie, label, synonyms.