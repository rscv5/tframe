from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import tensorflow as tf

from tframe import initializers
from tframe.layers.layer import Layer
from tframe.layers.layer import single_input



class Embedding(Layer):
  """Embedding layer for NLP"""
  abbreviation = 'embedding'
  full_name = abbreviation


  def __init__(self, vocab_size, hidden_size, initializer='default'):
    # Initialize keep probability until while linking to put the
    #   the placeholder in the right name scope

    # self._keep_prob = None
    self._vocab_size = vocab_size
    self._hidden_size = hidden_size
    if initializer == 'default':
      initializer = tf.random_uniform_initializer(-0.1, 0.1)
    self._initializer = initializers.get(initializer)


  @single_input
  def _link(self, ids, **kwargs):
    assert isinstance(ids, tf.Tensor) and len(ids.shape) == 2
    assert ids.shape.as_list()[1] == 1
    ids = tf.reshape(ids, [-1])
    
    with tf.device("/cpu:0"):
      embedding = tf.get_variable(
				"embedding", [self._vocab_size, self._hidden_size], dtype=tf.float32,
        initializer=self._initializer)
      inputs = tf.nn.embedding_lookup(embedding, ids)
    
    return inputs