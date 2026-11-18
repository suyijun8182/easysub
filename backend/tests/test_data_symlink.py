import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4
from types import SimpleNamespace
from unittest.mock import patch
from fastapi import HTTPException
from app.routers import icons, sync


class DataSymlinkTests(unittest.TestCase):
    def test_data_link_allows_icons_but_rejects_traversal_and_external_links(self):
        cwd = os.getcwd()
        with TemporaryDirectory() as temporary:
            root = Path(temporary)
            release = root / 'release'
            release.mkdir()
            data = root / 'persistent'
            (data / 'icons').mkdir(parents=True)
            (data / 'icons/good.png').write_bytes(b'icon')
            (root / 'secret.png').write_bytes(b'secret')
            try:
                (release / 'data').symlink_to(data, target_is_directory=True)
                (data / 'icons/escape.png').symlink_to(root / 'secret.png')
            except OSError as e:
                self.skipTest('当前平台无法创建符号链接：'+str(e))
            os.chdir(release)
            try:
                self.assertEqual(Path(icons._contained('data/icons', 'good.png')), data / 'icons/good.png')
                for name in ['../../secret.png', 'escape.png']:
                    self.assertIsNone(icons._contained('data/icons', name))
                identity = uuid4()
                record = SimpleNamespace(user_id=7, deleted=False, payload='fixture')
                db = SimpleNamespace(get=lambda *_: record)
                for name, allowed in [('good.png', True), ('../../secret.png', False), ('escape.png', False)]:
                    with patch.object(sync.service, 'decode', return_value={'icon': '/static/icons/'+name}):
                        if allowed:
                            self.assertEqual(Path(sync.download_icon(identity, SimpleNamespace(id=7), db).path), data / 'icons/good.png')
                        else:
                            with self.assertRaises(HTTPException):
                                sync.download_icon(identity, SimpleNamespace(id=7), db)
            finally:
                os.chdir(cwd)
