import unittest
from datetime import date

from sqlalchemy.orm import Session
from app.billing import add_cycle, compute_next_renewal
from app.models import Subscription
from tests import test_sync


class BillingAnchorTests(unittest.TestCase):
    setUpClass = classmethod(test_sync.SyncTests.setUpClass.__func__)
    make_engine = test_sync.SyncTests.make_engine
    setUp = test_sync.SyncTests.setUp
    tearDown = test_sync.SyncTests.tearDown
    changes = test_sync.SyncTests.changes
    push = test_sync.SyncTests.push
    def create_month_end(self, day="2027-01-31", cycle="month"):
        r = self.client.post('/api/subscriptions', headers=self.headers, json={
            'name': '月末', 'start_date': day, 'next_renewal_date': day, 'cycle': cycle})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def renew(self, sub):
        r = self.client.post(f"/api/subscriptions/{sub['id']}/renew", headers=self.headers, json={'mode': 'due'})
        self.assertEqual(r.status_code, 200, r.text)
        return r.json()

    def test_month_end_and_leap_year(self):
        for start, feb in [('2027-01-31', '2027-02-28'), ('2028-01-31', '2028-02-29')]:
            s = self.renew(self.create_month_end(start))
            self.assertEqual(s['next_renewal_date'], feb)
            self.assertEqual(self.renew(s)['next_renewal_date'], start[:4] + '-03-31')
        s = self.create_month_end('2028-02-29', 'year')
        for expected in ['2029-02-28', '2030-02-28', '2031-02-28', '2032-02-29']:
            s = self.renew(s)
            self.assertEqual(s['next_renewal_date'], expected)

    def test_edit_full_form_preserves_anchor_unless_date_changes(self):
        s = self.renew(self.create_month_end())
        for body, expected in [({'remark': '备注', 'next_renewal_date': s['next_renewal_date'], 'billing_anchor_day': 28}, 31),
                               ({'next_renewal_date': '2027-02-25'}, 25), ({'cycle': 'week'}, None)]:
            r = self.client.put(f"/api/subscriptions/{s['id']}", headers=self.headers, json=body)
            self.assertEqual(r.status_code, 200, r.text)
            self.assertEqual(r.json()['billing_anchor_day'], expected)

    def test_legacy_null_keeps_legacy_behavior(self):
        s = self.create_month_end()
        with Session(self.engine) as db:
            db.get(Subscription, s['id']).billing_anchor_day = None
            db.commit()
        self.assertEqual(self.renew(self.renew(s))['next_renewal_date'], '2027-03-28')

    def test_old_sync_client_does_not_clear_anchor(self):
        s = self.renew(self.create_month_end())
        record = [c for c in self.changes()['changes'] if c['kind'] == 'subscriptions'][-1]
        data = dict(record['data']); data.pop('billing_anchor_day', None); data['remark'] = '旧客户端'
        r = self.push([{'op_id': 'old-anchor', 'kind': 'subscriptions', 'id': record['id'], 'base_version': record['version'], 'data': data}])
        self.assertEqual(r.json()['results'][0]['status'], 'applied', r.text)
        self.assertEqual(self.renew(s)['next_renewal_date'], '2027-03-31')

    def test_compute_repeated_cycles(self):
        self.assertEqual(compute_next_renewal(date(2027, 1, 31), 'month', 1, date(2027, 3, 1), anchor_day=31), date(2027, 3, 31))
        self.assertEqual(add_cycle(date(2027, 2, 28), 'day', 1, 31), date(2027, 3, 1))

    def test_today_resets_anchor_and_invalid_anchor_is_rejected(self):
        s = self.create_month_end()
        r = self.client.post(f"/api/subscriptions/{s['id']}/renew", headers=self.headers, json={'mode': 'today'})
        self.assertEqual(r.json()['billing_anchor_day'], date.today().day)
        r = self.client.post('/api/subscriptions', headers=self.headers, json={'name': '无效', 'billing_anchor_day': 32})
        self.assertEqual(r.status_code, 422)

    def test_csv_preserves_explicit_anchor(self):
        r = self.client.post('/api/subscriptions/import-csv', headers=self.headers, json={'content': 'name,start_date,next_renewal_date,billing_anchor_day\n月末,2027-01-31,2027-02-28,31'})
        self.assertEqual(r.status_code, 200, r.text)
        s = self.client.get('/api/subscriptions', headers=self.headers).json()[0]
        self.assertEqual(self.renew(s)['next_renewal_date'], '2027-03-31')

    def test_backup_roundtrip_preserves_anchor_and_legacy_null(self):
        first = self.renew(self.create_month_end())
        second = self.create_month_end()
        with Session(self.engine) as db:
            db.get(Subscription, second['id']).billing_anchor_day = None
            db.commit()
        backup = self.client.get('/api/backup/export', headers=self.headers).json()
        self.assertEqual({s['billing_anchor_day'] for s in backup['subscriptions']}, {31, None})
        r = self.client.post('/api/backup/import', headers=self.headers, json={'data': backup, 'replace': True})
        self.assertEqual(r.status_code, 200, r.text)
        restored = self.client.get('/api/subscriptions', headers=self.headers).json()
        self.assertEqual({s['billing_anchor_day'] for s in restored}, {31, None})
        anchored = next(s for s in restored if s['billing_anchor_day'] == 31)
        self.assertEqual(self.renew(anchored)['next_renewal_date'], '2027-03-31')
