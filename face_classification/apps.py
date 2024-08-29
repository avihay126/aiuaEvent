import threading

from django.apps import AppConfig


class FaceClassificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'face_classification'
    bot_started = False


    def ready(self):
            if not self.bot_started:
                self.bot_started = True
                from .classify import get_unclassified_photos

                # הפעלת הבוט בתהליך נפרד כדי לא לחסום את שרת Django
                bot_thread = threading.Thread(target=get_unclassified_photos)
                bot_thread.daemon = True  # התהליך ייסגר עם סגירת השרת
                bot_thread.start()