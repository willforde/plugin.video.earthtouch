from codequickcli import initialize_addon
initialize_addon("plugin.video.earthtouch")
import unittest
import addon


class Tester(unittest.TestCase):
    def test_root(self):
        data = addon.Root.test()
        self.assertEqual(len(data), 43)
