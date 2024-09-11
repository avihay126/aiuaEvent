import threading

from django.apps import AppConfig

from thread_manager import submit_task


class FaceClassificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'face_classification'
    bot_started = False

    # def ready(self):
    #     if not self.bot_started:
    #         self.bot_started = True
    #         from .classify import get_unclassified_photos
    #         submit_task(get_unclassified_photos)
