from django.apps import AppConfig
import threading


class BotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'bot'
    bot_started = False

    def ready(self):
        if not self.bot_started:
            self.bot_started = True
            from .whatsapp_bot import check_messages

            bot_thread = threading.Thread(target=check_messages)
            bot_thread.daemon = True
            bot_thread.start()
