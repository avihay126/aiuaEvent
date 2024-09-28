import threading

from django.apps import AppConfig

from thread_manager import submit_task


class PhotosSenderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'photos_sender'
    bot_started = False

    def ready(self):
        if not self.bot_started:
            self.bot_started = True
            from .sender_bot import open_whatsapp
            submit_task(open_whatsapp)
