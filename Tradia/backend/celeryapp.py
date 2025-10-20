# from celery import Celery
# from config.settings import settings

# # This is a lightweight client; it doesn’t define or run any tasks

# celery_app = Celery(
#     broker=settings.redis_url+'/0',
#     backend=settings.redis_url+'/1',
# )

from celery import Celery
celery_app = Celery(broker='redis://redis:6379/0', backend='redis://redis:6379/1')