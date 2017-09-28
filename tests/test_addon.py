from addondev import initializer
import os

initializer(os.path.dirname(os.path.dirname(__file__)))
import unittest
import addon


class Tester(unittest.TestCase):
    def test_root(self):
        data = addon.Root.test()
        self.assertEqual(len(data), 44)
