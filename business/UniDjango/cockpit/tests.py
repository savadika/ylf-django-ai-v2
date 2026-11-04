"""SPEC-018 AC-002/AC-004: authenticated cockpit snapshot delivery."""

from pathlib import Path
import tempfile
from unittest import mock

from core_test_support import CoreApiTestCase, api_data, create_test_user
from django.test import TestCase
from menu.models import SysMenu
from rest_framework.test import APIClient


class CockpitSnapshotApiTests(CoreApiTestCase):
    def test_snapshot_requires_authentication_ac_002(self):
        response = APIClient().get('/cockpit/snapshot', secure=True)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['code'], 401)

    def test_snapshot_requires_dashboard_permission_ac_002(self):
        user = create_test_user('cockpit-no-access', permissions=())
        client = self.get_auth_client(user)

        response = client.get('/cockpit/snapshot', secure=True)

        self.assertEqual(response.status_code, 403)

    def test_snapshot_returns_generated_html_for_dashboard_user_ac_002(self):
        with tempfile.TemporaryDirectory() as temporary:
            snapshot = Path(temporary) / 'snapshot.html'
            snapshot.write_text(
                '<!doctype html><body class="embedded">驾驶舱</body>',
                encoding='utf-8',
            )
            with mock.patch('cockpit.views.SNAPSHOT_PATH', snapshot):
                response = self.client.get('/cockpit/snapshot', secure=True)

        data = api_data(response)
        self.assertIn('驾驶舱', data['html'])
        self.assertIsInstance(data['generated_at'], int)
        self.assertEqual(response['Cache-Control'], 'private, no-store')

    def test_missing_snapshot_returns_not_found_ac_002(self):
        missing = Path('/tmp/ylf-cockpit-snapshot-does-not-exist.html')
        with mock.patch('cockpit.views.SNAPSHOT_PATH', missing):
            response = self.client.get('/cockpit/snapshot', secure=True)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()['message'], '驾驶舱快照尚未生成')


class CockpitMenuTests(TestCase):
    def test_default_dashboard_menu_is_named_cockpit_ac_004(self):
        menu = SysMenu.objects.get(perms='system:dashboard:view')

        self.assertEqual(menu.name, '驾驶舱')
        self.assertEqual(menu.path, '/dashboard')
        self.assertEqual(menu.component, 'dashboard/index')
        self.assertEqual(menu.order_num, 0)
