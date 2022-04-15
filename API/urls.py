from django.urls import path
from . import views
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('', views.Home, name="Home"),
    path('API', views.Request, name="Request"),
]
urlpatterns += staticfiles_urlpatterns()
