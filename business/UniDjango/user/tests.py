"""SPEC-006/SPEC-011：JWT、登录、个人资料与用户管理 API。"""
import json
from datetime import datetime, timedelta
import jwt
from unittest import mock

from core_test_support import (
    CORE_TEST_PASSWORD,
    CoreApiTestCase,
    api_data,
    authenticated_api_client,
    create_test_user,
)
from django.contrib.auth.hashers import make_password
from django.conf import settings
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase, override_settings
from django.utils import timezone
from django.core.management import call_command
from rest_framework.serializers import ValidationError
from rest_framework.test import APIClient
from io import StringIO

from department.models import SysDep
from menu.models import SysMenu, SysRoleMenu
from role.models import SysRole, SysUserRole
from user.jwt_auth import (
    JWT_ALGORITHM,
    decode_token,
    encode_token,
    get_token_from_request,
    is_token_revoked,
    revoke_token,
)
from user.models import SysUser
from user.views import LOGIN_MAX_FAILURES, SysUserSerializer
from utils.exceptions import CacheUnavailable
from utils.filters import create_complex_filter_class


# 测试期间用本地内存缓存，避免依赖外部 Redis。
LOCMEM_CACHE = {
    'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache'},
}


@override_settings(CACHES=LOCMEM_CACHE)
class JwtAuthTests(SimpleTestCase):
    def test_encode_decode_roundtrip(self):
        user = SysUser(id=7, username='u', token_version=3)
        token = encode_token(user)
        payload = decode_token(token)
        self.assertEqual(payload['user_id'], 7)
        self.assertEqual(payload['ver'], 3)

    def test_token_expiration_defaults_to_at_most_eight_hours(self):
        token = encode_token(SysUser(id=7, username='u'))
        payload = decode_token(token)

        self.assertLessEqual(
            payload['exp'] - payload['iat'],
            timedelta(hours=8).total_seconds(),
        )

    @override_settings(JWT_EXPIRATION_SECONDS=60)
    def test_token_expiration_is_configurable(self):
        token = encode_token(SysUser(id=7, username='u'))
        payload = decode_token(token)

        self.assertLessEqual(payload['exp'] - payload['iat'], 60)

    def test_revoke_marks_token_revoked(self):
        user = SysUser(id=8, username='u')
        token = encode_token(user)
        self.assertFalse(is_token_revoked(decode_token(token)))
        revoke_token(token)
        self.assertTrue(is_token_revoked(decode_token(token)))

    def test_revoke_ignores_invalid_expired_and_anonymous_payloads(self):
        expired = jwt.encode(
            {'user_id': 9, 'exp': timezone.now().timestamp() - 1},
            settings.JWT_SECRET_KEY,
            algorithm=JWT_ALGORITHM,
        )

        with mock.patch('user.jwt_auth.cache.set') as cache_set:
            revoke_token('invalid-token')
            revoke_token(expired)
            revoke_token(
                jwt.encode(
                    {'user_id': 9, 'jti': 'without-exp'},
                    settings.JWT_SECRET_KEY,
                    algorithm=JWT_ALGORITHM,
                )
            )

        self.assertEqual(cache_set.call_count, 1)
        self.assertFalse(is_token_revoked({'user_id': 9}))

    def test_revoke_ignores_payload_without_jti(self):
        token = jwt.encode(
            {'user_id': 9, 'exp': timezone.now().timestamp() + 60},
            settings.JWT_SECRET_KEY,
            algorithm=JWT_ALGORITHM,
        )

        with mock.patch('user.jwt_auth.cache.set') as cache_set:
            revoke_token(token)

        cache_set.assert_not_called()

    def test_revoke_cache_failure_is_fail_closed(self):
        token = encode_token(SysUser(id=10, username='cache-user'))

        with self.assertLogs('user.jwt_auth', level='ERROR'):
            with mock.patch(
                'user.jwt_auth.cache.set',
                side_effect=RuntimeError('cache down'),
            ):
                with self.assertRaises(CacheUnavailable):
                    revoke_token(token)

    def test_extract_token_supports_bearer_and_raw_headers(self):
        from django.test import RequestFactory

        bearer = RequestFactory().get(
            '/',
            HTTP_AUTHORIZATION='Bearer   token-value  ',
        )
        raw = RequestFactory().get(
            '/',
            HTTP_AUTHORIZATION=' raw-token ',
        )
        missing = RequestFactory().get('/')

        self.assertEqual(get_token_from_request(bearer), 'token-value')
        self.assertEqual(get_token_from_request(raw), 'raw-token')
        self.assertIsNone(get_token_from_request(missing))


class SysUserModelTests(SimpleTestCase):
    def test_authentication_properties_follow_status(self):
        user = SysUser(username='model-user', status=1)

        self.assertTrue(user.is_authenticated)
        self.assertFalse(user.is_anonymous)
        self.assertTrue(user.is_active)

        user.status = 0

        self.assertFalse(user.is_active)


class PasswordValidationTests(TestCase):
    def test_weak_password_rejected(self):
        data = {'username': 'weakuser', 'password': '123', 'email': 'weak@example.com'}
        serializer = SysUserSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        with self.assertRaises(ValidationError):
            serializer.save()

    def test_empty_email_normalized_to_none(self):
        data = {'username': 'emailuser', 'password': 'StrongPass123', 'email': ''}
        serializer = SysUserSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        self.assertIsNone(serializer.validated_data['email'])

    def test_valid_password_creates_user(self):
        data = {'username': 'okuser', 'password': 'StrongPass123', 'email': 'ok@example.com'}
        serializer = SysUserSerializer(data=data)
        self.assertTrue(serializer.is_valid(), serializer.errors)
        user = serializer.save()
        self.assertTrue(SysUser.objects.filter(id=user.id).exists())


@override_settings(CACHES=LOCMEM_CACHE)
class LoginLockoutTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # 屏蔽请求日志的后台写库，避免异步线程干扰测试事务。
        cls._log_patch = mock.patch('log.middleware.submit_log')
        cls._log_patch.start()

    @classmethod
    def tearDownClass(cls):
        cls._log_patch.stop()
        super().tearDownClass()

    def setUp(self):
        # 清空 locmem 缓存，避免上个用例的登录锁定状态串扰到本用例。
        cache.clear()
        SysUser.objects.create(
            username='locktest',
            password=make_password('right-password'),
            email='locktest@example.com',
            status=1,
        )
        self.client = APIClient()
    def test_valid_login_returns_token_and_updates_login_date(self):
        url = '/user/gen_token'
        body = json.dumps({'username': 'locktest', 'password': 'right-password'})

        resp = self.client.post(
            url, data=body, content_type='application/json', secure=True,
        )

        self.assertEqual(resp.status_code, 200)
        self.assertIn('token', resp.json()['data'])
        user = SysUser.objects.get(username='locktest')
        self.assertIsNotNone(user.login_date)

    def test_locks_after_max_failures(self):
        url = '/user/gen_token'
        body = json.dumps({'username': 'locktest', 'password': 'wrong'})
        for _ in range(LOGIN_MAX_FAILURES):
            resp = self.client.post(
                url, data=body, content_type='application/json', secure=True,
            )
            self.assertEqual(resp.status_code, 401)
        resp = self.client.post(
            url, data=body, content_type='application/json', secure=True,
        )
        self.assertEqual(resp.status_code, 429)

    def test_success_clears_failures(self):
        url = '/user/gen_token'
        wrong = json.dumps({'username': 'locktest', 'password': 'wrong'})
        right = json.dumps({'username': 'locktest', 'password': 'right-password'})
        for _ in range(LOGIN_MAX_FAILURES - 1):
            self.client.post(
                url, data=wrong, content_type='application/json', secure=True,
            )
        resp = self.client.post(
            url, data=right, content_type='application/json', secure=True,
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn('token', resp.json()['data'])

    def test_disabled_user_uses_generic_login_error(self):
        SysUser.objects.filter(username='locktest').update(status=0)
        url = '/user/gen_token'
        body = json.dumps({'username': 'locktest', 'password': 'right-password'})

        resp = self.client.post(
            url, data=body, content_type='application/json', secure=True,
        )

        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.json()['message'], '用户不存在或密码错误')

    def test_unknown_user_uses_generic_login_error(self):
        response = self.client.post(
            '/user/gen_token',
            {'username': 'unknown-user', 'password': 'wrong'},
            format='json',
            secure=True,
        )

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['message'], '用户不存在或密码错误')

    def test_login_failure_cache_write_error_returns_503(self):
        with self.assertLogs('user.views', level='ERROR'):
            with (
                mock.patch('user.views.cache.get', return_value=0),
                mock.patch(
                    'user.views.cache.set',
                    side_effect=RuntimeError('cache down'),
                ),
            ):
                response = self.client.post(
                    '/user/gen_token',
                    {'username': 'unknown-cache-user', 'password': 'wrong'},
                    format='json',
                    secure=True,
                )

        self.assertEqual(response.status_code, 503)

    def test_wrong_password_cache_write_error_returns_503(self):
        with self.assertLogs('user.views', level='ERROR'):
            with (
                mock.patch('user.views.cache.get', return_value=0),
                mock.patch(
                    'user.views.cache.set',
                    side_effect=RuntimeError('cache down'),
                ),
            ):
                response = self.client.post(
                    '/user/gen_token',
                    {'username': 'locktest', 'password': 'wrong'},
                    format='json',
                    secure=True,
                )

        self.assertEqual(response.status_code, 503)

    def test_login_clear_cache_error_does_not_block_valid_login(self):
        with self.assertLogs('user.views', level='WARNING'):
            with mock.patch(
                'user.views.cache.delete',
                side_effect=RuntimeError('cache down'),
            ):
                response = self.client.post(
                    '/user/gen_token',
                    {'username': 'locktest', 'password': 'right-password'},
                    format='json',
                    secure=True,
                )

        self.assertEqual(response.status_code, 200)
        self.assertIn('token', response.json()['data'])


class JwtMiddlewareTests(TestCase):
    @mock.patch('log.middleware.submit_log')
    def test_missing_token_returns_401(self, _mock_log):
        resp = APIClient().get('/user/get_user_info', secure=True)
        self.assertEqual(resp.status_code, 401)

    @mock.patch('log.middleware.submit_log')
    def test_token_version_mismatch_returns_401(self, _mock_log):
        user = create_test_user('stale-token-user')
        client = authenticated_api_client(user)
        SysUser.objects.filter(pk=user.pk).update(token_version=1)

        response = client.get('/user/get_user_info', secure=True)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['message'], 'token已失效')

    @mock.patch('log.middleware.submit_log')
    def test_healthcheck_is_public_and_checks_dependencies(self, _mock_log):
        response = APIClient().get('/healthz/', secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['data']['status'], 'ok')


class HealthCheckTests(TestCase):
    @mock.patch('log.middleware.submit_log')
    def test_healthcheck_cache_failure_returns_503(self, _mock_log):
        with self.assertLogs('UniDjango.health', level='ERROR'):
            with mock.patch(
                'UniDjango.health.cache.get',
                side_effect=RuntimeError('cache down'),
            ):
                response = APIClient().get('/healthz/', secure=True)

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['data']['status'], 'unavailable')


class SysUserFilterTests(SimpleTestCase):
    def test_password_not_exposed_as_filter(self):
        filter_cls = create_complex_filter_class(SysUser, search_fields=['username'])
        self.assertNotIn('password', filter_cls.base_filters)
        self.assertIn('username', filter_cls.base_filters)


class SysUserDateTimeFilterTests(TestCase):
    def test_datetime_end_filter_includes_whole_day(self):
        user1 = SysUser.objects.create(
            username='eod-user-1',
            password='x',
            email='eod-user-1@example.com',
            status=1,
        )
        user2 = SysUser.objects.create(
            username='eod-user-2',
            password='x',
            email='eod-user-2@example.com',
            status=1,
        )

        SysUser.objects.filter(pk=user1.pk).update(
            create_time=timezone.make_aware(datetime(2026, 8, 18, 23, 30))
        )
        SysUser.objects.filter(pk=user2.pk).update(
            create_time=timezone.make_aware(datetime(2026, 8, 19, 0, 30))
        )

        filter_cls = create_complex_filter_class(SysUser, search_fields=['username'])
        filtered = filter_cls(
            {'create_time_start': '2026-08-18', 'create_time_end': '2026-08-18'},
            queryset=SysUser.objects.all(),
        ).qs

        self.assertEqual(
            set(filtered.values_list('username', flat=True)),
            {'eod-user-1'},
        )


class InitAdminSeedTests(TestCase):
    def test_init_admin_seeds_default_menu_tree(self):
        call_command(
            'init_admin',
            username='seed_admin',
            password='StrongPass123',
            email='seed_admin@example.com',
            stdout=StringIO(),
        )

        self.assertTrue(SysMenu.objects.filter(name='用户管理', menu_type='C').exists())
        self.assertTrue(SysMenu.objects.filter(name='用户列表', perms='system:user:list').exists())
        role = SysRole.objects.get(code='admin')
        self.assertTrue(SysRoleMenu.objects.filter(role=role, menu__name='用户管理').exists())

    def test_init_admin_is_idempotent_and_binds_test_admin_permissions(self):
        command_args = {
            'username': 'seed_admin',
            'password': 'StrongPass123',
            'email': 'seed_admin@example.com',
            'stdout': StringIO(),
        }

        call_command('init_admin', **command_args)
        call_command('init_admin', **command_args)

        self.assertEqual(SysUser.objects.filter(username='seed_admin').count(), 1)
        self.assertEqual(SysRole.objects.filter(code='admin').count(), 1)
        self.assertEqual(SysDep.objects.filter(dep_name='总部').count(), 1)
        admin = SysUser.objects.get(username='seed_admin')
        role = SysRole.objects.get(code='admin')
        self.assertTrue(admin.is_active)
        self.assertTrue(admin.check_password('StrongPass123'))
        self.assertTrue(SysUserRole.objects.filter(user=admin, role=role).exists())
        self.assertTrue(
            SysRoleMenu.objects.filter(
                role=role,
                menu__perms='*:*:*',
            ).exists()
        )


class UserAuthenticationApiTests(CoreApiTestCase):
    def test_login_rejects_malformed_json(self):
        response = APIClient().post(
            "/user/gen_token",
            data="{",
            content_type="application/json",
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "请求体必须是合法 JSON")

    def test_login_rejects_missing_credentials(self):
        response = APIClient().post(
            "/user/gen_token",
            {"username": "missing-password"},
            format="json",
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["message"], "用户名或密码不能为空")

    def test_user_info_returns_profile_menus_and_permissions(self):
        data = api_data(
            self.client.get("/user/get_user_info", secure=True)
        )

        self.assertEqual(data["id"], self.admin_user.id)
        self.assertEqual(data["username"], self.admin_user.username)
        self.assertTrue(data["avatar"].startswith("https://testserver/media/"))
        self.assertIn("*:*:*", data["permissions"])
        self.assertEqual(data["menus"][0]["name"], "Permission *:*:*")

    def test_logout_revokes_current_token(self):
        user = create_test_user(
            "logout-user",
            permissions=("system:user:list",),
        )
        client = self.get_auth_client(user)

        logout_response = client.post("/user/logout", secure=True)
        info_response = client.get("/user/get_user_info", secure=True)

        self.assertEqual(logout_response.status_code, 200)
        self.assertEqual(info_response.status_code, 401)
        self.assertEqual(info_response.json()["message"], "token已失效")

    def test_invalid_token_is_rejected(self):
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token")

        response = client.get("/user/get_user_info", secure=True)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["message"], "无效的token")

    def test_expired_token_is_rejected(self):
        token = jwt.encode(
            {"user_id": self.admin_user.id, "exp": timezone.now().timestamp() - 1},
            settings.JWT_SECRET_KEY,
            algorithm=JWT_ALGORITHM,
        )
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")

        response = client.get("/user/get_user_info", secure=True)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["message"], "token已过期")

    def test_token_for_missing_user_is_rejected(self):
        missing_user = SysUser(id=999999, username="missing")
        client = self.get_auth_client(missing_user)

        response = client.get("/user/get_user_info", secure=True)

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["message"], "用户不存在")

    def test_disabled_user_token_is_rejected(self):
        user = create_test_user("disabled-api-user", active=False)
        client = self.get_auth_client(user)

        response = client.get("/user/get_user_info", secure=True)

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["message"], "用户已被禁用")

    def test_authentication_cache_failure_returns_503(self):
        with self.assertLogs('user.jwt_auth', level='ERROR'):
            with mock.patch(
                "user.jwt_auth.cache.get",
                side_effect=RuntimeError("cache down"),
            ):
                response = self.client.get(
                    "/user/get_user_info",
                    secure=True,
                )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["message"], "认证服务暂不可用")

    def test_login_cache_read_failure_returns_503(self):
        with self.assertLogs('user.views', level='ERROR'):
            with mock.patch(
                "user.views.cache.get",
                side_effect=RuntimeError("cache down"),
            ):
                response = APIClient().post(
                    "/user/gen_token",
                    {"username": "cache-user", "password": "password"},
                    format="json",
                    secure=True,
                )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()["message"], "认证服务暂不可用")

    def test_logout_cache_failure_returns_503(self):
        with self.assertLogs('user.jwt_auth', level='ERROR'):
            with mock.patch(
                'user.jwt_auth.cache.set',
                side_effect=RuntimeError('cache down'),
            ):
                response = self.client.post(
                    '/user/logout',
                    secure=True,
                )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['message'], '注销服务暂不可用')


class UserProfileApiTests(CoreApiTestCase):
    def test_user_without_edit_permission_updates_own_avatar(self):
        user = create_test_user('profile-avatar-user')
        client = self.get_auth_client(user)

        response = client.patch(
            '/user/profile',
            {'avatar': 'uploads/profile/avatar.png'},
            format='json',
            secure=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json()['data']['avatar'],
            'uploads/profile/avatar.png',
        )
        self.assertFalse(response.json()['data']['reauth_required'])
        user.refresh_from_db()
        self.assertEqual(user.avatar, 'uploads/profile/avatar.png')

    def test_password_change_revokes_old_token_and_new_login_works(self):
        user = create_test_user('profile-password-user')
        old_client = self.get_auth_client(user)

        response = old_client.patch(
            '/user/profile',
            {'password': 'ProfileNewPass456!'},
            format='json',
            secure=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['data']['reauth_required'])
        user.refresh_from_db()
        self.assertTrue(user.check_password('ProfileNewPass456!'))
        self.assertEqual(user.token_version, 1)
        self.assertEqual(
            old_client.get('/user/get_user_info', secure=True).status_code,
            401,
        )

        login = APIClient().post(
            '/user/gen_token',
            {
                'username': user.username,
                'password': 'ProfileNewPass456!',
            },
            format='json',
            secure=True,
        )
        self.assertEqual(login.status_code, 200)
        new_client = APIClient()
        new_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {login.json()['data']['token']}"
        )
        self.assertEqual(
            new_client.get('/user/get_user_info', secure=True).status_code,
            200,
        )

    def test_profile_rejects_weak_password_without_revoking_token(self):
        user = create_test_user('profile-weak-password-user')
        client = self.get_auth_client(user)

        response = client.patch(
            '/user/profile',
            {'password': '123'},
            format='json',
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            client.get('/user/get_user_info', secure=True).status_code,
            200,
        )

    def test_profile_ignores_another_user_id_and_updates_only_self(self):
        user = create_test_user('profile-self-only-user')
        client = self.get_auth_client(user)

        response = client.patch(
            '/user/profile',
            {
                'id': self.admin_user.id,
                'avatar': 'uploads/profile/self.png',
            },
            format='json',
            secure=True,
        )

        self.assertEqual(response.status_code, 200)
        user.refresh_from_db()
        self.admin_user.refresh_from_db()
        self.assertEqual(user.avatar, 'uploads/profile/self.png')
        self.assertNotEqual(
            self.admin_user.avatar,
            'uploads/profile/self.png',
        )


class UserCrudApiTests(CoreApiTestCase):
    def setUp(self):
        super().setUp()
        self.department = SysDep.objects.create(
            dep_name="测试用户部门",
            status=1,
        )
        self.role_a = SysRole.objects.create(
            name="测试用户角色A",
            code="test-user-role-a",
        )
        self.role_b = SysRole.objects.create(
            name="测试用户角色B",
            code="test-user-role-b",
        )

    def test_anonymous_cannot_list_users(self):
        response = APIClient().get("/user", secure=True)

        self.assertEqual(response.status_code, 401)

    def test_user_without_permission_is_forbidden(self):
        viewer = create_test_user(
            "user-viewer",
            permissions=("system:role:list",),
        )

        response = self.get_auth_client(viewer).get("/user", secure=True)

        self.assertEqual(response.status_code, 403)

    def test_list_is_paginated_searches_and_never_exposes_passwords(self):
        for index in range(12):
            SysUser.objects.create(
                username=f"search-user-{index:02d}",
                password=make_password("Password123!"),
                email=f"search-user-{index:02d}@example.com",
                status=1,
            )

        data = api_data(
            self.client.get(
                "/user",
                {"search": "search-user", "page": 1, "page_size": 5},
                secure=True,
            )
        )

        self.assertEqual(data["count"], 12)
        self.assertEqual(len(data["results"]), 5)
        self.assertTrue(
            all(row["username"].startswith("search-user-") for row in data["results"])
        )
        self.assertTrue(all("password" not in row for row in data["results"]))

    def test_create_user_with_department_and_roles_is_retrievable(self):
        created = api_data(
            self.client.post(
                "/user",
                {
                    "department": self.department.id,
                    "username": "created-api-user",
                    "password": CORE_TEST_PASSWORD,
                    "email": "created-api-user@example.com",
                    "phone": "13800138000",
                    "roles": [self.role_a.id, self.role_b.id],
                },
                format="json",
                secure=True,
            )
        )
        detail = api_data(
            self.client.get(f"/user/{created['id']}", secure=True)
        )

        self.assertEqual(detail["username"], "created-api-user")
        self.assertEqual(detail["department"], self.department.id)
        self.assertEqual(set(detail["roles"]), {self.role_a.id, self.role_b.id})
        self.assertNotIn("password", detail)

    def test_create_user_requires_password(self):
        response = self.client.post(
            "/user",
            {
                "username": "missing-api-password",
                "email": "missing-api-password@example.com",
            },
            format="json",
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("密码不能为空", response.json()["message"])

    def test_create_user_rejects_weak_password(self):
        response = self.client.post(
            "/user",
            {
                "username": "weak-api-user",
                "password": "123",
                "email": "weak-api-user@example.com",
            },
            format="json",
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("password", response.json()["message"])

    def test_create_user_rejects_unknown_role(self):
        response = self.client.post(
            "/user",
            {
                "username": "bad-role-api-user",
                "password": CORE_TEST_PASSWORD,
                "email": "bad-role-api-user@example.com",
                "roles": [999999],
            },
            format="json",
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("角色不存在", response.json()["message"])
        self.assertFalse(
            SysUser.objects.filter(username="bad-role-api-user").exists()
        )

    def test_create_user_rejects_duplicate_email(self):
        SysUser.objects.create(
            username="existing-email-user",
            password=make_password(CORE_TEST_PASSWORD),
            email="duplicate@example.com",
            status=1,
        )

        response = self.client.post(
            "/user",
            {
                "username": "new-email-user",
                "password": CORE_TEST_PASSWORD,
                "email": "duplicate@example.com",
            },
            format="json",
            secure=True,
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("email", response.json()["message"])

    def test_patch_updates_password_and_replaces_roles(self):
        user = SysUser.objects.create(
            department=self.department,
            username="patch-api-user",
            password=make_password(CORE_TEST_PASSWORD),
            email="patch-api-user@example.com",
            status=1,
        )
        SysUserRole.objects.create(user=user, role=self.role_a)

        data = api_data(
            self.client.patch(
                f"/user/{user.id}",
                {
                    "email": "patch-api-user-new@example.com",
                    "password": "NewStrongPass456!",
                    "roles": [self.role_b.id],
                },
                format="json",
                secure=True,
            )
        )
        user.refresh_from_db()

        self.assertEqual(data["email"], "patch-api-user-new@example.com")
        self.assertEqual(data["roles"], [self.role_b.id])
        self.assertTrue(user.check_password("NewStrongPass456!"))
        self.assertFalse(user.check_password(CORE_TEST_PASSWORD))
        self.assertGreater(user.token_version, 0)
        self.assertEqual(
            list(
                SysUserRole.objects.filter(user=user).values_list(
                    "role_id", flat=True
                )
            ),
            [self.role_b.id],
        )

    def test_patch_without_roles_preserves_existing_roles(self):
        user = SysUser.objects.create(
            username="preserve-role-api-user",
            password=make_password(CORE_TEST_PASSWORD),
            email="preserve-role-api-user@example.com",
            status=1,
        )
        SysUserRole.objects.create(user=user, role=self.role_a)

        data = api_data(
            self.client.patch(
                f"/user/{user.id}",
                {"phone": "13700137000"},
                format="json",
                secure=True,
            )
        )

        self.assertEqual(data["phone"], "13700137000")
        self.assertEqual(data["roles"], [self.role_a.id])

    def test_put_updates_user_profile_and_preserves_password(self):
        user = SysUser.objects.create(
            username="put-api-user",
            password=make_password(CORE_TEST_PASSWORD),
            email="put-api-user@example.com",
            status=1,
        )

        data = api_data(
            self.client.put(
                f"/user/{user.id}",
                {
                    "department": self.department.id,
                    "username": "put-api-user-renamed",
                    "email": "put-api-user-renamed@example.com",
                    "phone": "13900139000",
                    "status": 0,
                    "roles": [self.role_a.id],
                },
                format="json",
                secure=True,
            )
        )
        user.refresh_from_db()

        self.assertEqual(data["username"], "put-api-user-renamed")
        self.assertEqual(data["status"], 0)
        self.assertEqual(data["roles"], [self.role_a.id])
        self.assertTrue(user.check_password(CORE_TEST_PASSWORD))

    def test_delete_user_cleans_role_links(self):
        user = SysUser.objects.create(
            username="delete-api-user",
            password=make_password(CORE_TEST_PASSWORD),
            email="delete-api-user@example.com",
            status=1,
        )
        SysUserRole.objects.create(user=user, role=self.role_a)

        response = self.client.delete(f"/user/{user.id}", secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(SysUser.objects.filter(id=user.id).exists())
        self.assertFalse(SysUserRole.objects.filter(user_id=user.id).exists())
        self.assertTrue(SysRole.objects.filter(id=self.role_a.id).exists())

    def test_missing_user_returns_404(self):
        response = self.client.get("/user/999999", secure=True)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.json()["code"], 404)

    def test_advanced_search_and_filter_options_are_available(self):
        SysUser.objects.create(
            username="advanced-api-user",
            password=make_password(CORE_TEST_PASSWORD),
            email="advanced-api-user@example.com",
            status=0,
        )

        data = api_data(
            self.client.get(
                "/user/advanced-search",
                {"status": 0, "search": "advanced-api-user"},
                secure=True,
            )
        )
        options = api_data(
            self.client.get("/user/filter-options", secure=True)
        )

        self.assertEqual(data["count"], 1)
        self.assertEqual(data["results"][0]["username"], "advanced-api-user")
        self.assertEqual(
            {item["value"] for item in options["status_options"]},
            {0, 1},
        )
