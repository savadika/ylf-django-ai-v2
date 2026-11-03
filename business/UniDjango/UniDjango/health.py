"""Deployment health checks for the database, cache and HTTP stack."""

import logging
import uuid

from django.core.cache import cache
from django.db import connection
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from utils.response import ApiResponse, Ok


logger = logging.getLogger(__name__)


class HealthCheckView(APIView):
    """Return success only when database and cache dependencies are usable."""

    authentication_classes = []
    permission_classes = [AllowAny]

    def get(self, request):
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

            cache_key = f"healthz:{uuid.uuid4().hex}"
            cache.set(cache_key, "ok", timeout=5)
            cache_ok = cache.get(cache_key) == "ok"
            cache.delete(cache_key)
            if not cache_ok:
                raise RuntimeError("cache read/write check failed")
        except Exception:
            logger.exception("健康检查失败")
            return ApiResponse(
                code=503,
                message="服务暂不可用",
                data={"status": "unavailable"},
            )

        return Ok(data={"status": "ok"})
