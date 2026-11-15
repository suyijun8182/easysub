import importlib
import os
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient


class StaticSafetyTests(unittest.TestCase):
    def setUp(self):
        self.previous_dir = os.getcwd()
        self.temp = tempfile.TemporaryDirectory()
        os.chdir(self.temp.name)
        Path('frontend_dist').mkdir()
        Path('frontend_dist/index.html').write_text('safe SPA index', encoding='utf-8')
        Path('secret.txt').write_text('outside-secret-content', encoding='utf-8')
        from app import main
        self.main = importlib.reload(main)
        self.client = TestClient(self.main.app)

    def tearDown(self):
        self.client.close()
        os.chdir(self.previous_dir)
        importlib.reload(self.main)
        self.temp.cleanup()

    def test_encoded_traversals_return_spa_without_secret(self):
        for path in ('/%2e%2e/secret.txt', '/..%2fsecret.txt', '/%2e%2e%2fsecret.txt'):
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertNotIn('outside-secret-content', response.text)
                self.assertEqual(response.text, 'safe SPA index')

    def test_index_and_frontend_route_return_index(self):
        for path in ('/index.html', '/missing/frontend/route'):
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.text, 'safe SPA index')


class IconSafetyTests(unittest.TestCase):
    setUp = StaticSafetyTests.setUp
    tearDown = StaticSafetyTests.tearDown

    def test_uploaded_svg_is_sandboxed_when_opened_directly(self):
        from app.deps import get_current_user
        from app.models import User
        self.main.app.dependency_overrides[get_current_user] = lambda: User(id=7)
        svg = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
        response = self.client.post('/api/icons/upload', files={'file': ('icon.svg', svg, 'image/svg+xml')})
        self.assertEqual(response.status_code, 200, response.text)
        response = self.client.get(response.json()['url'])
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, svg)
        self.assertEqual(response.headers.get('Content-Security-Policy'), "default-src 'none'; style-src 'unsafe-inline'; sandbox")
        self.assertEqual(response.headers.get('X-Content-Type-Options'), 'nosniff')
        cached = self.client.get(response.url, headers={'If-None-Match': response.headers['etag']})
        self.assertEqual(cached.status_code, 304)
        self.assertIn('sandbox', cached.headers.get('Content-Security-Policy', ''))
        self.assertEqual(cached.headers.get('X-Content-Type-Options'), 'nosniff')
