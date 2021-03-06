from gensim.models import KeyedVectors
from gensim.scripts.glove2word2vec import glove2word2vec
import numpy as np
import os.path
from scipy import spatial


class AbstractMetric:

  def reset(self):
    raise NotImplementedError('subclasses must override it')

  def most_similar(self, sentence, sentences):
    raise NotImplementedError('subclasses must override it')


class Word2VecSimilarityMetric(AbstractMetric):
  """Calculates cosine similarity between vectors of sentences
    See https://goo.gl/2r1mTF
    To use the model, download word embedding corpus first (e.g. glove from
    https://developer.syn.co.in/tutorial/bot/oscova/pretrained-vectors.html)
    and put to data folder.

    Before usage:
    - Go to
      https://developer.syn.co.in/tutorial/bot/oscova/pretrained-vectors.html
    - Download Wikipedia+Gigaword 5
    - Unpack to data/glove

    Usage:
      model = Word2VecModel()

      model.similarity('this is a sentence', 'this is also sentence')
      > 0.915479828613

      s, dist = model.most_similar('how are you', queries)
      > how are you, 1
  """

  glove_input_file = 'data/glove/glove.6B.50d.txt'
  word2vec_output_file = 'data/glove/glove.6B.50d.txt.word2vec'

  def __init__(self,
      logging,
      num_features = 50,
      word2vec_file = glove_input_file):

    self.logging = logging
    self.num_features = num_features

    if word2vec_file == self.glove_input_file:
      if not os.path.exists(self.word2vec_output_file):
        # See how to convert from glove to word2vec:
        # https://radimrehurek.com/gensim/scripts/glove2word2vec.html
        glove2word2vec(self.glove_input_file, self.word2vec_output_file)
      word2vec_file = self.word2vec_output_file

    # TODO: too slow; optimize loading e.g. using binary data.
    self.word_vectors = \
      KeyedVectors.load_word2vec_format(word2vec_file, binary=False)
    self.index2word_set = set(self.word_vectors.index2word)
    # Cashes sentence average vector
    self.sentence_to_vector_map = {}


  def reset(self):
    self.sentence_to_vector_map = {}


  def most_similar(self, sentence, sentences):
    if sentence not in self.sentence_to_vector_map:
      self.sentence_to_vector_map[sentence] = self.avg_vector(sentence)
    sentence_vector = self.sentence_to_vector_map[sentence]

    max_cosine = 0
    most_similar_sentence = ''

    for s in sentences:
      if s not in self.sentence_to_vector_map:
        self.sentence_to_vector_map[s] = self.avg_vector(s)
      v = self.sentence_to_vector_map[s]

      cosine = 1 - spatial.distance.cosine(sentence_vector, v)

      if max_cosine < cosine:
        max_cosine = cosine
        most_similar_sentence = s

    return most_similar_sentence, max_cosine


  def similarity(self, sentence1, sentence2):
    """Bad examples for the word2vec model. Fixed by removing stop words.
       # should be 'hello'
      print(model.similarity('hi there', 'where to so see holidays'))
      # should be 'become mentee'
      print(model.similarity('how to become mentee', 'become mentee'))
    """
    s1_v = self.avg_vector(sentence1)
    s2_v = self.avg_vector(sentence2)
    return 1 - spatial.distance.cosine(s1_v, s2_v)


  def avg_vector(self, sentence):
    '''Returns average vector for sentence'''
    words = sentence.split()
    feature_vec = np.zeros((self.num_features, ), dtype='float32')
    n_words = 0
    for word in words:
      if word in self.index2word_set:
        n_words += 1
        feature_vec = np.add(feature_vec, self.word_vectors[word])
    if (n_words > 0):
      feature_vec = np.divide(feature_vec, n_words)
    return feature_vec
