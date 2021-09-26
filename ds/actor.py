import importlib
import json
import logging
import logging.handlers
import math
import sys
import threading
import time
from pathlib import Path
from queue import Full, Queue

import grpc
import numpy as np

import algorithm.config_helper as config_helper
from algorithm.agent import Agent
from algorithm.utils import EnvException, ReadWriteLock, elapsed_timer, elapsed_counter

from .constants import *
from .proto import evolver_pb2, evolver_pb2_grpc, learner_pb2, learner_pb2_grpc
from .proto.ndarray_pb2 import Empty
from .proto.numproto import ndarray_to_proto, proto_to_ndarray
from .proto.pingpong_pb2 import Ping, Pong
from .sac_ds_base import SAC_DS_Base
from .utils import rpc_error_inspector


class AddTransitionBuffer:
    def __init__(self, add_trans):
        self._add_trans = add_trans

        self._closed = False
        self._buffer = Queue(maxsize=10)
        self._logger = logging.getLogger('ds.actor.add_transition_buffer')

        self.add_trans_counter = elapsed_counter(self._logger, 'Buffer is full', ELAPSED_REPEAT)

        threading.Thread(target=self.run).start()

    def run(self):
        timer_waiting_trans = elapsed_timer(self._logger, 'Waiting trans', repeat=ELAPSED_REPEAT)
        timer_add_trans = elapsed_timer(self._logger, 'Add trans', repeat=ELAPSED_REPEAT)

        while not self._closed:
            with timer_waiting_trans:
                episode_trans = self._buffer.get()

            with timer_add_trans:
                self._add_trans(*episode_trans)

    def add_trans(self, episode_trans):
        with self.add_trans_counter:
            try:
                self._buffer.put_nowait(episode_trans)
            except Full:
                self.add_trans_counter.add()

    def close(self):
        self._closed = True


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
        self._add_trans_buffer = AddTransitionBuffer(self._add_trans)

        register_response = self._evolver_stub.register_to_evolver()

        learner_host, learner_port = register_response
        self._logger.info(f'Assigned to learner {learner_host}:{learner_port}')

        # The learner stub is generated by evovler
        self._stub = StubController(learner_host, learner_port)

        self._init_config(constant_config, args)
        self._init_env()
        self._init_sac(config_abs_dir)

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
        self.additional_args = args.additional_args
        self.device = args.device
        self.run_in_editor = args.editor

        if args.evolver_host is not None:
            config['net_config']['evolver_host'] = args.evolver_host
        if args.evolver_port is not None:
            config['net_config']['evolver_port'] = args.evolver_port

        return config, config_abs_dir

    def _init_config(self, config, args):
        # Each time actor connects to the learner, initialize env
        if args.build_port is not None:
            config['base_config']['build_port'] = args.build_port
        if args.nn is not None:
            config['base_config']['nn'] = args.nn
        if args.agents is not None:
            config['base_config']['n_agents'] = args.agents

        self.base_config = config['base_config']

        register_response = self._stub.register_to_learner()

        (model_abs_dir, _id,
         reset_config,
         sac_config) = register_response
        self._logger.info(f'Assigned to id {_id}')

        config['reset_config'] = self.reset_config = reset_config
        config['sac_config'] = sac_config

        self.sac_config = config['sac_config']

        # Set logger file if available
        if args.logger_in_file:
            logger_file = Path(model_abs_dir).joinpath(f'actor-{_id}.log')
            config_helper.set_logger(logger_file)
            self._logger.info(f'Set to logger {logger_file}')

        config_helper.display_config(config, self._logger)

    def _init_env(self):
        if self.base_config['env_type'] == 'UNITY':
            from algorithm.env_wrapper.unity_wrapper import UnityWrapper

            if self.run_in_editor:
                self.env = UnityWrapper()
            else:
                self.env = UnityWrapper(file_name=self.base_config['build_path'][sys.platform],
                                        base_port=self.base_config['build_port'],
                                        no_graphics=self.base_config['no_graphics'],
                                        scene=self.base_config['scene'],
                                        additional_args=self.additional_args,
                                        n_agents=self.base_config['n_agents'])

        elif self.base_config['env_type'] == 'GYM':
            from algorithm.env_wrapper.gym_wrapper import GymWrapper

            self.env = GymWrapper(env_name=self.base_config['build_path'],
                                  n_agents=self.base_config['n_agents'])
        else:
            raise RuntimeError(f'Undefined Environment Type: {self.base_config["env_type"]}')

        self.obs_shapes, self.d_action_size, self.c_action_size = self.env.init()
        self.action_size = self.d_action_size + self.c_action_size

        self._logger.info(f'{self.base_config["build_path"]} initialized')

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
                                     device=self.device,
                                     train_mode=False,

                                     **self.sac_config)

        self._logger.info(f'SAC_ACTOR started')

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
                   n_obses_list,
                   n_actions,
                   n_rewards,
                   next_obs_list,
                   n_dones,
                   n_rnn_states=None):

        if n_obses_list[0].shape[1] < self.sac_actor.burn_in_step + self.sac_actor.n_step:
            return

        # TODO if not update_policy_mode, do not need get_n_probs
        with self._sac_actor_lock.read():
            n_mu_probs = self.sac_actor.get_n_probs_np(n_obses_list,
                                                       n_actions,
                                                       n_rnn_states[:, 0, ...] if self.sac_actor.use_rnn else None)

        self._stub.add_transitions(n_obses_list,
                                   n_actions,
                                   n_rewards,
                                   next_obs_list,
                                   n_dones,
                                   n_mu_probs,
                                   n_rnn_states if self.sac_actor.use_rnn else None)

    def _run(self):
        use_rnn = self.sac_actor.use_rnn

        obs_list = self.env.reset(reset_config=self.reset_config)

        agents = [self._agent_class(i, use_rnn=use_rnn, max_return_episode_trans=MAX_EPISODE_SIZE)
                  for i in range(self.base_config['n_agents'])]

        if use_rnn:
            initial_rnn_state = self.sac_actor.get_initial_rnn_state(len(agents))
            rnn_state = initial_rnn_state

        iteration = 0

        while self._stub.connected and self._evolver_stub.connected:
            if self.base_config['reset_on_iteration'] or any([a.max_reached for a in agents]):
                obs_list = self.env.reset(reset_config=self.reset_config)
                for agent in agents:
                    agent.clear()

                if use_rnn:
                    rnn_state = initial_rnn_state
            else:
                for agent in agents:
                    agent.reset()

            action = np.zeros([len(agents), self.action_size], dtype=np.float32)
            step = 0

            if self.base_config['update_policy_mode']:
                self._update_policy_variables()

            try:
                while not all([a.done for a in agents]) and self._stub.connected:
                    # burn in padding
                    for agent in agents:
                        if agent.is_empty():
                            for _ in range(self.sac_actor.burn_in_step):
                                agent.add_transition([np.zeros(t) for t in self.obs_shapes],
                                                     np.zeros(self.action_size),
                                                     0, False, False,
                                                     [np.zeros(t) for t in self.obs_shapes],
                                                     initial_rnn_state[0])

                    if self.base_config['update_policy_mode']:
                        with self._sac_actor_lock.read():
                            if use_rnn:
                                action, next_rnn_state = self.sac_actor.choose_rnn_action([o.astype(np.float32) for o in obs_list],
                                                                                          action,
                                                                                          rnn_state)
                            else:
                                action = self.sac_actor.choose_action([o.astype(np.float32) for o in obs_list])

                    else:
                        # Get action from learner each step
                        # TODO need prob
                        if use_rnn:
                            action_rnn_state = self._stub.get_action([o.astype(np.float32) for o in obs_list],
                                                                     rnn_state)
                            if action_rnn_state is None:
                                break
                            action, next_rnn_state = action_rnn_state
                        else:
                            action = self._stub.get_action([o.astype(np.float32) for o in obs_list])
                            if action is None:
                                break

                    next_obs_list, reward, local_done, max_reached = self.env.step(action[..., :self.d_action_size],
                                                                                   action[..., self.d_action_size:])

                    if step == self.base_config['max_step_each_iter']:
                        local_done = [True] * len(agents)
                        max_reached = [True] * len(agents)

                    episode_trans_list = [agents[i].add_transition([o[i] for o in obs_list],
                                                                   action[i],
                                                                   reward[i],
                                                                   local_done[i],
                                                                   max_reached[i],
                                                                   [o[i] for o in next_obs_list],
                                                                   rnn_state[i] if use_rnn else None)
                                          for i in range(len(agents))]

                    episode_trans_list = [t for t in episode_trans_list if t is not None]
                    if len(episode_trans_list) != 0:
                        for episode_trans in episode_trans_list:
                            self._add_trans_buffer.add_trans(episode_trans)

                    obs_list = next_obs_list
                    action[local_done] = np.zeros(self.action_size)
                    if use_rnn:
                        rnn_state = next_rnn_state
                        rnn_state[local_done] = initial_rnn_state[local_done]

                    step += 1

            except EnvException as e:
                self._logger.error(e)
                self.env.close()
                self._logger.info(f'Restarting {self.base_config["build_path"]}...')
                self._init_env()
                continue

            except Exception as e:
                self._logger.error(e)
                self._logger.error('Exiting...')
                break

            self._log_episode_info(iteration, agents)
            iteration += 1

        self.close()

    def _log_episode_info(self, iteration, agents):
        rewards = [a.reward for a in agents]
        rewards = ", ".join([f"{i:6.1f}" for i in rewards])
        steps = [a.steps for a in agents]
        self._logger.info(f'{iteration}, S {max(steps)}, R {rewards}')

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
                        json.loads(response.sac_config_json))
            else:
                response = None
                time.sleep(RECONNECTION_TIME)

    @rpc_error_inspector
    def add_transitions(self,
                        n_obses_list,
                        n_actions,
                        n_rewards,
                        next_obs_list,
                        n_dones,
                        n_mu_probs,
                        n_rnn_states=None):
        self._learner_stub.Add(learner_pb2.AddRequest(n_obses_list=[ndarray_to_proto(n_obses)
                                                                    for n_obses in n_obses_list],
                                                      n_actions=ndarray_to_proto(n_actions),
                                                      n_rewards=ndarray_to_proto(n_rewards),
                                                      next_obs_list=[ndarray_to_proto(next_obs)
                                                                     for next_obs in next_obs_list],
                                                      n_dones=ndarray_to_proto(n_dones),
                                                      n_mu_probs=ndarray_to_proto(n_mu_probs),
                                                      n_rnn_states=ndarray_to_proto(n_rnn_states)))

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
