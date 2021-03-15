import inspect
import threading
import time

import tensorflow as tf


def squash_correction_log_prob(dist, x):
    return dist.log_prob(x) - tf.math.log(tf.maximum(1 - tf.square(tf.tanh(x)), 1e-2))


def squash_correction_prob(dist, x):
    return dist.prob(x) / (tf.maximum(1 - tf.square(tf.tanh(x)), 1e-2))


def debug(name, x):
    tf.print(name, tf.reduce_min(x), tf.reduce_mean(x), tf.reduce_max(x))


def debug_grad(grads):
    for grad in grads:
        if grad is not None:
            debug(grad.name, grad)


def debug_grad_com(grads, grads1):
    for i, grad in enumerate(grads):
        debug(grad.name, grad - grads1[i])


def gen_pre_n_actions(n_actions, keep_last_action=False):
    return tf.concat([
        tf.zeros_like(n_actions[:, 0:1, ...]),
        n_actions if keep_last_action else n_actions[:, :-1, ...]
    ], axis=1)


def np_to_tensor(fn):
    def c(*args, **kwargs):
        return fn(*[k if k is not None else tf.zeros((0,)) for k in args],
                  **{k: v if v is not None else tf.zeros((0,)) for k, v in kwargs.items()})

    return c


def scale_h(x, epsilon=0.001):
    return tf.sign(x) * (tf.sqrt(tf.abs(x) + 1) - 1) + epsilon * x


def scale_inverse_h(x, epsilon=0.001):
    t = 1 + 4 * epsilon * (tf.abs(x) + 1 + epsilon)
    return tf.sign(x) * ((tf.sqrt(t) - 1) / (2 * epsilon) - 1)


def _format_lock_log(custom_log=None, start_time=None):
    stack = inspect.stack()

    if custom_log is None:
        stack_log = ''
        for i, frame in enumerate(stack):
            if '__enter__' in frame.function:
                frame = stack[i + 1]
                stack_log = f'[{frame.filename}, {frame.lineno}, {frame.function}]'
                break

    if start_time is None:
        if custom_log:
            return f'Timeout! {custom_log}, ident: {threading.get_ident()}'
        else:
            return f'Timeout! {stack_log}, ident: {threading.get_ident()}'
    else:
        if custom_log:
            return f'Acquired in {time.time()-start_time:.1f}s. {custom_log}, ident: {threading.get_ident()}'
        else:
            return f'Acquired in {time.time()-start_time:.1f}s. {stack_log}, ident: {threading.get_ident()}'


class MaxMutexCheck:
    def __init__(self, max_num):
        self._lock = threading.RLock()
        self._max = max_num
        self._count = 0

    def __enter__(self):
        with self._lock:
            self._count += 1

            if self._count <= self._max:
                return True
            else:
                return False

    def __exit__(self, exc_type, exc_value, traceback):
        with self._lock:
            self._count -= 1


class RLock(object):
    _locked = False

    def __init__(self, timeout=-1, logger=None):
        self._lock = threading.RLock()
        self._timeout = timeout
        self._logger = logger

    def __enter__(self, custom_log=None, timeout=-1):
        timeout = timeout if timeout != -1 else self._timeout
        start_time = time.time()
        timeout_occur = False

        while not self._lock.acquire(timeout=timeout):
            if not timeout_occur and self._logger is not None:
                timeout_occur = True
                self._logger.warning(_format_lock_log(custom_log))

        if timeout_occur and self._logger is not None:
            self._logger.warning(_format_lock_log(custom_log, start_time))

        self._locked = True

    def __exit__(self, exc_type, exc_value, traceback):
        if self._locked:
            self._lock.release()


class ReadWriteLock:
    def __init__(self, max_read=None, read_timeout=-1, write_timeout=-1, write_first=True, logger=None):
        self.max_read = max_read
        self._read_timeout = read_timeout
        self._write_timeout = write_timeout
        self.write_first = write_first
        self._logger = logger

        self._lock = threading.Lock()
        self._rcond = threading.Condition(self._lock)
        self._wcond = threading.Condition(self._lock)

        self._read_waiter = 0  # Number of threads waiting to acquire a read lock
        self._write_waiter = 0  # Number of threads waiting to acquire a write lock
        self._state = 0
        # postive: Number of threads being read
        # negative: Number of threads being write
        self._owners = []  # The list of threads idents being operate

    def write(self, custom_log=None):
        return self._write_lock(self, custom_log)

    def read(self, custom_log=None):
        return self._read_lock(self, custom_log)

    class _write_lock:
        def __init__(self, rwlock, custom_log=None):
            self._rwlock = rwlock
            self._custom_log = custom_log

        def __enter__(self):
            self._rwlock.write_acquire(self._custom_log)

        def __exit__(self, exc_type, exc_value, traceback):
            self._rwlock.unlock()

    class _read_lock:
        def __init__(self, rwlock, custom_log=None):
            self._rwlock = rwlock
            self._custom_log = custom_log

        def __enter__(self):
            self._rwlock.read_acquire(self._custom_log)

        def __exit__(self, exc_type, exc_value, traceback):
            self._rwlock.unlock()

    def write_acquire(self, custom_log=None):
        me = threading.get_ident()
        with self._lock:
            self._write_waiter += 1
            start_time = time.time()
            timeout_occur = 0

            while not self._wcond.wait_for(lambda: self._write_acquire(me),
                                           timeout=self._write_timeout):
                if not timeout_occur and self._logger is not None:
                    self._logger.warning(f'Write {_format_lock_log(custom_log)}')
                timeout_occur += 1

                if timeout_occur > 10 and self._logger is not None:
                    self._logger.warning('.'.join([str(o) for o in self._owners]))

            if timeout_occur and self._logger is not None:
                self._logger.warning(f'Write {_format_lock_log(custom_log, start_time)}')
            self._write_waiter -= 1
        return True

    def _write_acquire(self, me):
        # If only the lock is free or current thread is operating
        if self._state == 0 or (self._state < 0 and me in self._owners):
            self._state -= 1
            self._owners.append(me)
            return True
        if self._state > 0 and me in self._owners:
            raise RuntimeError('Cannot recursively wlock an acquired rlock')
        return False

    def read_acquire(self, custom_log=None):
        me = threading.get_ident()
        with self._lock:
            self._read_waiter += 1
            start_time = time.time()
            timeout_occur = 0

            while not self._rcond.wait_for(lambda: self._read_acquire(me), timeout=self._read_timeout):
                if not timeout_occur and self._logger is not None:
                    self._logger.warning(f'Read {_format_lock_log(custom_log)}')
                timeout_occur += 1

                if timeout_occur > 10 and self._logger is not None:
                    self._logger.warning('.'.join([str(o) for o in self._owners]))

            if timeout_occur and self._logger is not None:
                self._logger.warning(f'Read {_format_lock_log(custom_log, start_time)}')
            self._read_waiter -= 1
        return True

    def _read_acquire(self, me):
        if self._state < 0 or (self.max_read is not None and self._state == self.max_read):
            # If write lock is acquired or the number of threads being read reaches the maximum
            return False

        if self._write_waiter == 0:
            ok = True
        else:
            ok = me in self._owners
        if ok or not self.write_first:
            self._state += 1
            self._owners.append(me)
            return True

        return False

    def unlock(self):
        me = threading.get_ident()
        with self._lock:
            try:
                self._owners.remove(me)
            except ValueError:
                raise RuntimeError('Cannot release un-acquired lock')

            if self._state > 0:
                self._state -= 1
            else:
                self._state += 1
            if not self._state:
                if self._write_waiter and self.write_first:
                    self._wcond.notify()
                elif self._read_waiter:
                    self._rcond.notify_all()
                elif self._write_waiter:
                    self._wcond.notify()
