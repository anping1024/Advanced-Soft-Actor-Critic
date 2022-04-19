import importlib
import logging
import shutil
import sys
import time
import traceback
from pathlib import Path

import numpy as np

import algorithm.config_helper as config_helper

from .agent import Agent
from .sac_base import SAC_Base
from .utils import format_global_step, gen_pre_n_actions
from .utils.enums import *


class Main(object):
    train_mode = True
    _agent_class = Agent  # For different environments

    def __init__(self, root_dir, config_dir, args):
        """
        config_path: the directory of config file
        args: command arguments generated by argparse
        """
        self._logger = logging.getLogger('sac')

        config_abs_dir = self._init_config(root_dir, config_dir, args)

        self._init_env()
        self._init_sac(config_abs_dir)

        self._run()

    def _init_config(self, root_dir, config_dir, args):
        config_abs_dir = Path(root_dir).joinpath(config_dir)
        config_abs_path = config_abs_dir.joinpath('config.yaml')
        default_config_abs_path = Path(__file__).resolve().parent.joinpath('default_config.yaml')
        # Merge default_config.yaml and custom config.yaml
        config = config_helper.initialize_config_from_yaml(default_config_abs_path,
                                                           config_abs_path,
                                                           args.config)

        # Initialize config from command line arguments
        self.train_mode = not args.run
        self.render = args.render

        self.run_in_editor = args.editor

        self.disable_sample = args.disable_sample
        self.alway_use_env_nn = args.use_env_nn
        self.device = args.device
        self.last_ckpt = args.ckpt

        if args.name is not None:
            config['base_config']['name'] = args.name
        if args.env_args is not None:
            config['base_config']['env_args'] = args.env_args
        if args.port is not None:
            config['base_config']['unity_args']['port'] = args.port

        if args.nn is not None:
            config['base_config']['nn'] = args.nn
        if args.agents is not None:
            config['base_config']['n_agents'] = args.agents
        if args.max_iter is not None:
            config['base_config']['max_iter'] = args.max_iter

        config['base_config']['name'] = config_helper.generate_base_name(config['base_config']['name'])

        # The absolute directory of a specific training
        model_abs_dir = Path(root_dir).joinpath('models',
                                                config['base_config']['env_name'],
                                                config['base_config']['name'])
        model_abs_dir.mkdir(parents=True, exist_ok=True)
        self.model_abs_dir = model_abs_dir

        if args.logger_in_file:
            config_helper.set_logger(Path(model_abs_dir).joinpath(f'log.log'))

        if self.train_mode:
            config_helper.save_config(config, model_abs_dir, 'config.yaml')

        config_helper.display_config(config, self._logger)

        convert_config_to_enum(config['sac_config'])

        self.base_config = config['base_config']
        self.reset_config = config['reset_config']
        self.model_config = config['model_config']
        self.replay_config = config['replay_config']
        self.sac_config = config['sac_config']

        return config_abs_dir

    def _init_env(self):
        if self.base_config['env_type'] == 'UNITY':
            from algorithm.env_wrapper.unity_wrapper import UnityWrapper

            if self.run_in_editor:
                self.env = UnityWrapper(train_mode=self.train_mode,
                                        n_agents=self.base_config['n_agents'])
            else:
                self.env = UnityWrapper(train_mode=self.train_mode,
                                        file_name=self.base_config['unity_args']['build_path'][sys.platform],
                                        base_port=self.base_config['unity_args']['port'],
                                        no_graphics=self.base_config['unity_args']['no_graphics'] and not self.render,
                                        scene=self.base_config['env_name'],
                                        additional_args=self.base_config['env_args'],
                                        n_agents=self.base_config['n_agents'])

        elif self.base_config['env_type'] == 'GYM':
            from algorithm.env_wrapper.gym_wrapper import GymWrapper

            self.env = GymWrapper(train_mode=self.train_mode,
                                  env_name=self.base_config['env_name'],
                                  render=self.render,
                                  n_agents=self.base_config['n_agents'])

        elif self.base_config['env_type'] == 'DM_CONTROL':
            from algorithm.env_wrapper.dm_control_wrapper import DMControlWrapper

            self.env = DMControlWrapper(train_mode=self.train_mode,
                                        env_name=self.base_config['env_name'],
                                        render=self.render,
                                        n_agents=self.base_config['n_agents'])

        else:
            raise RuntimeError(f'Undefined Environment Type: {self.base_config["env_type"]}')

        self.obs_shapes, self.d_action_size, self.c_action_size = self.env.init()
        self.action_size = self.d_action_size + self.c_action_size

        self._logger.info(f'{self.base_config["env_name"]} initialized')

    def _init_sac(self, config_abs_dir: Path):
        # If nn models exists, load saved model, or copy a new one
        nn_model_abs_path = self.model_abs_dir.joinpath('nn_models.py')
        if not self.alway_use_env_nn and nn_model_abs_path.exists():
            spec = importlib.util.spec_from_file_location('nn', str(nn_model_abs_path))
            self._logger.info(f'Loaded nn from existed {nn_model_abs_path}')
        else:
            nn_abs_path = config_abs_dir.joinpath(f'{self.base_config["nn"]}.py')
            spec = importlib.util.spec_from_file_location('nn', str(nn_abs_path))
            self._logger.info(f'Loaded nn in env dir: {nn_abs_path}')
            if not self.alway_use_env_nn:
                shutil.copyfile(nn_abs_path, nn_model_abs_path)

        custom_nn_model = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(custom_nn_model)

        self.sac = SAC_Base(obs_shapes=self.obs_shapes,
                            d_action_size=self.d_action_size,
                            c_action_size=self.c_action_size,
                            model_abs_dir=self.model_abs_dir,
                            model=custom_nn_model,
                            model_config=self.model_config,
                            device=self.device,
                            train_mode=self.train_mode,
                            last_ckpt=self.last_ckpt,

                            replay_config=self.replay_config,

                            **self.sac_config)

    def _run(self):
        num_agents = self.base_config['n_agents']
        seq_encoder = self.sac.seq_encoder

        obs_list = self.env.reset(reset_config=self.reset_config)
        initial_pre_action = self.sac.get_initial_action(num_agents)  # [n_agents, action_size]
        pre_action = initial_pre_action
        if seq_encoder is not None:
            initial_seq_hidden_state = self.sac.get_initial_seq_hidden_state(num_agents)  # [n_agents, *seq_hidden_state_shape]
            seq_hidden_state = initial_seq_hidden_state

        agents = [self._agent_class(i, self.obs_shapes, self.action_size,
                                    seq_hidden_state_shape=self.sac.seq_hidden_state_shape if seq_encoder is not None else None)
                  for i in range(num_agents)]

        force_reset = False
        iteration = 0
        trained_steps = 0

        while iteration != self.base_config['max_iter']:
            if self.base_config['max_step'] != -1 and trained_steps >= self.base_config['max_step']:
                break

            if self.base_config['reset_on_iteration'] or any([a.max_reached for a in agents]) or force_reset:
                obs_list = self.env.reset(reset_config=self.reset_config)
                for agent in agents:
                    agent.clear()

                force_reset = False
            else:
                for agent in agents:
                    agent.reset()

            step = 0
            iter_time = time.time()

            try:
                while not all([a.done for a in agents]):
                    # burn-in padding
                    for agent in [a for a in agents if a.is_empty()]:
                        for _ in range(self.sac.burn_in_step):
                            agent.add_transition(
                                obs_list=[np.zeros(t, dtype=np.float32) for t in self.obs_shapes],
                                action=initial_pre_action[0],
                                reward=0.,
                                local_done=False,
                                max_reached=False,
                                next_obs_list=[np.zeros(t, dtype=np.float32) for t in self.obs_shapes],
                                prob=0.,
                                is_padding=True,
                                seq_hidden_state=initial_seq_hidden_state[0]
                            )

                    if seq_encoder == SEQ_ENCODER.RNN:
                        action, prob, next_seq_hidden_state = self.sac.choose_rnn_action(obs_list,
                                                                                         pre_action,
                                                                                         seq_hidden_state,
                                                                                         disable_sample=self.disable_sample)

                    elif seq_encoder == SEQ_ENCODER.ATTN:
                        ep_length = min(512, max([a.episode_length for a in agents]))

                        all_episode_trans = [a.get_episode_trans(ep_length) for a in agents]
                        (all_ep_indexes,
                            all_ep_padding_masks,
                            all_ep_obses_list,
                            all_ep_actions,
                            all_all_ep_rewards,
                            all_next_obs_list,
                            all_ep_dones,
                            all_ep_probs,
                            all_ep_attn_states) = zip(*all_episode_trans)

                        ep_indexes = np.concatenate(all_ep_indexes)
                        ep_padding_masks = np.concatenate(all_ep_padding_masks)
                        ep_obses_list = [np.concatenate(o) for o in zip(*all_ep_obses_list)]
                        ep_actions = np.concatenate(all_ep_actions)
                        ep_attn_states = np.concatenate(all_ep_attn_states)

                        ep_indexes = np.concatenate([ep_indexes, ep_indexes[:, -1:] + 1], axis=1)
                        ep_padding_masks = np.concatenate([ep_padding_masks,
                                                           np.zeros_like(ep_padding_masks[:, -1:], dtype=bool)], axis=1)
                        ep_obses_list = [np.concatenate([o, np.expand_dims(t_o, 1)], axis=1)
                                         for o, t_o in zip(ep_obses_list, obs_list)]
                        ep_pre_actions = gen_pre_n_actions(ep_actions, True)

                        action, prob, next_seq_hidden_state = self.sac.choose_attn_action(ep_indexes,
                                                                                          ep_padding_masks,
                                                                                          ep_obses_list,
                                                                                          ep_pre_actions,
                                                                                          ep_attn_states,
                                                                                          disable_sample=self.disable_sample)
                    else:
                        action, prob = self.sac.choose_action(obs_list,
                                                              disable_sample=self.disable_sample)

                    next_obs_list, reward, local_done, max_reached = self.env.step(action[..., :self.d_action_size],
                                                                                   action[..., self.d_action_size:])

                    if next_obs_list is None:
                        force_reset = True

                        self._logger.warning('Step encounters error, episode ignored')
                        continue

                    if step == self.base_config['max_step_each_iter']:
                        local_done = [True] * len(agents)
                        max_reached = [True] * len(agents)

                    episode_trans_list = [
                        agents[i].add_transition(
                            obs_list=[o[i] for o in obs_list],
                            action=action[i],
                            reward=reward[i],
                            local_done=local_done[i],
                            max_reached=max_reached[i],
                            next_obs_list=[o[i] for o in next_obs_list],
                            prob=prob[i],
                            is_padding=False,
                            seq_hidden_state=seq_hidden_state[i] if seq_encoder is not None else None,
                        )
                        for i in range(len(agents))
                    ]

                    if self.train_mode:
                        episode_trans_list = [t for t in episode_trans_list if t is not None]
                        if len(episode_trans_list) != 0:
                            # ep_indexes, ep_padding_masks,
                            # ep_obses_list, ep_actions, ep_rewards, next_obs_list, ep_dones, ep_probs,
                            # ep_seq_hidden_states
                            for episode_trans in episode_trans_list:
                                self.sac.put_episode(*episode_trans)
                        trained_steps = self.sac.train()

                    obs_list = next_obs_list
                    pre_action = action
                    pre_action[local_done] = initial_pre_action[local_done]
                    if seq_encoder is not None:
                        seq_hidden_state = next_seq_hidden_state
                        seq_hidden_state[local_done] = initial_seq_hidden_state[local_done]

                    step += 1

            except:
                self._logger.error(traceback.format_exc())
                self._logger.error('Exiting...')
                break

            if self.train_mode:
                self._log_episode_summaries(agents)

            self._log_episode_info(iteration, time.time() - iter_time, agents)

            p = self.model_abs_dir.joinpath('save_model')
            if self.train_mode and p.exists():
                self.sac.save_model()
                p.unlink()

            iteration += 1

        if self.train_mode:
            self.sac.save_model()
        self.env.close()

    def _log_episode_summaries(self, agents):
        rewards = np.array([a.reward for a in agents])
        self.sac.write_constant_summaries([
            {'tag': 'reward/mean', 'simple_value': rewards.mean()},
            {'tag': 'reward/max', 'simple_value': rewards.max()},
            {'tag': 'reward/min', 'simple_value': rewards.min()}
        ])

    def _log_episode_info(self, iteration, iter_time, agents):
        global_step = format_global_step(self.sac.get_global_step())
        rewards = [a.reward for a in agents]
        rewards = ", ".join([f"{i:6.1f}" for i in rewards])
        max_step = max([a.steps for a in agents])
        self._logger.info(f'{iteration}({global_step}), T {iter_time:.2f}s, S {max_step}, R {rewards}')
