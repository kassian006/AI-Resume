from celery import Celery
from my_site.config import REDIS_URL

celery_app = Celery(
    "resume_app",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

import my_site.workers.tasks