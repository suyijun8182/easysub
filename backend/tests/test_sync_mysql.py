"""Runs only against an explicitly named disposable CI database."""
import os
import unittest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url
from app.database import Base
from app.migrate import run_migrations
from tests import test_sync as base

@unittest.skipUnless(os.environ.get('EASYSUB_TEST_MYSQL_URL'), 'Dedicated MySQL CI service not configured')
class MySQLSyncTests(base.SyncTests):
    def make_engine(self):
        url = make_url(os.environ['EASYSUB_TEST_MYSQL_URL'])
        if url.database != 'easysub_ci_test' or url.host not in {'localhost', '127.0.0.1', 'mysql'}:
            raise RuntimeError('Refusing to reset anything except the dedicated local easysub_ci_test database')
        engine = create_engine(url, isolation_level='READ COMMITTED')
        Base.metadata.drop_all(engine)
        return engine

    def test_existing_text_payload_columns_are_expanded_before_writes(self):
        with self.engine.begin() as conn:
            for table in ('sync_records', 'sync_changes', 'sync_receipts'):
                conn.execute(text(f'ALTER TABLE `{table}` MODIFY COLUMN payload TEXT NOT NULL'))
        run_migrations(self.engine)
        run_migrations(self.engine)
        with self.engine.connect() as conn:
            for table in ('sync_records', 'sync_changes', 'sync_receipts'):
                actual = conn.execute(text("SELECT DATA_TYPE FROM information_schema.columns WHERE table_schema=DATABASE() AND table_name=:table AND column_name='payload'"), {'table': table}).scalar()
                self.assertEqual(actual.lower(), 'longtext')
        self.test_long_existing_notes_survive_encrypted_journal_and_receipt()
