"""Module containing the assetfeedback app's URL configuration."""

from django.urls import path

from assetfeedback.views import AssetFeedbackView

urlpatterns = [
    path("<int:asset_id>/", AssetFeedbackView.as_view(), name="asset_feedback"),
]
