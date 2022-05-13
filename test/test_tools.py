import os
import random
from unittest import TestCase

import numpy as np

from src.strawb.config_parser import Config
from src.strawb.base_file_handler import BaseFileHandler
from src.strawb.tools import unique_steps


class TestTools(TestCase):
    def test_unique_steps(self):
        states = [np.array([-1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 2, 2, 2, 3, 4, 4, 5, 5]),
                  np.array([-1, -1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 2, 2, 2, 3, 4, 4, 5]),
                  np.array([-1, -1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 2, 2, 2, 3, 4, 4, 5, 5]),
                  ]

        # one starting point and step: 3 only one
        state = np.array([-1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 2, 2, 2, 3, 4, 4, 5, 5])
        res_s = np.array([-1, -1, 0, 0, 1, 1, 0, 0, 2, 2, 3, 3, 4, 4, 5, 5])
        res_t = np.array([0., 0.75, 1., 3., 4., 7., 8., 9., 10., 12., 13., 13., 14., 15., 16., 17.])
        t = np.arange(len(state))

        t_steps, state_steps = unique_steps(t, state)
        self.assertTrue(np.all(res_s.reshape((-1, 2)) == state_steps))
        self.assertTrue(np.all(res_t.reshape((-1, 2)) == t_steps))

        # one end point and step: 3 only one
        state = np.array([-1, -1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 2, 2, 2, 3, 4, 4, 5])
        res_s = np.array([-1, -1, 0, 0, 1, 1, 0, 0, 2, 2, 3, 3, 4, 4, 5, 5])
        res_t = np.array([0.0, 1.0, 2.0, 4.0, 5.0, 8.0, 9.0, 10.0, 11.0, 13.0, 14.0, 14.75, 15.0, 16.0, 17.0, 17.0])
        t = np.arange(len(state))

        t_steps, state_steps = unique_steps(t, state)
        self.assertTrue(np.all(res_s.reshape((-1, 2)) == state_steps))
        self.assertTrue(np.all(res_t.reshape((-1, 2)) == t_steps))

        # all steps double
        state = np.array([-1, -1, 0, 0, 0, 1, 1, 1, 1, 0, 0, 2, 2, 2, 3, 4, 4, 5, 5])
        res_s = np.array([-1, -1, 0, 0, 1, 1, 0, 0, 2, 2, 3, 3, 4, 4, 5, 5])
        res_t = np.array([0., 1., 2., 4., 5., 8., 9., 10., 11., 13., 14., 14., 15., 16., 17., 18.])
        t = np.arange(len(state))

        t_steps, state_steps = unique_steps(t, state)
        # print('[', ", ".join(t_steps.flatten().astype(str)), ']')
        # print('[', ", ".join(state_steps.flatten().astype(str)), ']')

        self.assertTrue(np.all(res_s.reshape((-1, 2)) == state_steps))
        self.assertTrue(np.all(res_t.reshape((-1, 2)) == t_steps))
