# Celery Configuration for Charity Nepal Backend

import os

from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "charity_backend.settings")

app = Celery("charity_backend")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Celery beat scheduler for periodic tasks
app.conf.beat_schedule = {
    "send-periodic-updates": {
        "task": "cases.tasks.send_periodic_updates",
        "schedule": 60.0 * 60 * 24,  # Every 24 hours
    },
    "update-recommendation-models": {
        "task": "recommendations.tasks.retrain_models",
        "schedule": 60.0 * 60 * 24 * 7,  # Every week
    },
    "cleanup-expired-payments": {
        "task": "payments.tasks.cleanup_expired_payments",
        "schedule": 60.0 * 60,  # Every hour
    },
}

app.conf.timezone = "Asia/Kathmandu"


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
