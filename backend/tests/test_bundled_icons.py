import unittest
from pathlib import Path

from app import icon_library

BUNDLED = Path(__file__).resolve().parents[2] / 'frontend' / 'public' / 'preview-icons'
# Services whose icon could not be fetched from any public source; they get the
# letter placeholder. Keep this list explicit so new gaps fail the test.
EXEMPT = {
    '10010_com', '1pmobile_com', 'bandwagonhost_com', 'cht_com_tw', 'docomo_ne_jp',
    'frantech_ca', 'lycamobile_com', 'nexusbytes_com', 'quadranet_com',
}


class BundledCoverageTests(unittest.TestCase):
    def test_every_library_service_ships_an_icon_or_is_explicitly_exempt(self):
        missing = sorted(e['slug'] for e in icon_library.manifest()
                         if not (BUNDLED / f"{e['slug']}.png").is_file() and e['slug'] not in EXEMPT)
        self.assertEqual(missing, [])


if __name__ == '__main__':
    unittest.main()
