from django.urls import path
from . import event_views, authentication_views

urlpatterns = [
    path('get-events/', event_views.get_events, name='get-events'),
    path('add-photos/', event_views.add_photos, name='add_photos'),
    path('create-event/', event_views.create_event, name='create_event'),
    path('register/', authentication_views.register_photographer),
    path('login/', authentication_views.login_photographer),
    path('logout/', authentication_views.logout_photographer),
]
