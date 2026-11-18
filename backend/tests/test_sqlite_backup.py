import json
import unittest
from datetime import date
from pathlib import Path
from sqlalchemy import event, select
from sqlalchemy.orm import Session
from tests import test_sync
from app.models import User, Subscription, Category, NotificationLog, SyncRecord
from app.services import notify, sync


class SQLiteBackupTests(unittest.TestCase):
    setUpClass = classmethod(test_sync.SyncTests.setUpClass.__func__)
    setUp = test_sync.SyncTests.setUp
    tearDown = test_sync.SyncTests.tearDown

    def make_engine(self):
        engine = test_sync.SyncTests.make_engine(self)
        @event.listens_for(engine, 'connect')
        def foreign_keys(conn, _):
            conn.execute('PRAGMA foreign_keys=ON')
        return engine

    def test_mysql_shaped_backup_restores_entities_notifications_and_sync(self):
        fixture = json.loads((Path(__file__).parent / 'fixtures/mysql-backup-debug27.json').read_text(encoding='utf-8'))
        with Session(self.engine) as db:
            db.get(User, 1).is_admin = True
            db.commit()
        r = self.client.post('/api/backup/import-all', headers=self.headers, json={'data': fixture})
        self.assertEqual(r.status_code, 200, r.text)
        with Session(self.engine) as db:
            user = db.scalar(select(User).where(User.username == 'migrated'))
            subs = db.scalars(select(Subscription).where(Subscription.user_id == user.id)).all()
            cats = db.scalars(select(Category).where(Category.user_id == user.id)).all()
            self.assertEqual((len(subs), len(cats)), (1, 1))
            self.assertEqual((subs[0].category_id, subs[0].amount, subs[0].billing_anchor_day), (cats[0].id, 19.99, 31))
            self.assertEqual(subs[0].next_renewal_date, date(2027, 2, 28))
            self.assertEqual(notify.load_config(user)['telegram']['chat_id'], '123')
            sync.capture(db, user.id)
            db.commit()
            records = db.scalars(select(SyncRecord).where(SyncRecord.user_id == user.id)).all()
            self.assertEqual(len(records), 4)
            self.assertEqual({r.kind for r in records}, {'subscriptions', 'categories', 'preferences', 'notification-config'})
            record = next(r for r in records if r.kind == 'subscriptions')
            self.assertEqual(sync.decode(record.payload)['billing_anchor_day'], 31)

    def test_delete_subscription_with_notification_under_foreign_keys(self):
        r = self.client.post('/api/subscriptions', headers=self.headers, json={'name': '有提醒记录'})
        sid = r.json()['id']
        with Session(self.engine) as db:
            db.add(NotificationLog(subscription_id=sid, user_id=1, days_before=1, status='sent'))
            db.commit()
        r = self.client.request('DELETE', f'/api/subscriptions/{sid}', headers=self.headers, json={'password': 'test-password'})
        self.assertEqual(r.status_code, 200, r.text)
        with Session(self.engine) as db:
            self.assertIsNone(db.get(Subscription, sid))
            self.assertEqual(db.scalars(select(NotificationLog)).all(), [])
