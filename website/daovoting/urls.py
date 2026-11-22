"""Module containing the daovoting app's URL configuration."""

from django.urls import path

from daovoting import views

urlpatterns = [
    path("", views.dao_index, name="dao_index"),
    path("governors/", views.dao_governors, name="dao_governors"),
    path("session/<int:session_id>/", views.dao_session, name="dao_session"),
    path(
        "session/<int:session_id>/<str:name>",
        views.dao_document,
        name="dao_document",
    ),
]
