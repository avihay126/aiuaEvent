from django.apps import AppConfig
import threading
from task_queue import add_task


class BotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bot'
    bot_started = False

    def ready(self):
        if not self.bot_started:
            self.bot_started = True
            from .whatsapp_bot import check_messages

            # # הפעלת הבוט בתהליך נפרד כדי לא לחסום את שרת Django
            # bot_thread = threading.Thread(target=check_messages)
            # bot_thread.daemon = True  # התהליך ייסגר עם סגירת השרת
            # bot_thread.start()
            add_task(check_messages)