import importlib
import json
import logging
import logging.handlers
import multiprocessing as mp
import os
import sys
import threading
import time
import traceback
from pathlib import Path
from typing import List

import grpc
import numpy as np

import algorithm.config_helper as config_helper
from algorithm.agent import Agent
from algorithm.utils import ReadWriteLock, elapsed_timer, gen_pre_n_actions
from algorithm.utils.enums import *

from .constants import *
from .proto import evolver_pb2, evolver_pb2_grpc, learner_pb2, learner_pb2_grpc
from .proto.ndarray_pb2 import Empty
from .proto.numproto import ndarray_to_proto, proto_to_ndarray
from .proto.pingpong_pb2 import Ping, Pong
from .sac_ds_base import SAC_DS_Base
from .utils import (SharedMemoryManager, get_episode_shapes_dtypes,
                    rpc_error_inspector, traverse_lists)


class EpisodeSender:
    def __init__(self,
                 logger_in_file: bool,
                 model_abs_dir: str,
                 learner_host: str,
                 learner_port: int,
                 episode_buffer: SharedMemoryManager,
                 episode_length_array: mp.Array):
        self._episode_buffer = episode_buffer
        self._episode_length_array = episode_length_array

        config_helper.set_logger(Path(model_abs_dir).joinpath(f'actor_episode_sender_{os.getpid()}.log') if logger_in_file else None)
        self._logger = logging.getLogger(f'ds.actor.episode_sender_{os.getpid()}')

        self._stub = StubEpisodeSenderController(learner_host, learner_port)

        self._logger.info(f'EpisodeSender {os.getpid()} initialized')

        episode_buffer.init_logger(self._logger)

        self._run()

    def _run(self):
        timer_add_trans = elapsed_timer(self._logger, 'Add trans', repeat=ELAPSED_REPEAT)

        while True:
            episode, episode_idx = self._episode_buffer.get(timeout=EPISODE_QUEUE_TIMEOUT)
            if episode is None:
                continue

            episode_length = self._episode_length_array[episode_idx]

            episode = traverse_lists(episode, lambda e: e[:, :episode_length])

            with timer_add_trans:
                self._stub.add_transitions(*episode)


class Actor(object):
    _agent_class = Agent

    def __init__(self, root_dir, config_dir, args):
        self._logger = logging.getLogger('ds.actor')

        constant_config, config_abs_dir = self._init_constant_config(root_dir, config_dir, args)

        # The evolver stub is fixed,
        # but the learner stub will be generated by evolver
        self._evolver_stub = EvolverStubController(constant_config['net_config']['evolver_host'],
                                                   constant_config['net_config']['evolver_port'])

        self._sac_actor_lock = ReadWriteLock(5, 1, 1, logger=self._logger)

        learner_host, learner_port = self._evolver_stub.register_to_evolver()

        self._logger.info(f'Assigned to learner {learner_host}:{learner_port}')

        # The learner stub is generated by evovler
        self._stub = StubController(learner_host, learner_port)

        self._init_config(constant_config, args)
        self._init_env()
        self._init_sac(config_abs_dir)
        self._init_episode_sender(learner_host, learner_port)

        self._run()

        self.close()

    def _init_constant_config(self, root_dir, config_dir, args):
        default_config_abs_path = Path(__file__).resolve().parent.joinpath('default_config.yaml')
        config_abs_dir = Path(root_dir).joinpath(config_dir)
        config_abs_path = config_abs_dir.joinpath('config_ds.yaml')
        config = config_helper.initialize_config_from_yaml(default_config_abs_path,
                                                           config_abs_path,
                                                           args.config)

        # Initialize config from command line arguments
        self.logger_in_file = args.logger_in_file

        self.device = args.device

        if args.evolver_host is not None:
            config['net_config']['evolver_host'] = args.evolver_host
        if args.evolver_port is not None:
            config['net_config']['evolver_port'] = args.evolver_port

        return config, config_abs_dir

    def _init_config(self, config, args):
        if args.env_args is not None:
            config['base_config']['env_args'] = args.env_args
        if args.build_port is not None:
            config['base_config']['unity_args']['build_port'] = args.build_port

        if args.nn is not None:
            config['base_config']['nn'] = args.nn
        if args.agents is not None:
            config['base_config']['n_agents'] = args.agents

        self.base_config = config['base_config']

        register_response = self._stub.register_to_learner()

        (model_abs_dir, _id,
         reset_config,
         model_config,
         sac_config) = register_response
        self._logger.info(f'Assigned to id {_id}')

        config['reset_config'] = reset_config
        config['model_config'] = model_config
        config['sac_config'] = sac_config

        self.model_abs_dir = model_abs_dir

        # Set logger file if available
        if self.logger_in_file:
            logger_file = Path(model_abs_dir).joinpath(f'actor-{_id}.log')
            config_helper.set_logger(logger_file)
            self._logger.info(f'Set to logger {logger_file}')

        config_helper.display_config(config, self._logger)

        convert_config_to_enum(config['sac_config'])

        self.reset_config = config['reset_config']
        self.model_config = config['model_config']
        self.sac_config = config['sac_config']

    def _init_env(self):
        if self.base_config['env_type'] == 'UNITY':
            from algorithm.env_wrapper.unity_wrapper import UnityWrapper

            if self.run_in_editor:
                self.env = UnityWrapper(n_agents=self.base_config['n_agents'])
            else:
                self.env = UnityWrapper(file_name=self.base_config['unity_args']['build_path'][sys.platform],
                                        base_port=self.base_config['unity_args']['build_port'],
                                        no_graphics=self.base_config['unity_args']['no_graphics'],
                                        scene=self.base_config['env_name'],
                                        additional_args=self.base_config['env_args'],
                                        n_agents=self.base_config['n_agents'])

        elif self.base_config['env_type'] == 'GYM':
            from algorithm.env_wrapper.gym_wrapper import GymWrapper

            self.env = GymWrapper(env_name=self.base_config['env_name'],
                                  n_agents=self.base_config['n_agents'])

        elif self.base_config['env_type'] == 'DM_CONTROL':
            from algorithm.env_wrapper.dm_control_wrapper import DMControlWrapper

            self.env = DMControlWrapper(env_name=self.base_config['env_name'],
                                        n_agents=self.base_config['n_agents'])

        else:
            raise RuntimeError(f'Undefined Environment Type: {self.base_config["env_type"]}')

        self.obs_shapes, self.d_action_size, self.c_action_size = self.env.init()
        self.action_size = self.d_action_size + self.c_action_size

        self._logger.info(f'{self.base_config["env_name"]} initialized')

    def _init_sac(self, config_abs_dir):
        nn_abs_path = Path(config_abs_dir).joinpath(f'{self.base_config["nn"]}.py')
        spec = importlib.util.spec_from_file_location('nn', str(nn_abs_path))
        custom_nn_model = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(custom_nn_model)

        self.sac_actor = SAC_DS_Base(obs_shapes=self.obs_shapes,
                                     d_action_size=self.d_action_size,
                                     c_action_size=self.c_action_size,
                                     model_abs_dir=None,
                                     model=custom_nn_model,
                                     model_config=self.model_config,
                                     device=self.device,
                                     train_mode=False,

                                     **self.sac_config)

        self._logger.info(f'SAC_ACTOR started')

    def _init_episode_sender(self, learner_host, learner_port):
        max_episode_length = self.base_config['max_episode_length']

        episode_shapes, episode_dtypes = get_episode_shapes_dtypes(
            max_episode_length,
            self.obs_shapes,
            self.action_size,
            self.sac_actor.seq_hidden_state_shape if self.sac_actor.seq_encoder is not None else None)

        self._episode_buffer = SharedMemoryManager(self.base_config['episode_queue_size'],
                                                   logger=self._logger,
                                                   counter_get_shm_index_empty_log='Episode shm index is empty',
                                                   timer_get_shm_index_log='Get an episode shm index',
                                                   timer_get_data_log='Get an episode',
                                                   log_repeat=ELAPSED_REPEAT)

        self._episode_buffer.init_from_shapes(episode_shapes, episode_dtypes)
        self._episode_length_array = mp.Array('i', range(self.base_config['episode_queue_size']))

        for _ in range(self.base_config['episode_sender_process_num']):
            mp.Process(target=EpisodeSender, kwargs={
                'logger_in_file': self.logger_in_file,
                'model_abs_dir': self.model_abs_dir,
                'learner_host': learner_host,
                'learner_port': learner_port,
                'episode_buffer': self._episode_buffer,
                'episode_length_array': self._episode_length_array
            }).start()

    def _update_policy_variables(self):
        variables = self._stub.get_policy_variables()
        if variables is not None:
            if not any([np.isnan(np.min(v)) for v in variables]):
                with self._sac_actor_lock.write():
                    self.sac_actor.update_policy_variables(variables)
                self._logger.info('Policy variables updated')
            else:
                self._logger.warning('NAN in variables, skip updating')

    def _add_trans(self,
                   l_indexes: np.ndarray,
                   l_padding_masks: np.ndarray,
                   l_obses_list: List[np.ndarray],
                   l_actions: np.ndarray,
                   l_rewards: np.ndarray,
                   next_obs_list: List[np.ndarray],
                   l_dones: np.ndarray,
                   l_probs: List[np.ndarray],
                   l_seq_hidden_states: np.ndarray = None):

        if l_indexes.shape[1] < self.sac_actor.burn_in_step + self.sac_actor.n_step:
            return

        """
        Args:
            l_indexes: [1, episode_len]
            l_padding_masks: [1, episode_len]
            l_obses_list: list([1, episode_len, *obs_shapes_i], ...)
            l_actions: [1, episode_len, action_size]
            l_rewards: [1, episode_len]
            next_obs_list: list([1, *obs_shapes_i], ...)
            l_dones: [1, episode_len]
            l_probs: [1, episode_len]
            l_seq_hidden_states: [1, episode_len, *seq_hidden_state_shape]
        """
        episode_idx = self._episode_buffer.put([
            l_indexes,
            l_padding_masks,
            l_obses_list,
            l_actions,
            l_rewards,
            next_obs_list,
            l_dones,
            l_probs,
            l_seq_hidden_states
        ])
        self._episode_length_array[episode_idx] = l_indexes.shape[1]

    def _run(self):
        num_agents = self.base_config['n_agents']
        seq_encoder = self.sac_actor.seq_encoder

        obs_list = self.env.reset(reset_config=self.reset_config)
        initial_pre_action = self.sac_actor.get_initial_action(num_agents)  # [n_agents, action_size]
        pre_action = initial_pre_action
        if seq_encoder is not None:
            initial_seq_hidden_state = self.sac_actor.get_initial_seq_hidden_state(num_agents)  # [n_agents, *seq_hidden_state_shape]
            seq_hidden_state = initial_seq_hidden_state

        agents = [self._agent_class(i, self.obs_shapes, self.action_size,
                                    seq_hidden_state_shape=self.sac_actor.seq_hidden_state_shape if seq_encoder is not None else None,
                                    max_return_episode_trans=self.base_config['max_episode_length'])
                  for i in range(num_agents)]

        force_reset = False
        iteration = 0

        while self._stub.connected and self._evolver_stub.connected:
            if self.base_config['reset_on_iteration'] or any([a.max_reached for a in agents]) or force_reset:
                obs_list = self.env.reset(reset_config=self.reset_config)
                for agent in agents:
                    agent.clear()
            else:
                for agent in agents:
                    agent.reset()

            step = 0

            self._update_policy_variables()

            try:
                while not all([a.done for a in agents]) and self._stub.connected:
                    # burn in padding
                    for agent in [a for a in agents if a.is_empty()]:
                        for _ in range(self.sac_actor.burn_in_step):
                            agent.add_transition(
                                obs_list=[np.zeros(t, dtype=np.float32) for t in self.obs_shapes],
                                action=np.zeros(self.action_size),
                                reward=0.,
                                local_done=False,
                                max_reached=False,
                                next_obs_list=[np.zeros(t, dtype=np.float32) for t in self.obs_shapes],
                                prob=0.,
                                is_padding=True,
                                seq_hidden_state=initial_seq_hidden_state[0]
                            )

                    with self._sac_actor_lock.read():
                        if seq_encoder == SEQ_ENCODER.RNN:
                            action, prob, next_seq_hidden_state = self.sac_actor.choose_rnn_action(obs_list,
                                                                                                   pre_action,
                                                                                                   seq_hidden_state,
                                                                                                   force_rnd_if_avaiable=True)

                        elif seq_encoder == SEQ_ENCODER.ATTN:
                            ep_length = max(1, max([a.episode_length for a in agents]))

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

                            action, prob, next_seq_hidden_state = self.sac_actor.choose_attn_action(ep_indexes,
                                                                                                    ep_padding_masks,
                                                                                                    ep_obses_list,
                                                                                                    ep_pre_actions,
                                                                                                    ep_attn_states,
                                                                                                    force_rnd_if_avaiable=True)
                        else:
                            action, prob = self.sac_actor.choose_action(obs_list,
                                                                        force_rnd_if_avaiable=True)

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

                    episode_trans_list = [t for t in episode_trans_list if t is not None]
                    if len(episode_trans_list) != 0:
                        # ep_indexes, ep_padding_masks,
                        # ep_obses_list, ep_actions, ep_rewards, next_obs_list, ep_dones, ep_probs,
                        # ep_seq_hidden_states
                        for episode_trans in episode_trans_list:
                            self._add_trans(*episode_trans)

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

            self._log_episode_info(iteration, agents)
            iteration += 1

        self.close()

    def _log_episode_info(self, iteration, agents):
        rewards = [a.reward for a in agents]
        rewards = ", ".join([f"{i:6.1f}" for i in rewards])
        max_step = max([a.steps for a in agents])
        self._logger.info(f'{iteration}, S {max_step}, R {rewards}')

    def close(self):
        if hasattr(self, 'env'):
            self.env.close()
        if hasattr(self, '_stub'):
            self._stub.close()

        self._evolver_stub.close()

        self._logger.warning('Closed')


class EvolverStubController:
    _closed = False

    def __init__(self, evolver_host, evolver_port):
        self._logger = logging.getLogger('ds.actor.evolver_stub')

        self._evolver_channel = grpc.insecure_channel(f'{evolver_host}:{evolver_port}', [
            ('grpc.max_reconnect_backoff_ms', MAX_RECONNECT_BACKOFF_MS)
        ])
        self._evolver_stub = evolver_pb2_grpc.EvolverServiceStub(self._evolver_channel)
        self._logger.info(f'Starting evolver stub [{evolver_host}:{evolver_port}]')

        self._evolver_connected = False

        t_evolver = threading.Thread(target=self._start_persistence)
        t_evolver.start()

    @property
    def connected(self):
        return self._evolver_connected

    @rpc_error_inspector
    def register_to_evolver(self):
        self._logger.info('Waiting for evolver connection')
        while not self.connected:
            time.sleep(RECONNECTION_TIME)
            continue

        response = None
        self._logger.info('Registering to evolver...')
        while response is None:
            response = self._evolver_stub.RegisterActor(Empty())
            if response.succeeded:
                self._logger.info('Registered to evolver')

                return (response.learner_host, response.learner_port)
            else:
                response = None
                time.sleep(RECONNECTION_TIME)

    def _start_persistence(self):
        def request_messages():
            while not self._closed:
                yield Ping(time=int(time.time() * 1000))
                time.sleep(PING_INTERVAL)
                if not self._evolver_connected:
                    break

        while not self._closed:
            try:
                reponse_iterator = self._evolver_stub.Persistence(request_messages())
                for response in reponse_iterator:
                    if not self._evolver_connected:
                        self._evolver_connected = True
                        self._logger.info('Evolver connected')
            except grpc.RpcError:
                if self._evolver_connected:
                    self._evolver_connected = False
                    self._logger.error('Evolver disconnected')
            finally:
                time.sleep(RECONNECTION_TIME)

    def close(self):
        self._closed = True


class StubController:
    _closed = False

    def __init__(self, learner_host, learner_port):
        self._logger = logging.getLogger('ds.actor.stub')

        self._learner_channel = grpc.insecure_channel(f'{learner_host}:{learner_port}', [
            ('grpc.max_reconnect_backoff_ms', MAX_RECONNECT_BACKOFF_MS)
        ])
        self._learner_stub = learner_pb2_grpc.LearnerServiceStub(self._learner_channel)
        self._logger.info(f'Starting learner stub [{learner_host}:{learner_port}]')

        self._learner_connected = False

        t_learner = threading.Thread(target=self._start_learner_persistence)
        t_learner.start()

    @property
    def connected(self):
        return self._learner_connected

    @rpc_error_inspector
    def register_to_learner(self):
        self._logger.info('Waiting for learner connection')
        while not self.connected:
            time.sleep(RECONNECTION_TIME)
            continue

        response = None
        self._logger.info('Registering to learner...')
        while response is None:
            response = self._learner_stub.RegisterActor(Empty())

            if response.model_abs_dir and response.unique_id != -1:
                self._logger.info('Registered to learner')
                return (response.model_abs_dir, response.unique_id,
                        json.loads(response.reset_config_json),
                        json.loads(response.model_config_json),
                        json.loads(response.sac_config_json))
            else:
                response = None
                time.sleep(RECONNECTION_TIME)

    @rpc_error_inspector
    def get_action(self, obs_list, rnn_state=None):
        request = learner_pb2.GetActionRequest(obs_list=[ndarray_to_proto(obs)
                                                         for obs in obs_list],
                                               rnn_state=ndarray_to_proto(rnn_state))

        response = self._learner_stub.GetAction(request)
        action = proto_to_ndarray(response.action)
        rnn_state = proto_to_ndarray(response.rnn_state)

        if rnn_state is None:
            return action
        else:
            return action, rnn_state

    @rpc_error_inspector
    def get_policy_variables(self):
        response = self._learner_stub.GetPolicyVariables(Empty())
        if response.succeeded:
            return [proto_to_ndarray(v) for v in response.variables]

    def _start_learner_persistence(self):
        def request_messages():
            while not self._closed:
                yield Ping(time=int(time.time() * 1000))
                time.sleep(PING_INTERVAL)
                if not self._learner_connected:
                    break

        while not self._closed:
            try:
                reponse_iterator = self._learner_stub.Persistence(request_messages())
                for response in reponse_iterator:
                    if not self._learner_connected:
                        self._learner_connected = True
                        self._logger.info('Learner connected')
            except grpc.RpcError:
                if self._learner_connected:
                    self._learner_connected = False
                    self._logger.error('Learner disconnected')
            finally:
                time.sleep(RECONNECTION_TIME)

    def close(self):
        self._closed = True


class StubEpisodeSenderController:
    def __init__(self, learner_host, learner_port):
        self._learner_channel = grpc.insecure_channel(f'{learner_host}:{learner_port}', [
            ('grpc.max_reconnect_backoff_ms', MAX_RECONNECT_BACKOFF_MS)
        ])
        self._learner_stub = learner_pb2_grpc.LearnerServiceStub(self._learner_channel)

    @rpc_error_inspector
    def add_transitions(self,
                        l_indexes,
                        l_padding_masks,
                        l_obses_list,
                        l_actions,
                        l_rewards,
                        next_obs_list,
                        l_dones,
                        l_mu_probs,
                        l_seq_hidden_states=None):
        self._learner_stub.Add(learner_pb2.AddRequest(l_indexes=ndarray_to_proto(l_indexes),
                                                      l_padding_masks=ndarray_to_proto(l_padding_masks),
                                                      l_obses_list=[ndarray_to_proto(l_obses)
                                                                    for l_obses in l_obses_list],
                                                      l_actions=ndarray_to_proto(l_actions),
                                                      l_rewards=ndarray_to_proto(l_rewards),
                                                      next_obs_list=[ndarray_to_proto(next_obs)
                                                                     for next_obs in next_obs_list],
                                                      l_dones=ndarray_to_proto(l_dones),
                                                      l_mu_probs=ndarray_to_proto(l_mu_probs),
                                                      l_seq_hidden_states=ndarray_to_proto(l_seq_hidden_states)))
