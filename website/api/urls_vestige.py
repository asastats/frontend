"""Module containing URL configuration of the Vestige-compatible endpoints."""

from django.urls import re_path

from api import vestige

urlpatterns = [
    re_path(pattern, getattr(vestige, view).as_view(), name=name)
    for pattern, view, name in vestige.VESTIGE_PATHS
]
