import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "library_service.settings")
app = Celery("library_service")

app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print("Request: {0!r}".format(self.request))
