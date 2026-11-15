import importlib
import os
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app import icon_library

PNG = b'\x89PNG\r\n\x1a\nbundled'


class LibraryIconTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.addCleanup(os.chdir, os.getcwd())
        root = Path(self.temp.name)
        (root / 'backend').mkdir()
        os.chdir(root / 'backend')
        from app.routers import icons
        self.icons = importlib.reload(icons)
        app = FastAPI()
        app.include_router(self.icons.router)
        self.client = TestClient(app)
        self.addCleanup(self.client.close)
        self.entry = icon_library.manifest()[0]
        self.slug = self.entry['slug']

    def get(self, slug=None):
        return self.client.get(f'/api/icons/library/{slug or self.slug}.png')

    def test_image_bundled_in_docker_dist_is_served_without_network(self):
        target = Path('frontend_dist/preview-icons'); target.mkdir(parents=True)
        (target / f'{self.slug}.png').write_bytes(PNG)
        with mock.patch.object(self.icons.httpx, 'get') as fetch:
            response = self.get()
        fetch.assert_not_called()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, PNG)

    def test_image_bundled_in_source_checkout_is_served_without_network(self):
        target = Path('../frontend/public/preview-icons'); target.mkdir(parents=True)
        (target / f'{self.slug}.png').write_bytes(PNG)
        with mock.patch.object(self.icons.httpx, 'get') as fetch:
            response = self.get()
        fetch.assert_not_called()
        self.assertEqual(response.content, PNG)

    def test_download_cache_wins_over_bundled_copy(self):
        Path('data/icons/library').mkdir(parents=True)
        Path(f'data/icons/library/{self.slug}.png').write_bytes(b'cached')
        Path('frontend_dist/preview-icons').mkdir(parents=True)
        Path(f'frontend_dist/preview-icons/{self.slug}.png').write_bytes(PNG)
        with mock.patch.object(self.icons.httpx, 'get') as fetch:
            self.assertEqual(self.get().content, b'cached')
        fetch.assert_not_called()

    def test_failed_download_returns_cached_placeholder_and_is_not_retried_for_six_hours(self):
        with mock.patch.object(self.icons.httpx, 'get', side_effect=OSError('blocked')) as fetch:
            first = self.get()
            second = self.get()
            self.assertEqual(fetch.call_count, 1)
            self.assertEqual(fetch.call_args.kwargs['timeout'], 4)
            with mock.patch.object(self.icons.time, 'monotonic', return_value=time.monotonic() + 6 * 3600 + 1):
                self.get()
            self.assertEqual(fetch.call_count, 2)
        for response in (first, second):
            self.assertEqual(response.status_code, 200)
            self.assertTrue(response.headers['content-type'].startswith('image/svg+xml'))
            self.assertIn('max-age=86400', response.headers['cache-control'])
            self.assertIn(self.entry['name'][0], response.text)
        self.assertFalse(Path(f'data/icons/library/{self.slug}.png').exists())

    def test_placeholder_escapes_markup_in_names(self):
        svg = self.icons.placeholder_svg('<script>')
        self.assertNotIn('<script', svg)

    def test_unknown_slug_is_still_404(self):
        with mock.patch.object(self.icons.httpx, 'get') as fetch:
            self.assertEqual(self.get('not_a_known_service').status_code, 404)
        fetch.assert_not_called()


if __name__ == '__main__':
    unittest.main()
