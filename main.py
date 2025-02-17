import argparse
import sys
from pathlib import Path

from algorithm.config_helper import set_logger

HITTED_ENVS = {'roller', 'square', 'pyramid', 'usv', 'realcar'}

if __name__ == '__main__':
    set_logger()

    parser = argparse.ArgumentParser()
    parser.add_argument('env')
    parser.add_argument('--config', '-c', help='config file')
    parser.add_argument('--run', action='store_true', help='inference mode')
    parser.add_argument('--logger_in_file', action='store_true', help='logging into a file')

    parser.add_argument('--render', action='store_true', help='render')
    parser.add_argument('--env_args', help='additional args for environments')
    parser.add_argument('--agents', type=int, help='number of agents')
    parser.add_argument('--max_iter', type=int, help='max iteration')

    parser.add_argument('--port', '-p', type=int, default=5005, help='UNITY: communication port')
    parser.add_argument('--editor', action='store_true', help='UNITY: running in Unity Editor')

    parser.add_argument('--name', '-n', help='training name')
    parser.add_argument('--nn', help='neural network model')
    parser.add_argument('--disable_sample', action='store_true', help='disable sampling when choosing actions')
    parser.add_argument('--use_env_nn', action='store_true', help='always use nn.py in env, or use saved nn_models.py if existed')
    parser.add_argument('--device', help='cpu or gpu')
    parser.add_argument('--ckpt', help='ckeckpoint to restore')
    parser.add_argument('--repeat', type=int, default=1, help='number of repeated experiments')
    args = parser.parse_args()

    if args.env in HITTED_ENVS:
        from algorithm.sac_main_hitted import MainHitted as Main
    else:
        from algorithm.sac_main import Main

    root_dir = Path(__file__).resolve().parent
    if sys.platform == 'win32':
        for _ in range(args.repeat):
            Main(root_dir, f'envs/{args.env}', args)
    elif sys.platform == 'linux':
        for i in range(args.repeat):
            Main(root_dir, f'envs/{args.env}', args)
            args.port += 1
