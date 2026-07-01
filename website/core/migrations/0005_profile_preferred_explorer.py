"""Add Profile.preferred_explorer (preferred blockchain explorer key)."""

from django.db import migrations, models


class Migration(migrations.Migration):
    """Add the preferred_explorer preference field to Profile."""

    dependencies = [
        ("core", "0004_profile_preferred_router"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="preferred_explorer",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
    ]
