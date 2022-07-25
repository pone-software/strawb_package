import gc

import multiprocessing
import threading
import logging

import psutil
import os
import time


class MProcessIterator:
    def __init__(self, progress_bar=None, log_sys_keys=None, with_sys_log=False, *args, **kwargs):
        self.logger = logging.getLogger(type(self).__name__)

        self.pool_args = args
        self.pool_kwargs = kwargs

        self._progress_bar_ = progress_bar
        self.progress_bar = None

        self._total_jobs_ = 0
        self._active_jobs_dict_ = {}
        self._ready_dict_ = {}
        self._result_dict_ = {}

        # System parameter logging
        self.sys_log_keys = log_sys_keys
        self.with_sys_log = with_sys_log

        available_keys = set(psutil.Process(os.getpid()).as_dict().keys())
        if isinstance(self.sys_log_keys, str) == 'all':
            self.sys_log_keys = available_keys
        elif self.sys_log_keys is None:
            self.sys_log_keys = ['cpu_num', 'cpu_percent', 'cpu_times',
                                 'create_time', 'cwd', 'memory_full_info', 'memory_percent',
                                 'name', 'nice', 'num_ctx_switches', 'num_fds', 'num_threads',
                                 'open_files', 'pid', 'ppid', 'status', 'username']

        self.sys_log_keys = set(self.sys_log_keys).intersection(available_keys)
        self.sys_log = []

        # Locks
        self.pool = None
        self._multiprocessing_lock_ = multiprocessing.Lock()
        self._threading_lock_ = threading.Lock()

        # Thread
        self._thread_ = None

        self._active_ = False

    @property
    def active(self):
        """True if jobs are running, else False"""
        return self._active_

    def terminate(self):
        """Terminate jobs"""
        self._active_ = False
        self.pool.terminate()
        self.pool.close()
        self.pool.join()
        self._thread_.join()

    def get_process_info(self, pid=None, process=None):
        if process is not None:
            process = process
        elif pid is None:
            process = psutil.Process(os.getpid())
        else:
            process = psutil.Process(pid)

        # Additional parameters
        # 'io_counters', 'environ', 'exe', 'cpu_affinity', 'connections', 'memory_maps', 'cmdline',
        # 'threads', 'memory_info', 'gids', 'uids', 'terminal', 'ionice'
        res = process.as_dict(self.sys_log_keys)
        res['time'] = time.time()

        if 'memory_full_info' in res:
            temp_res = res.pop('memory_full_info')
            for i in ['rss', 'vms', 'shared', 'text', 'lib', 'data', 'dirty', 'uss', 'pss', 'swap']:
                try:
                    res[f'memory_info_{i}'] = temp_res.__getattribute__(i)
                except AttributeError:
                    pass

        if 'cpu_times' in res:
            temp_res = res.pop('cpu_times')
            for i in ['user', 'system', 'children_user', 'children_system', 'iowait']:
                try:
                    res[f'cpu_times_{i}'] = temp_res.__getattribute__(i)
                except AttributeError:
                    pass

        if 'open_files' in res:
            res['open_files'] = [i.path for i in res['open_files']]
        return res

    def get_process_info_w_children(self, pid=None, with_childs=True, recursive=True):
        if pid is None:
            pid = os.getpid()

        process = psutil.Process(pid)
        res = [self.get_process_info(process=process)]
        if with_childs:
            for process_i in process.children(recursive=recursive):
                res.append(self.get_process_info(process=process_i))
        return res

    def __get_sys_log__(self, index, log_type='start'):
        """Wrapper for get_process_info_w_children which adds index and log_type to sys_log."""
        res = self.get_process_info_w_children()
        for i in range(len(res)):
            res[i]['index'] = index
            res[i]['log_type'] = log_type
        return res

    def __update__(self, index):
        """Update the progress bar and sys_log, both if specified."""
        self.logger.debug(f"Update: {index}")
        with self._threading_lock_:
            self._ready_dict_.update({index: self._active_jobs_dict_.pop(index)})
            if self.with_sys_log:
                self.sys_log.extend(self.__get_sys_log__(index, 'end'))

        if self.progress_bar is not None:
            self.progress_bar.update()

    def __get_result__(self, index, job):
        """Return True if job finished."""
        try:
            result = job.get()
            self.logger.debug(f"Get: {index}")

        except Exception as exc:
            self.logger.warning(f'Get error at {index} with: {exc.__repr__()}')
            result = exc

        return result

    def __gen_callback_i__(self, index, callback=None):
        """The callbacks need to include the index for result tracking. Add it here."""
        if callback is None:
            def f(*args: list):
                self.__update__(index)

            return f
        else:
            def f(*args):
                callback(*args)
                self.__update__(index)

            return f

    def __thread_worker__(self, func, iterable, args=(), callback=None, error_callback=None, **kwargs):
        """Function for the worker. It takes care of submitting jobs to the pool and
        PARAMETER
        ---------
        func: executable
        iterable: iterable
            function must take the iterable[i] as first argument, i.e. func(iterable[i], *args, **kwargs)
        args, kwargs: list, dict, optional
            parsed to func, i.e. func(iterable[i], *args, **kwargs). args and kwargs are fixed and don't iterate.
        callback, error_callback: executable
            executables which are executed when a job (res=func(iterable[i], *args, **kwargs)) finished.
            Takes `callback` if func returns normal, and `error_callback` if func raise an exception.
            Both function must return immediately!
        """

        self.logger.debug(f"---- START ----")
        self._active_ = True

        self._total_jobs_ = len(iterable)

        try:
            len(args)
        except TypeError:
            args = list([args])

        for i, iterable_i in enumerate(iterable):
            if not self.active:
                break

            self.logger.debug(f"Init: {i}")
            if self.with_sys_log:
                self.sys_log.extend(self.__get_sys_log__(i, 'start'))

            # add job to pool
            with self._threading_lock_:
                self._active_jobs_dict_[i] = self.pool.apply_async(
                    func=func,
                    args=(iterable_i, *args),
                    kwds=kwargs,
                    callback=self.__gen_callback_i__(i, callback),
                    error_callback=self.__gen_callback_i__(i, error_callback),
                )

            # wait for task to finish and keep 2-times the number of tasks in the pool as processes

            self.logger.debug(f"Active:{len(self._active_jobs_dict_)}, len(iterable):{len(iterable)}, i: {i}")
            if len(self._active_jobs_dict_) > self.pool._processes * 2 or len(iterable) - 1 == i:
                self.logger.debug(f"Check or wait for finished jobs: {self._ready_dict_}")

                # wait for a job to get ready
                j = 0
                while not len(self._ready_dict_):
                    time.sleep(.01)
                    j += 1

                # self.logger.debug(
                #     f"After {j} waits, {len(self._ready_dict_)} jobs ready: {list(self._ready_dict_.keys())}")

                # get the results, check_once: loop only once if not at the end of the iterable
                # else loop until all jobs done.
                j = 0
                while len(self._ready_dict_) or len(iterable) - 1 == i:
                    if len(self._active_jobs_dict_) == 0 and len(self._ready_dict_) == 0:
                        self._active_ = False
                        break
                    elif len(self._ready_dict_) == 0:
                        time.sleep(.1)
                        j += 1
                    else:
                        key_0 = list(self._ready_dict_.keys())[0]
                        self.logger.debug(f"After {j} waits, get ready job: {key_0}")
                        j = 0
                        with self._threading_lock_:
                            result = self.__get_result__(key_0, self._ready_dict_.pop(key_0))
                        self._result_dict_.update({key_0: result})

                        # clean up RAM
                        c1, c2, c3 = gc.get_count(), gc.collect(), gc.get_count()
                        # self.logger.debug(f'Clean up gc: {c1}, {c2}, {c3}')

        self.pool.close()
        self.pool.join()

        # close the progress bar
        if self.progress_bar is not None:
            self.progress_bar.close()

        c1, c2, c3 = gc.get_count(), gc.collect(), gc.get_count()
        self.logger.debug(f'Stop Iteration and clean up gc: {c1}, {c2}, {c3}')

    # Public
    def run_async(self, func, iterable, args=(), pbar_kwargs=None, callback=None, error_callback=None, **kwargs):
        """Run func(iterable[i]) for all i on multiple processors asynchronously (function executes not blocking).

        PARAMETER
        ---------
        func: executable
        iterable: iterable
            function must take the iterable[i] as first argument, i.e. func(iterable[i], *args, **kwargs)
        args, kwargs: list, dict, optional
            parsed to func, i.e. func(iterable[i], *args, **kwargs). args and kwargs are fixed and don't iterate.
        pbar_kwargs: dict, optional
            kwargs for a progressbar (supports only tqdm). The progressbar typ must be specified in the init,
            e.g. tqdm.tqdm or tqdm.notebook.tqdm
        callback, error_callback: executable
            executables which are executed when a job (res=func(iterable[i], *args, **kwargs)) finished.
            Takes `callback` if func returns normal, and `error_callback` if func raise an exception.
            Both function must return immediately!
        """
        if pbar_kwargs is None:
            pbar_kwargs = {}

        if self.active:
            return

        self.progress_bar = None
        if self._progress_bar_ is not None:
            self.progress_bar = self._progress_bar_(iterable, position=0, **pbar_kwargs)

        self.pool = multiprocessing.Pool(*self.pool_args, **self.pool_kwargs)

        # can be done without lock
        self._active_jobs_dict_ = {}
        self._result_dict_ = {}
        self._ready_dict_ = {}
        self.sys_log = []

        self._thread_ = threading.Thread(target=self.__thread_worker__,
                                         kwargs={'func': func,
                                                 'iterable': iterable,
                                                 'callback': callback,
                                                 'error_callback': error_callback,
                                                 'args': args,
                                                 **kwargs})
        self._thread_.start()

        return None

    def run(self, *args, **kwargs):
        """Same as run_async, but blocking."""
        if not self.active:
            self.run_async(*args, **kwargs)
            time.sleep(.001)
            self._thread_.join()
            return self.result_dict
        else:
            raise RuntimeError('Worker is active.')

    @property
    def result_dict(self):
        """The results of finished jobs as dict - {index_job: func(iterable[index_job], *args, **kwargs)}"""
        with self._threading_lock_:
            return self._result_dict_.copy()

    @property
    def success_dict(self):
        """The results of all successfully finished jobs as dict -
        {index_job: func(iterable[index_job], *args, **kwargs)}"""
        success_dict = {}
        with self._threading_lock_:
            for i in self._result_dict_:
                if not isinstance(self._result_dict_[i], Exception):
                    success_dict.update({i: self._result_dict_[i]})
            return success_dict

    @property
    def error_dict(self):
        """The results of all unsuccessfully finished jobs as dict -
        {index_job: func(iterable[index_job], *args, **kwargs)}"""
        error_dict = {}
        with self._threading_lock_:
            for i in self._result_dict_:
                if isinstance(self._result_dict_[i], Exception):
                    error_dict.update({i: self._result_dict_[i]})
            return error_dict

    @property
    def number_total_jobs(self):
        """Number of total submitted jobs."""
        return self._total_jobs_

    @property
    def number_active_jobs(self):
        """Number of active jobs in the pool."""
        return len(self._active_jobs_dict_)

    @property
    def number_ready_jobs(self):
        """Number of jobs where the result can be collected."""
        return len(self._ready_dict_)

    @property
    def number_finished_jobs(self):
        """Number of finished jobs."""
        return len(self._result_dict_)
