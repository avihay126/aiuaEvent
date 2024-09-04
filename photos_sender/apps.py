import threading

from django.apps import AppConfig
from task_queue import add_task


class PhotosSenderConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'photos_sender'
    bot_started = False

    def ready(self):
        if not self.bot_started:
            self.bot_started = True
            from .sender_bot import send_images_to_all

            # # הפעלת הבוט בתהליך נפרד כדי לא לחסום את שרת Django
            # bot_thread = threading.Thread(target=send_images_to_all)
            # bot_thread.daemon = True  # התהליך ייסגר עם סגירת השרת
            # bot_thread.start()
            add_task(send_images_to_all)
