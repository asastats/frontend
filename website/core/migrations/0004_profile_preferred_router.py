"""Add Profile.preferred_router (preferred smart router id)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Add the preferred_router preference field to Profile."""

    dependencies = [
        ("core", "0003_profile_auth_method_etc"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="preferred_router",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
    ]
