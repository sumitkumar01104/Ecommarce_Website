import os

from celery import Celery


# Tell Celery which Django settings module to use
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'ecommarce.settings'
)


# Create Celery application
app = Celery('ecommarce')


# Load Celery settings from Django settings.py
app.config_from_object(
    'django.conf:settings',
    namespace='CELERY'
)


# Automatically discover tasks.py from installed Django apps
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

