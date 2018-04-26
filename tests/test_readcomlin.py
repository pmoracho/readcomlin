# -*- coding: utf-8 -*-

"""
# Copyright (c) 2014 Patricio Moracho <pmoracho@gmail.com>
#
# test_readcomline
#
"""

import sys
import re
import unittest
import re

sys.path.append('.')
sys.path.append('..')

from readcomlin import load_plugins

class ExtractionTest(unittest.TestCase):

    def test_each_format_versus_itself(self):
        """Prueba de cada formato sobre si mismo"""
        for f1 in self._lst_formatos:
            self.assertEqual(f1.sample_ret, f1.get_data(f1.sample_data),"{0} not match!".format(f1.nombre))

    def test_each_format_versus_others(self):
        """Prueba de cada formato sobre los otros"""
        for f1 in self._lst_formatos:
            for f2 in [e for e in self._lst_formatos if e.nombre != f1.nombre]:
                self.assertIsNone(f2.get_data(f1.sample_data), "{0} vs {1} match!".format(f1.nombre, f2.nombre))

    @classmethod
    def setUpClass(cls):
        cls._lst_formatos = list(load_plugins("plugins"))
        sorted(cls._lst_formatos, key=lambda x: (x.orden, x.nombre))

if __name__ == '__main__':
    unittest.main()
