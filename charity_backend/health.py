"""
Health check views for system monitoring
"""

import logging
import time

from django.conf import settings
from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """
    Comprehensive health check endpoint
    Returns status of various system components
    """
    health_status = {"status": "healthy", "timestamp": time.time(), "checks": {}}

    # Database check
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status["checks"]["database"] = {
                "status": "healthy",
                "response_time_ms": 0,
            }
    except Exception as e:
        health_status["checks"]["database"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"

    # Cache check (Redis)
    try:
        start_time = time.time()
        cache.set("health_check", "test", 60)
        cache.get("health_check")
        response_time = (time.time() - start_time) * 1000

        health_status["checks"]["cache"] = {
            "status": "healthy",
            "response_time_ms": round(response_time, 2),
        }
    except Exception as e:
        health_status["checks"]["cache"] = {"status": "unhealthy", "error": str(e)}
        health_status["status"] = "unhealthy"

    # System info
    health_status["system"] = {
        "debug": settings.DEBUG,
        "version": "1.0.0",
        "environment": "development" if settings.DEBUG else "production",
    }

    # Return appropriate HTTP status
    status_code = 200 if health_status["status"] == "healthy" else 503

    return JsonResponse(health_status, status=status_code)


@csrf_exempt
@require_http_methods(["GET"])
def readiness_check(request):
    """
    Readiness check for Kubernetes/container orchestration
    """
    return JsonResponse(
        {"status": "ready", "message": "Service is ready to accept requests"}
    )


@csrf_exempt
@require_http_methods(["GET"])
def liveness_check(request):
    """
    Liveness check for Kubernetes/container orchestration
    """
    return JsonResponse({"status": "alive", "message": "Service is running"})
