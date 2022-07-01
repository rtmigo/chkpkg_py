import sys
import unittest

from chkpkg._require_pytyped import get_module_path


class TestGetModulePath(unittest.TestCase):
    def test(self):
        p = get_module_path(sys.executable, 'urllib3')

        # .../site-packages/urllib3/__init__.py
        self.assertTrue(p.exists())
        self.assertTrue(p.is_file())
