#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Jan 31 14:09:43 2018

@author: https://github.com/kyu999/biovec/blob/master/biovec/models.py
"""

from gensim.models import word2vec
from Bio import SeqIO
import sys



def split_ngrams(seq, n):
    """
    'AGAMQSASM' => [['AGA', 'MQS', 'ASM'], ['GAM','QSA'], ['AMQ', 'SAS']]
    """
    a, b, c = zip(*[iter(seq)]*n), zip(*[iter(seq[1:])]*n), zip(*[iter(seq[2:])]*n)
    str_ngrams = []
    for ngrams in [a,b,c]:
        x = []
        for ngram in ngrams:
            x.append("".join(ngram))
        str_ngrams.append(x)
    return str_ngrams

def split_ngrams_no_repetitions(seq, n, reading_frame):
    """
    'acccgtgtctgg', n=3, reading frame = 1: ['acc', 'cgt', 'gtc', 'tgg']
    reading frame = 2: ['ccc', 'gtg', 'tct']
    reading frame = 3: ['ccg', 'tgt', 'ctg']
    """
    a, b, c = zip(*[iter(seq)]*n), zip(*[iter(seq[1:])]*n), zip(*[iter(seq[2:])]*n)
    str_ngrams = []
    for ngrams in [a,b,c]:
        x = []
        for ngram in ngrams:
            x.append("".join(ngram))
        str_ngrams.append(x)
    return str_ngrams[reading_frame-1]


def generate_corpusfile(corpus_fname, n, out):
    '''
    Args:
        corpus_fname: corpus file name
        n: the number of chunks to split. In other words, "n" for "n-gram"
        out: output corpus file path
    Description:
        Protvec uses word2vec inside, and it requires to load corpus file
        to generate corpus.
    '''
    f = open(out, "w")
    for r in SeqIO.parse(corpus_fname, "fasta"):
        ngram_patterns = split_ngrams(r.seq, n)
        for ngram_pattern in ngram_patterns:
            f.write(" ".join(ngram_pattern) + "\n")
        sys.stdout.write(".")

    f.close()


def generate_corpusfile_no_repetitions(corpus_fname, n, reading_frame, out):
    '''
    Args:
        corpus_fname: corpus file name
        n: the number of chunks to split. In other words, "n" for "n-gram"
        reading_frame: 1/2/3 for splitting
        out: output corpus file path
    Description:
        Protvec uses word2vec inside, and it requires to load corpus file
        to generate corpus.
    '''
    f = open(out, "w")
    for r in SeqIO.parse(corpus_fname, "fasta"):
        ngram_patterns = split_ngrams_no_repetitions(r.seq, n, reading_frame)
        f.write(" ".join(ngram_patterns) + "\n")

    f.close()

def load_protvec(model_fname):
    return word2vec.Word2Vec.load(model_fname)


class ProtVec(word2vec.Word2Vec):

    def __init__(self, corpus_fname=None, corpus=None, n=3, size=100, out="corpus.txt",  sg=1, window=25, min_count=2, workers=3):
        """
        Either fname or corpus is required.
        corpus_fname: fasta file for corpus
        corpus: corpus object implemented by gensim
        n: n of n-gram
        out: corpus output file path
        min_count: least appearance count in corpus. if the n-gram appear k times which is below min_count, the model does not remember the n-gram
        """

        self.n = n
        self.size = size
        self.corpus_fname = corpus_fname

        if corpus is None and corpus_fname is None:
            raise Exception("Either corpus_fname or corpus is needed!")

        if corpus_fname is not None:
            print('Generate Corpus file from fasta file...')
            generate_corpusfile(corpus_fname, n, out)
            corpus = word2vec.Text8Corpus(out)

        word2vec.Word2Vec.__init__(self, corpus, size=size, sg=sg, window=window, min_count=min_count, workers=workers)

    def to_vecs(self, seq):
        """
        convert sequence to three n-length vectors
        e.g. 'AGAMQSASM' => [ array([  ... * 100 ], array([  ... * 100 ], array([  ... * 100 ] ]
        """
        ngram_patterns = split_ngrams(seq, self.n)

        protvecs = []
        for ngrams in ngram_patterns:
            ngram_vecs = []
            for ngram in ngrams:
                try:
                    ngram_vecs.append(self[ngram])
                except:
                    raise KeyError("Model has never trained this n-gram: " + ngram)
            protvecs.append(sum(ngram_vecs))
            return protvecs
        
        
class AAVec(word2vec.Word2Vec):

    def __init__(self, corpus_fname=None, corpus=None, n=3, reading_frame=1,size=100, out="corpus.txt",  sg=1, window=25, min_count=2, workers=3):
        """
        Either fname or corpus is required.
        corpus_fname: fasta file for corpus
        corpus: corpus object implemented by gensim
        n: n of n-gram
        out: corpus output file path
        min_count: least appearance count in corpus. if the n-gram appear k times which is below min_count, the model does not remember the n-gram
        """

        self.n = n
        self.size = size
        self.corpus_fname = corpus_fname
        self.reading_frame = reading_frame

        if corpus is None and corpus_fname is None:
            raise Exception("Either corpus_fname or corpus is needed!")

        if corpus_fname is not None:
            print('Generate Corpus file from fasta file...')
            generate_corpusfile_no_repetitions(corpus_fname, n, reading_frame, out)
            corpus = word2vec.Text8Corpus(out)

        word2vec.Word2Vec.__init__(self, corpus, size=size, sg=sg, window=window, min_count=min_count, workers=workers)

    def to_vecs(self, seq):
        """
        convert sequence to n-length vector
        e.g. 'AGAMQSASM' => [ array([  ... * 100 ])]
        """
        ngrams = split_ngrams_no_repetitions(seq, self.n, self.reading_frame)

        protvecs = []
        ngram_vecs = []
        for ngram in ngrams:
            try:
                ngram_vecs.append(self[ngram])
            except:
                raise Exception("Model has never trained this n-gram: " + ngram)
        protvecs.append(sum(ngram_vecs))
        return protvecs