import argparse
import enum
import logging
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

import algorithm.config_helper as config_helper
from algorithm.agent import Agent
from algorithm.config_helper import set_logger
from algorithm.utils import elapsed_timer


class Main(object):
    def __init__(self, root_dir, config_dir, args):
        """
        config_path: the directory of config file
        args: command arguments generated by argparse
        """
        self._logger = logging.getLogger('test_env')

        config_abs_dir = self._init_config(root_dir, config_dir, args)

        self._init_env()
        self._run()

    def _init_config(self, root_dir, config_dir, args):
        config_abs_dir = Path(root_dir).joinpath(config_dir)
        config_abs_path = config_abs_dir.joinpath('config.yaml')
        default_config_abs_path = Path(__file__).resolve().parent.joinpath('algorithm', 'default_config.yaml')
        # Merge default_config.yaml and custom config.yaml
        config = config_helper.initialize_config_from_yaml(default_config_abs_path,
                                                           config_abs_path,
                                                           args.config)

        # Initialize config from command line arguments
        self.train_mode = not args.run
        self.render = args.render

        self.run_in_editor = args.editor

        self.save_image = args.save_image
        self.save_standalone = args.save_standalone

        if args.env_args is not None:
            config['base_config']['env_args'] = args.env_args
        if args.port is not None:
            config['base_config']['unity_args']['port'] = args.port

        if args.agents is not None:
            config['base_config']['n_agents'] = args.agents

        config['base_config']['name'] = config_helper.generate_base_name(config['base_config']['name'])

        # The absolute directory of a specific training
        model_abs_dir = Path(root_dir).joinpath('models',
                                                config['base_config']['env_name'],
                                                config['base_config']['name'])
        model_abs_dir.mkdir(parents=True, exist_ok=True)
        self.model_abs_dir = model_abs_dir

        config_helper.display_config(config, self._logger)

        self.base_config = config['base_config']
        self.reset_config = config['reset_config']

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

    def _run(self):
        obs_list = self.env.reset(reset_config=self.reset_config)

        agents = [Agent(i,
                        self.obs_shapes,
                        self.action_size,) for i in range(self.base_config['n_agents'])]

        agent_size = len(agents)
        fig_size = sum([len(s) == 3 for s in self.obs_shapes])

        img_save_index = 0

        plt.ion()
        fig, axes = plt.subplots(nrows=agent_size, ncols=fig_size, squeeze=False, figsize=(3 * fig_size, 3 * agent_size))
        ims = [[] for _ in range(agent_size)]
        for i in range(agent_size):
            j = 0
            for obs_shape in self.obs_shapes:
                if len(obs_shape) == 3:
                    axes[i][j].axis('off')
                    ims[i].append(axes[i][j].imshow(np.zeros(obs_shape)))
                    j += 1

        iteration = 0

        step_timer = elapsed_timer(self._logger, 'One step interacting', 200)

        while iteration != self.base_config['max_iter']:
            if self.base_config['reset_on_iteration'] or any([a.max_reached for a in agents]):
                obs_list = self.env.reset(reset_config=self.reset_config)
                for agent in agents:
                    agent.clear()
            else:
                for agent in agents:
                    agent.reset()

            action = np.zeros([agent_size, self.action_size], dtype=np.float32)
            step = 0

            try:
                while not all([a.done for a in agents]):
                    j = 0
                    for obs in obs_list:
                        if len(obs.shape) > 2:
                            for i, image in enumerate(obs):
                                ims[i][j].set_data(image)
                            j += 1

                    fig.canvas.draw()
                    fig.canvas.flush_events()

                    action = np.random.rand(len(agents), self.action_size)

                    with step_timer:
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
                                                                   None)
                                          for i in range(len(agents))]

                    if self.save_image:
                        episode_trans_list = [t for t in episode_trans_list if t is not None]
                        for episode_trans in episode_trans_list:
                            # ep_indexes, ep_padding_masks,
                            # ep_obses_list, ep_actions, ep_rewards, next_obs_list, ep_dones, ep_probs,
                            # ep_seq_hidden_states

                            # list([1, episode_len, *obs_shapes_i], ...)
                            ep_obses_list = episode_trans[2]

                            for i, ep_obses in enumerate(ep_obses_list):
                                ep_obses = ep_obses[0]
                                if len(ep_obses.shape) > 2:
                                    if self.save_standalone:
                                        for j, obs in enumerate(ep_obses):
                                            img = Image.fromarray(np.uint8(obs * 255))
                                            img.save(self.model_abs_dir.joinpath(f'{img_save_index}-{i}-{j}.png'))
                                    else:
                                        img = Image.fromarray(np.uint8(ep_obses[0] * 255))
                                        self._logger.info(f'Saved {img_save_index}-{i}')
                                        img.save(self.model_abs_dir.joinpath(f'{img_save_index}-{i}.gif'),
                                                save_all=True,
                                                append_images=[Image.fromarray(np.uint8(o * 255)) for o in ep_obses[1:]])

                            img_save_index += 1

                    obs_list = next_obs_list

                    step += 1

            except Exception as e:
                self._logger.error(e)
                self._logger.error('Exiting...')
                break

            iteration += 1

        self.env.close()


if __name__ == '__main__':
    set_logger()

    parser = argparse.ArgumentParser()
    parser.add_argument('env')
    parser.add_argument('--config', '-c', help='config file')
    parser.add_argument('--run', action='store_true', help='inference mode')

    parser.add_argument('--render', action='store_true', help='render')
    parser.add_argument('--editor', action='store_true', help='running in Unity Editor')
    parser.add_argument('--env_args', help='additional args for Unity')
    parser.add_argument('--port', '-p', type=int, default=5005, help='communication port')
    parser.add_argument('--agents', type=int, help='number of agents')

    parser.add_argument('--save_image', action='store_true')
    parser.add_argument('--save_standalone', action='store_true')
    args = parser.parse_args()

    root_dir = Path(__file__).resolve().parent
    Main(root_dir, f'envs/{args.env}', args)
