import unittest

# Testing specific imports
import addon


class Tester(unittest.TestCase):
    def test_root(self):
        data = addon.Root.test()
        self.assertGreater(len(data), 40)
