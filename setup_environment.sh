#!/bin/bash
# Environment setup for the narrative chain solver

# Download the Stanford CoreNLP
wget http://nlp.stanford.edu/software/stanford-corenlp-full-2017-06-09.zip
unzip stanford-corenlp-full-2017-06-09.zip
rm stanford-corenlp-full-2017-06-09.zip

# Install numpy nltk xmltodict pycorenlp
python -m pip install --user numpy nltk xmltodict pycorenlp
