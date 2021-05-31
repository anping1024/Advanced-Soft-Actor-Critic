import torch
from torch import nn

import algorithm.nn_models as m


class ModelRep(m.ModelBaseRNNRep):
    def _build_model(self):
        assert self.obs_shapes == ((44,), (6,))

        self.rnn = m.GRU(self.obs_shapes[0][0] + self.c_action_size, 8, 1)

    def forward(self, obs_list, pre_action, rnn_state=None):
        ray_obs, vec_obs = obs_list

        output, hn = self.rnn(torch.cat([ray_obs, pre_action], dim=-1), rnn_state)

        state = torch.cat([vec_obs, output], dim=-1)

        return state, hn


class ModelTransition(m.ModelTransition):
    def _build_model(self):
        return super()._build_model(dense_n=128, dense_depth=3)


class ModelReward(m.ModelReward):
    def _build_model(self):
        return super()._build_model(dense_n=128, dense_depth=2)


class ModelObservation(m.ModelBaseObservation):
    def _build_model(self):
        self.dense = m.LinearLayers(self.state_size,
                                    dense_n=64, dense_depth=2,
                                    output_size=self.obs_shapes[0][0] + self.obs_shapes[1][0])

    def forward(self, state):
        obs = self.dense(state)

        return obs[..., :self.obs_shapes[0][0]], obs[..., self.obs_shapes[0][0]:]

    def get_loss(self, state, obs_list):
        mse = nn.MSELoss()

        approx_ray_obs, approx_vec_obs = self(state)

        ray_obs, vec_obs = obs_list

        return mse(approx_ray_obs, ray_obs) + mse(approx_vec_obs, vec_obs)


class ModelQ(m.ModelQ):
    def _build_model(self):
        return super()._build_model(c_state_n=128, c_state_depth=1,
                                    c_action_n=128, c_action_depth=1,
                                    c_dense_n=128, c_dense_depth=3)


class ModelPolicy(m.ModelPolicy):
    def _build_model(self):
        return super()._build_model(c_dense_n=128, c_dense_depth=2,
                                    mean_n=128, mean_depth=1,
                                    logstd_n=128, logstd_depth=1)
