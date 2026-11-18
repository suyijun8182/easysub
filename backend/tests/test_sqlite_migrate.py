import unittest
from sqlalchemy import create_engine, inspect, text
from app.migrate import run_migrations, _COLUMNS


class SQLiteMigrationTests(unittest.TestCase):
    def test_old_tables_gain_all_columns_and_migration_is_idempotent(self):
        engine = create_engine('sqlite://')
        try:
            with engine.begin() as conn:
                conn.execute(text('create table subscriptions (id integer primary key, name text)'))
                conn.execute(text('create table users (id integer primary key, username text)'))
                conn.execute(text("insert into subscriptions values (1, '旧数据')"))
            run_migrations(engine)
            run_migrations(engine)
            for table, column, _ in _COLUMNS:
                self.assertIn(column, {c['name'] for c in inspect(engine).get_columns(table)})
            with engine.connect() as conn:
                self.assertIsNone(conn.execute(text('select billing_anchor_day from subscriptions')).scalar())
                self.assertEqual(conn.execute(text('select name from subscriptions')).scalar(), '旧数据')
        finally:
            engine.dispose()
