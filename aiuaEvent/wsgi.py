"""
WSGI config for aiuaEvent project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/wsgi/
"""

import os
from django.core.wsgi import get_wsgi_application
import django
from django.core.management import call_command

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aiuaEvent.settings')

application = get_wsgi_application()

# Execute migrations automatically when the server starts
django.setup()
call_command('migrate')



