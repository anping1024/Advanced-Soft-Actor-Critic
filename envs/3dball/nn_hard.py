import tensorflow as tf
import tensorflow_probability as tfp

import algorithm.nn_models as m


class ModelTransition(m.ModelBaseTransition):
    def __init__(self, state_size, d_action_size, c_action_size, use_extra_data):
        super().__init__(state_size, d_action_size, c_action_size, use_extra_data)

        self.dense = tf.keras.Sequential([
            tf.keras.layers.Dense(64, activation=tf.nn.relu),
            tf.keras.layers.Dense(64, activation=tf.nn.relu),
            tf.keras.layers.Dense(state_size + state_size)
        ])

        self.next_state_tfpd = tfp.layers.DistributionLambda(
            make_distribution_fn=lambda t: tfp.distributions.Normal(t[0], t[1]))

    def call(self, state, action):
        next_state = self.dense(tf.concat([state, action], -1))
        mean, logstd = tf.split(next_state, num_or_size_splits=2, axis=-1)
        next_state_dist = self.next_state_tfpd([mean, tf.clip_by_value(tf.exp(logstd), 0.1, 1.0)])

        return next_state_dist


class ModelReward(m.ModelBaseReward):
    def __init__(self, state_size, use_extra_data):
        super().__init__(state_size, use_extra_data)

        self.dense = tf.keras.Sequential([
            tf.keras.layers.Dense(64, tf.nn.relu),
            tf.keras.layers.Dense(1)
        ])

    def call(self, state):
        reward = self.dense(state)

        return reward


class ModelObservation(m.ModelBaseObservation):
    def __init__(self, state_size, obs_shapes, use_extra_data):
        super().__init__(state_size, obs_shapes, use_extra_data)

        self.dense = tf.keras.Sequential([
            tf.keras.layers.Dense(64, tf.nn.relu),
            tf.keras.layers.Dense(obs_shapes[0][0])
        ])

    def call(self, state):
        obs = self.dense(state)

        return obs

    def get_loss(self, state, obs_list):
        approx_obs = self(state)

        return tf.reduce_mean(tf.square(approx_obs - obs_list[0]))


class ModelRep(m.ModelBaseGRURep):
    def __init__(self, obs_shapes, d_action_size, c_action_size):
        super().__init__(obs_shapes, d_action_size, c_action_size, rnn_units=32)

        self.dense = tf.keras.Sequential([
            tf.keras.layers.Dense(32, activation=tf.nn.tanh)
        ])

    def call(self, obs_list, pre_action, rnn_state):
        obs = obs_list[0][..., :-3]
        obs = tf.concat([obs, pre_action], axis=-1)
        outputs, next_rnn_state = self.gru(obs, initial_state=rnn_state)

        state = self.dense(outputs)

        return state, next_rnn_state


class ModelQ(m.ModelQ):
    def __init__(self, state_size, d_action_size, c_action_size):
        super().__init__(state_size, d_action_size, c_action_size,
                         dense_n=64, dense_depth=2)


class ModelPolicy(m.ModelPolicy):
    def __init__(self, state_size, d_action_size, c_action_size):
        super().__init__(state_size, d_action_size, c_action_size,
                         dense_n=64, dense_depth=2)
