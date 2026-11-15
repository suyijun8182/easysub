import unittest
from datetime import date, datetime, timedelta, timezone
from unittest.mock import patch

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import User, Subscription, NotificationLog
from app.services import scheduler, notify


class NotificationRetryTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine('sqlite://', connect_args={'check_same_thread': False}, poolclass=StaticPool)
        Base.metadata.create_all(self.engine)
        self.sessions = sessionmaker(self.engine)
        with self.sessions() as db:
            db.add(User(id=1, username='alice', email='alice@example.com', password_hash='unused', notify_config={'telegram': {'enabled': True}, 'email': {'enabled': True}}))
            db.add(Subscription(id=1, user_id=1, name='SIM', amount=1, next_renewal_date=date.today(), remind_days_before='0'))
            db.commit()

    def tearDown(self):
        self.engine.dispose()

    def test_partial_failure_retries_only_failed_channel_with_backoff(self):
        calls = []
        def send(channel, *args, **kwargs):
            calls.append(channel)
            if channel == 'email' and calls.count('email') == 1:
                raise RuntimeError('temporary failure')
        with patch.object(scheduler.database, 'SessionLocal', self.sessions), patch.dict(notify._SENDERS, {'email': lambda *a: send('email'), 'telegram': lambda *a: send('telegram')}), patch.object(notify, '_send_telegram', side_effect=lambda *a: send('telegram')):
            scheduler.run_reminder_scan()
            scheduler.run_reminder_scan()
            self.assertEqual(calls, ['telegram', 'email'])
            with self.sessions() as db:
                for row in db.scalars(select(NotificationLog)):
                    row.sent_at = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(seconds=301)
                db.commit()
            scheduler.run_reminder_scan(retry_only=True)
            self.assertEqual(calls, ['telegram', 'email', 'email'])
            scheduler.run_reminder_scan()
            self.assertEqual(len(calls), 3)
        with self.sessions() as db:
            self.assertEqual({row.channel for row in db.scalars(select(NotificationLog).where(NotificationLog.status == 'sent'))}, {'telegram', 'email'})

    def test_retry_job_does_not_send_new_events_or_renewed_subscriptions(self):
        with patch.object(scheduler.database, 'SessionLocal', self.sessions), patch.object(notify, 'dispatch', return_value=[{'channel': 'telegram', 'ok': True}, {'channel': 'email', 'ok': True}]) as send:
            scheduler.run_reminder_scan(retry_only=True)
            send.assert_not_called()
            scheduler.run_reminder_scan()
            self.assertEqual(send.call_count, 1)
            with self.sessions() as db:
                db.get(Subscription, 1).next_renewal_date = date.today() + timedelta(days=30); db.commit()
            scheduler.run_reminder_scan(retry_only=True)
            self.assertEqual(send.call_count, 1)
