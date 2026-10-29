"""URLs of the app's sign-in, mounted at ``app/auth/``: system browser (F4), native (O3)."""

from django.urls import path

from core import views_appauth, views_appnative

urlpatterns = [
    path("start/<str:provider>/", views_appauth.app_auth_start, name="app_auth_start"),
    path("complete/", views_appauth.app_auth_complete, name="app_auth_complete"),
    # The callback the OS matches in mobile/ WebAuth: keep the path in step.
    path("return/", views_appauth.app_auth_return, name="app_auth_return"),
    path("redeem/", views_appauth.app_auth_redeem, name="app_auth_redeem"),
    # mobile/ signIn.ts posts to both: keep the paths in step.
    path("native/nonce/", views_appnative.app_native_nonce, name="app_native_nonce"),
    path("native/", views_appnative.app_native_signin, name="app_native_signin"),
]
