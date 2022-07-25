import multiprocessing
import os
import time
from unittest import TestCase

import logging

import numpy as np
import psutil
import tqdm.notebook

from strawb.multi_processing import MProcessIterator

formatter_list = ['%(asctime)s',
                  '%(levelname)s',
                  # Text logging level for the message ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL').
                  '%(processName)s',  # Process name (if available).
                  '%(threadName)s',  # Thread name (if available).
                  # '%(thread)d',  # Thread ID (if available).
                  # '%(name)s',  # Name of the logger (logging channel).
                  '%(funcName)s',  # Name of function containing the logging call.
                  # '%(lineno)d',  # Source line number where the logging call was issued (if available).
                  '%(message)s'  # The logged message, computed as msg % args.
                  ]

logging.basicConfig(format=";".join(formatter_list),
                    level=[logging.DEBUG, logging.INFO, logging.WARNING][1],
                    )


class ApplyResultTest:
    def __init__(self, result, error=None):
        self.result = result
        self.error = error

    def get(self):
        if self.error is None:
            return self.result
        else:
            raise self.error(self.result)

    def __repr__(self):
        return f'Result: {self.result} - Error: {self.error}'


def test_worker(i, sleep=.01, modulo_error=None):
    logging.debug(f'Start worker: {i}')
    time.sleep(sleep)
    if modulo_error is not None and i % modulo_error == modulo_error - 1:
        raise ValueError(i)
    return i * 2


class TestMultiProcessing(TestCase):
    def setUp(self) -> None:
        self.mpi = MProcessIterator()

    def test_init(self):
        self.assertIsInstance(self.mpi.sys_log_keys, set)

        mpi = MProcessIterator(log_sys_keys='all')
        self.assertIsInstance(mpi.sys_log_keys, set)

        test_keys = ['cpu_num', 'cpu_percent', 'cpu_times', 'pid', 'ppid', 'status', 'username']
        mpi = MProcessIterator(log_sys_keys=test_keys)
        self.assertIsInstance(mpi.sys_log_keys, set)
        self.assertIn('pid', mpi.sys_log_keys)

    def test_get_process_info(self):
        self.assertIsInstance(self.mpi.get_process_info(), dict)
        self.assertIsInstance(self.mpi.get_process_info(pid=os.getpid()), dict)
        self.assertIsInstance(self.mpi.get_process_info(process=psutil.Process(os.getpid())), dict)

    def test_get_process_info_w_children(self):
        self.assertIsInstance(self.mpi.get_process_info_w_children(), list)

    def test__get_sys_log__(self):
        self.assertIsInstance(self.mpi.__get_sys_log__(10), list)

    def test__update__(self):
        jobs = 5
        index = np.random.randint(0, jobs)
        self.mpi._active_jobs_dict_ = {i: ApplyResultTest(f'job_{i}') for i in range(5)}
        self.assertIn(index, self.mpi._active_jobs_dict_)
        self.assertEqual(len(self.mpi.sys_log), 0)

        self.mpi.__update__(index)
        self.assertIn(index, self.mpi._ready_dict_)
        self.assertNotIn(index, self.mpi._active_jobs_dict_)
        self.assertGreater(len(self.mpi.sys_log), 0)

    def test__get_result__(self):
        index = 3
        job = ApplyResultTest(f'job_{index}')
        self.assertEqual(f'job_{index}', self.mpi.__get_result__(index, job))

        job = ApplyResultTest(f'job_{index}', KeyError)
        print(job.error)
        self.assertRaises(KeyError, job.get)
        self.assertEqual(job.error(job.result).args, self.mpi.__get_result__(index, job).args)

    def test__thread_worker__(self):
        # Define test
        modulo_error = 3
        processes = 2
        length = np.random.randint(processes*4, processes*7)

        # Set UP
        self.mpi._active_jobs_dict_ = {}
        self.mpi._result_dict_ = {}
        self.mpi.sys_log = []
        self.mpi.pool = multiprocessing.Pool(processes=2)

        # Test
        self.mpi.__thread_worker__(test_worker, range(length))
        self.assertEqual(length, len(self.mpi.result_dict))
        self.assertEqual(0, len(self.mpi.error_dict))
        self.assertEqual(length, len(self.mpi.success_dict))

        # Set UP
        self.mpi._active_jobs_dict_ = {}
        self.mpi._result_dict_ = {}
        self.mpi.sys_log = []
        self.mpi.pool = multiprocessing.Pool(processes=2)

        # Test with error
        self.mpi.__thread_worker__(test_worker, range(length), modulo_error=modulo_error)
        self.assertEqual(length, len(self.mpi.result_dict))
        self.assertEqual(int(length/modulo_error), len(self.mpi.error_dict))
        self.assertEqual(length-int(length/modulo_error), len(self.mpi.success_dict))

        # print('_active_jobs_dict_: ', self.mpi._active_jobs_dict_)
        # print('_ready_dict_: ', self.mpi._ready_dict_)
        # print('_result_dict_: ', self.mpi._result_dict_)
        # print('sys :', '\n'.join(str(i) for i in self.mpi.sys_log))

    def test_run(self):
        # Define test
        modulo_error = 3
        processes = 2
        length = np.random.randint(processes*4, processes*7)
        self.pool_kwargs = {'processes': processes}

        # Test 1
        self.mpi.run(test_worker, range(length))
        self.assertEqual(length, len(self.mpi.result_dict))
        self.assertEqual(0, len(self.mpi.error_dict))
        self.assertEqual(length, len(self.mpi.success_dict))

        # Test 2 with errors
        self.mpi.run(test_worker, range(length), modulo_error=modulo_error)
        self.assertEqual(length, len(self.mpi.result_dict))
        self.assertEqual(int(length/modulo_error), len(self.mpi.error_dict))
        self.assertEqual(length-int(length/modulo_error), len(self.mpi.success_dict))

        # Test 2 with errors and progress bar
        print('progress')
        self._progress_bar_ = tqdm.tqdm
        self.mpi.run(test_worker, range(length), modulo_error=modulo_error)
        self.assertEqual(length, len(self.mpi.result_dict))
        self.assertEqual(int(length/modulo_error), len(self.mpi.error_dict))
        self.assertEqual(length-int(length/modulo_error), len(self.mpi.success_dict))

