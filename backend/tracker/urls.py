from django.urls import path

from . import views

urlpatterns = [
    path("promises/", views.promise_list, name="promise-list"),
    path("promises/<int:promise_id>/override/", views.set_override, name="promise-override"),
]
