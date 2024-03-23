from celery import Celery
from .utils import send_verification_email

redis_host = '51.20.142.197'
redis_port = 6379

# Celery configuration

worker_concurrency = 4
worker_prefetch_multiplier = 1
worker_max_tasks_per_child = 1000
task_acks_late = True
task_default_retry_delay = 30
task_max_retries = 3
task_time_limit = 600
result_expires = 3600
worker_pool_restarts = True

# Initialize Celery application
celery = Celery(
    'tasks',
    broker=f'redis://{redis_host}:{redis_port}/0',
    backend=f'redis://{redis_host}:{redis_port}/0',
    worker_concurrency=worker_concurrency,
    worker_prefetch_multiplier=worker_prefetch_multiplier,
    worker_max_tasks_per_child=worker_max_tasks_per_child,
    task_acks_late=task_acks_late,
    task_default_retry_delay=task_default_retry_delay,
    task_max_retries=task_max_retries,
    task_time_limit=task_time_limit,
    result_expires=result_expires,
    worker_pool_restarts=worker_pool_restarts
)

@celery.task
def send_verification_email_task(email, verification_token):
    send_verification_email(email, verification_token)