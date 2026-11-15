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
