
# https://github.com/TranslatorSRI/NameResolution/blob/master/data-loading/Makefile

# Download synonym files
data/synonyms:
	wget -c -r -l1 -nd -P data/synonyms https://stars.renci.org/var/babel_outputs/2023nov5/synonyms/
	gunzip data/synonyms/*.txt.gz


# Load files in vector db
.PHONY: load
load: data/synonyms
	python3 src/load.py
