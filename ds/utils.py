import functools
import threading

import grpc

from .constants import RPC_ERR_RETRY


def rpc_error_inspector(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        retry = RPC_ERR_RETRY
        while retry > 0:
            try:
                return func(self, *args, **kwargs)
            except grpc.RpcError:
                self._logger.error(f'Connection lost in {func.__name__}')
            except Exception as e:
                self._logger.error(f'Error in {func.__name__}')
                self._logger.error(e)

            retry -= 1
            if retry > 0:
                self._logger.error('Retrying ...')
    return wrapper


class PeerSet(object):
    def __init__(self, logger):
        self._peers_lock = threading.RLock()
        self._peers = dict()
        self._logger = logger

    def connect(self, peer):
        with self._peers_lock:
            if peer not in self._peers:
                self._peers[peer] = dict()
                self._peers[peer]['__conn'] = 1
            else:
                self._peers[peer]['__conn'] += 1

        self._logger.info(f'{peer} connected')

    def disconnect(self, peer):
        with self._peers_lock:
            if peer not in self._peers:
                raise RuntimeError(f'Tried to disconnect peer {peer} but it was never connected')
            self._peers[peer]['__conn'] -= 1
            if self._peers[peer]['__conn'] == 0:
                del self._peers[peer]

        self._logger.info(f'{peer} disconnected')

    def add_info(self, peer, info):
        with self._peers_lock:
            if peer not in self._peers:
                raise RuntimeError(f'Tried to add peer {peer} info but it was never connected')
            for k, v in info.items():
                self._peers[peer][k] = v

    def get_info(self, key):
        with self._peers_lock:
            if key in self._peers:
                return self._peers[key]

    def peers(self):
        with self._peers_lock:
            return list(self._peers.keys()), self._peers
