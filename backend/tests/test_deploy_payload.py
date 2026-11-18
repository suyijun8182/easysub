import importlib.util
from pathlib import Path
import struct
import unittest

module_path = Path(__file__).resolve().parents[2] / 'deploy/index_payload.py'
spec = importlib.util.spec_from_file_location('index_payload', module_path)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class PayloadIndexTests(unittest.TestCase):
    def test_index_reuses_embedded_data_and_encodes_bounds(self):
        binary = b'ELF-header-gzip-payload-trailer'
        result = module.index(binary, b'gzip-payload')
        self.assertEqual(result[:-64], binary)
        self.assertEqual(struct.unpack('<QQ', result[-64:-48]), (11, 12))
        self.assertEqual(result[-16:], b'EASYSUB_PAYLOAD1')
        with self.assertRaises(ValueError):
            module.index(binary, b'missing')
        with self.assertRaises(ValueError):
            module.index(binary, b'')
