"""URLs of the app's system-browser sign-in (F4), mounted at ``app/auth/``."""

from django.urls import path

from core import views_appauth

urlpatterns = [
    path("start/<str:provider>/", views_appauth.app_auth_start, name="app_auth_start"),
    path("complete/", views_appauth.app_auth_complete, name="app_auth_complete"),
    # The callback the OS matches in mobile/ WebAuth: keep the path in step.
    path("return/", views_appauth.app_auth_return, name="app_auth_return"),
    path("redeem/", views_appauth.app_auth_redeem, name="app_auth_redeem"),
]
