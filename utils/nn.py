import math
import tensorflow as tf


def weight(name, shape, init='xavier', range=None):
    """ Initializes weight.
    :param name: Variable name
    :param shape: Tensor shape
    :param init: Init mode. xavier / normal / uniform (default is 'xavier')
    :param range:
    :return: Variable
    """
    initializer = tf.constant_initializer()
    if init == 'xavier':
        fan_in, fan_out = shape
        range = math.sqrt(6.0 / (fan_in + fan_out))
        initializer = tf.random_uniform_initializer(-range, range)

    elif init == 'normal':
        initializer = tf.random_normal_initializer(stddev=0.1)

    elif init == 'uniform':
        if range is None:
            raise ValueError("range must not be None if uniform init is used.")
        initializer = tf.random_uniform_initializer(-range, range)

    var = tf.get_variable(name, shape, initializer=initializer)
    tf.add_to_collection('l2', tf.nn.l2_loss(var))  # Add L2 Loss
    return var


def bias(name, dim, initial_value=0.0):
    """ Initializes bias parameter.
    :param name: Variable name
    :param dim: Tensor size (list or int)
    :param initial_value: Initial bias term
    :return: Variable
    """
    dims = dim if isinstance(dim, list) else [dim]
    return tf.get_variable(name, dims, initializer=tf.constant_initializer(initial_value))


def batch_norm(x, is_training):
    """ Batch normalization.
    :param x: Tensor
    :param is_training: boolean tf.Variable, true indicates training phase
    :return: batch-normalized tensor
    """
    with tf.variable_scope('BatchNorm'):
        # calculate dimensions (from tf.contrib.layers.batch_norm)
        inputs_shape = x.get_shape()
        axis = list(range(len(inputs_shape) - 1))
        param_shape = inputs_shape[-1:]

        beta = tf.get_variable('beta', param_shape, initializer=tf.constant_initializer(0.))
        gamma = tf.get_variable('gamma', param_shape, initializer=tf.constant_initializer(1.))
        batch_mean, batch_var = tf.nn.moments(x, axis)
        ema = tf.train.ExponentialMovingAverage(decay=0.5)

        def mean_var_with_update():
            ema_apply_op = ema.apply([batch_mean, batch_var])
            with tf.control_dependencies([ema_apply_op]):
                return tf.identity(batch_mean), tf.identity(batch_var)

        mean, var = tf.cond(is_training,
                            mean_var_with_update,
                            lambda: (ema.average(batch_mean), ema.average(batch_var)))
        normed = tf.nn.batch_normalization(x, mean, var, beta, gamma, 1e-3)
    return normed


def dropout(x, keep_prob, is_training):
    """ Apply dropout.
    :param x: Tensor
    :param keep_prob: float, Dropout rate.
    :param is_training: boolean tf.Varialbe, true indicates training phase
    :return: dropout applied tensor
    """
    return tf.cond(is_training, lambda: tf.nn.dropout(x, keep_prob), lambda: x)
