from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # זה יהיה דף הבית שלך
    path('about/', views.about, name='about'),
    path('get-events/', views.get_events, name='get-events'),
    path('add-photos/', views.add_photos, name='add_photos')
]
