from pathlib import Path
import sys
import threading
import time

import numpy as np
import tensorflow as tf

sys.path.append(str(Path(__file__).resolve().parent.parent))
from algorithm.sac_base import SAC_Base
from algorithm.saver import Saver
from algorithm.replay_buffer import PrioritizedReplayBuffer


class SAC_DS_Base(SAC_Base):
    def __init__(self,
                 state_dim,
                 action_dim,
                 model_root_path,

                 write_summary_graph=False,
                 seed=None,
                 tau=0.005,
                 save_model_per_step=5000,
                 write_summary_per_step=20,
                 update_target_per_step=1,
                 init_log_alpha=-4.6,
                 use_auto_alpha=True,
                 lr=3e-4):

        self.graph = tf.Graph()
        gpu_options = tf.GPUOptions(allow_growth=True)
        self.sess = tf.Session(config=tf.ConfigProto(gpu_options=gpu_options),
                               graph=self.graph)

        self.s_dim = state_dim
        self.a_dim = action_dim
        self.model_root_path = model_root_path

        self.save_model_per_step = save_model_per_step
        self.write_summary_per_step = write_summary_per_step
        self.update_target_per_step = update_target_per_step

        self.use_priority = True
        self.use_auto_alpha = use_auto_alpha

        with self.graph.as_default():
            self._build_model(tau, lr, init_log_alpha)

            if model_root_path is not None:
                if seed is not None:
                    tf.random.set_random_seed(seed)

                self.saver = Saver(f'{model_root_path}/model', self.sess)
                init_step = self.saver.restore_or_init()
                self.global_step.load(init_step, self.sess)

                summary_path = f'{model_root_path}/log'
                if write_summary_graph:
                    writer = tf.summary.FileWriter(summary_path, self.graph)
                    writer.close()
                self.summary_writer = tf.summary.FileWriter(summary_path)

                self.sess.run(self.update_target_hard_op)

    def get_policy_variables(self):
        variables = self.sess.run(self.policy_variables)

        return [v.tolist() for v in variables]

    def update_policy_variables(self, policy_variables):
        assert len(self.policy_variables) == len(policy_variables)

        for v, n_v in zip(self.policy_variables, policy_variables):
            v.load(n_v, self.sess)

    def save_model(self):
        raise Exception('save_model is removed')

    def write_constant_summaries(self, constant_summaries, step=None):
        if self.summary_writer is not None:
            summaries = tf.Summary(value=[tf.Summary.Value(tag=i['tag'],
                                                           simple_value=i['simple_value'])
                                          for i in constant_summaries])
            self.summary_writer.add_summary(summaries, self.sess.run(self.global_step) if step is None else step)

    def train(self, s, a, r, s_, done, gamma, is_weight):
        assert len(s.shape) == 2
        assert self.model_root_path is not None

        global_step = self.sess.run(self.global_step)

        # update target networks
        if global_step % self.update_target_per_step == 0:
            self.sess.run(self.update_target_op)

        if global_step % self.write_summary_per_step == 0:
            summaries = self.sess.run(self.summaries, {
                self.pl_s: s,
                self.pl_a: a,
                self.pl_r: r,
                self.pl_s_: s_,
                self.pl_done: done,
                self.pl_gamma: gamma,
                self.pl_is: is_weight
            })
            self.summary_writer.add_summary(summaries, global_step)

        self.sess.run(self.train_q_ops, {
            self.pl_s: s,
            self.pl_a: a,
            self.pl_r: r,
            self.pl_s_: s_,
            self.pl_done: done,
            self.pl_gamma: gamma,
            self.pl_is: is_weight
        })

        self.sess.run(self.train_policy_op, {
            self.pl_s: s,
        })

        if self.use_auto_alpha:
            self.sess.run(self.train_alpha_op, {
                self.pl_s: s,
            })

        td_error = self.sess.run(self.td_error, {
            self.pl_s: s,
            self.pl_a: a,
            self.pl_r: r,
            self.pl_s_: s_,
            self.pl_done: done,
            self.pl_gamma: gamma
        })

        if global_step % self.save_model_per_step == 0:
            self.saver.save(global_step)

        return global_step, td_error.flatten()
