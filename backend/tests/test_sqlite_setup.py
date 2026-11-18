import json
import os
import sqlite3
from contextlib import closing
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import text

from app import bootstrap, database
from app.routers import setup


class SQLiteSetupTests(unittest.TestCase):
    def setUp(self):
        self.cwd = os.getcwd()
        self.temp = TemporaryDirectory()
        os.chdir(self.temp.name)
        database.reset_engine()
        self.scheduler = patch('app.services.scheduler.start_scheduler')
        self.scheduler.start()
        app = FastAPI()
        app.include_router(setup.router)
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        database.reset_engine()
        self.scheduler.stop()
        os.chdir(self.cwd)
        self.temp.cleanup()

    def test_sqlite_test_save_and_pragmas(self):
        cfg = {'engine': 'sqlite', 'path': 'data/easysub.db'}
        r = self.client.post('/api/setup/test', json=cfg)
        self.assertEqual(r.status_code, 200, r.text)
        r = self.client.post('/api/setup/save', json=cfg)
        self.assertEqual(r.status_code, 200, r.text)
        self.assertEqual(bootstrap.load_config(), cfg)
        with database.engine.connect() as conn:
            for key, expected in [('journal_mode', 'wal'), ('foreign_keys', 1), ('busy_timeout', 30000), ('synchronous', 1)]:
                self.assertEqual(conn.execute(text('PRAGMA '+key)).scalar(), expected)

    def test_auto_backup_emits_encrypted_json_and_sqlite_snapshot(self):
        from app.services import autobackup
        r = self.client.post('/api/setup/save', json={'engine': 'sqlite', 'path': 'data/easysub.db'})
        self.assertEqual(r.status_code, 200, r.text)
        with patch.object(autobackup.settings, 'backup_password', 'backup-password-fixture'):
            result = autobackup.run_auto_backup()
        self.assertTrue(result['ok'])
        payload = json.loads((Path('data/backups') / result['file']).read_text(encoding='utf-8'))
        self.assertIn('format', payload)
        self.assertNotIn('users', payload)
        self.assertEqual(len(list(Path('data/backups').glob('sqlite-*.db'))), 1)

    def test_unsafe_paths_are_rejected_by_both_endpoints(self):
        for path in ['../x.db', 'data/../x.db', '/tmp/x.db', 'C:/x.db', 'data2/x.db', 'data/../../x.db', 'data\\..\\x.db']:
            for route in ['test', 'save']:
                r = self.client.post('/api/setup/'+route, json={'engine': 'sqlite', 'path': path})
                self.assertIn(r.status_code, [400, 422], (path, r.text))
    def test_symlink_path_cannot_escape_data_directory(self):
        Path('outside').mkdir()
        Path('data').mkdir(exist_ok=True)
        try:
            Path('data/link').symlink_to(Path('outside').resolve(), target_is_directory=True)
        except OSError as e:
            self.skipTest('当前系统不允许创建符号链接：'+str(e))
        with self.assertRaises(ValueError):
            bootstrap.build_url({'engine': 'sqlite', 'path': 'data/link/x.db'})

    def test_legacy_config_and_headless_idempotence(self):
        cfg = {'host': 'db', 'user': 'u', 'database': 'old'}
        self.assertTrue(bootstrap.build_url(cfg).startswith('mysql+pymysql://'))
        with patch.dict(os.environ, {'EASYSUB_DB': 'sqlite'}):
            self.assertTrue(database.connect_from_saved_config(force=True))
            first = bootstrap.load_config()
            with database.engine.connect() as conn:
                count = conn.execute(text('select count(*) from categories')).scalar()
            database.reset_engine()
            self.assertTrue(database.connect_from_saved_config(force=True))
            self.assertEqual(bootstrap.load_config(), first)
            with database.engine.connect() as conn:
                self.assertEqual(conn.execute(text('select count(*) from categories')).scalar(), count)

    def test_headless_setting_preserves_existing_mysql_config(self):
        cfg = {'host': 'db', 'user': 'u', 'database': 'old'}
        bootstrap.save_config(cfg)
        with patch.dict(os.environ, {'EASYSUB_DB': 'sqlite'}):
            bootstrap.auto_configure()
        self.assertEqual(bootstrap.load_config(), cfg)

    def test_sqlite_snapshot_retains_seven_consistent_copies(self):
        from app.services import autobackup
        database.init_engine(bootstrap.build_url({'engine': 'sqlite', 'path': 'data/easysub.db'}))
        with database.engine.begin() as conn:
            conn.execute(text('create table sample (value text)'))
            conn.execute(text("insert into sample values ('WAL 数据')"))
        Path('data/backups').mkdir()
        for n in range(10):
            autobackup.sqlite_snapshot(f'202601{n+1:02}')
        copies = sorted(Path('data/backups').glob('sqlite-*.db'))
        self.assertEqual(len(copies), 7)
        with closing(sqlite3.connect(copies[-1])) as db:
            self.assertEqual(db.execute('select value from sample').fetchone()[0], 'WAL 数据')
